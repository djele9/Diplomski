"""
llm.py — call the model, parse the answer, write the files, record the run.

The parsing here is deliberately stricter than a single regex. The original
pattern

    r"FILE:\\s*([^\\r\\n]+)\\r?\\n\\s*```[^\\r\\n]*\\r?\\n(.*?)\\r?\\n```"

fails in three ways that all lose data silently:

  * a truncated response never emits its final closing fence, so the last file
    simply does not match and disappears without an error;
  * a file whose content contains a fenced block (a README, a template literal
    holding markdown) terminates early at the inner fence;
  * a response with no FILE: markers at all raises, but a response with ONE
    valid file out of twelve looks like a success.

This module detects all three.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

import ollama

import config


# ------------------------------------------------------------- records -----
@dataclass
class StageRecord: #One stage of generation
    stage: str
    model: str
    started_at: str
    wall_seconds: float = 0.0
    prompt_chars: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tokens_per_second: float = 0.0
    done_reason: str = ""
    truncated: bool = False
    files_written: list[str] = field(default_factory=list)
    placeholder_hits: list[str] = field(default_factory=list)
    repair_round: int = 0


# ------------------------------------------------------------- parsing -----
_FILE_MARKER = re.compile(r"^\s*FILE:\s*(.+?)\s*$")
_FENCE = re.compile(r"^\s*```")


def parse_files(response_text: str) -> list[tuple[str, str]]:
    """
    Extract (path, content) pairs.

    Fence handling: within one FILE: block the content runs from the line after
    the FIRST fence to the LAST fence in that block. Taking the last fence
    rather than the first closing one lets a generated file legitimately
    contain ``` inside it.
    """
    lines = response_text.splitlines()

    # Where each FILE: marker sits.
    markers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = _FILE_MARKER.match(line)
        if m and not line.lstrip().startswith(("*", "-", "#", "//")):
            markers.append((i, m.group(1).strip()))

    results: list[tuple[str, str]] = []
    for idx, (start, raw_path) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        block = lines[start + 1:end]

        fences = [i for i, l in enumerate(block) if _FENCE.match(l)]
        if len(fences) < 2:
            # An unterminated block is the signature of a truncated response.
            # Reported by the caller through `truncated`; skipped here.
            continue
        content = "\n".join(block[fences[0] + 1:fences[-1]])
        results.append((raw_path, content))

    return results


def find_unterminated(response_text: str) -> list[str]:
    """Paths whose fenced block never closed — almost always truncation."""
    lines = response_text.splitlines()
    markers = [(i, m.group(1).strip())
               for i, line in enumerate(lines)
               if (m := _FILE_MARKER.match(line))]
    bad = []
    for idx, (start, path) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        block = lines[start + 1:end]
        if len([i for i, l in enumerate(block) if _FENCE.match(l)]) < 2:
            bad.append(path)
    return bad


def scan_placeholders(path: str, content: str) -> list[str]:
    """Report stub markers the prompt forbade. The original never checked."""
    hits = []
    upper = content.upper()
    for marker in config.PLACEHOLDER_MARKERS:
        if marker.upper() in upper:
            hits.append(f"{path}: {marker}")
    return hits


# ------------------------------------------------------------- writing -----
def safe_destination(raw_path: str) -> Path:
    """
    Resolve a model-supplied path under OUTPUT_DIR, refusing escapes.

    The rejection checks run on the RAW path, before any normalisation.
    `"/etc/passwd".lstrip("./")` is `"etc/passwd"` and
    `"../../x".lstrip("./")` is `"x"` — so stripping first would turn both an
    absolute path and a traversal into innocent-looking relative paths and
    write them without complaint. Reject first, normalise second.
    """
    candidate = raw_path.strip().replace("\\", "/")

    if candidate.startswith("/") or re.match(r"^[A-Za-z]:", candidate):
        raise RuntimeError(f"Refusing absolute path from model: {raw_path}")
    if ".." in Path(candidate).parts:
        raise RuntimeError(f"Refusing path escape from model: {raw_path}")

    # Only now strip a leading "./", and only that exact prefix.
    while candidate.startswith("./"):
        candidate = candidate[2:]
    path = Path(candidate)

    if not candidate:
        raise RuntimeError(f"Refusing empty path from model: {raw_path!r}") #repr(raw_path)
    if path.name in config.FORBIDDEN_OUTPUT_FILES:
        raise RuntimeError(
            f"Refusing to write {path.name}: a generated lockfile contains "
            f"invented integrity hashes and breaks `npm ci`. Run `npm install`."
        )

    # Models sometimes prefix the output root they were shown. Strip it so
    # "app/backend/src/x.ts" and "backend/src/x.ts" land in the same place.
    parts = path.parts
    if parts and parts[0] == config.OUTPUT_DIR.name:
        path = Path(*parts[1:])

    destination = config.OUTPUT_DIR / path
    destination.resolve().relative_to(config.OUTPUT_DIR.resolve())  # raises if outside
    return destination


def write_files(pairs: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    written: list[str] = []
    placeholders: list[str] = []
    for raw_path, content in pairs:
        destination = safe_destination(raw_path)
        placeholders.extend(scan_placeholders(raw_path, content))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(destination.relative_to(config.OUTPUT_DIR).as_posix())
    return written, placeholders


# ---------------------------------------------------------------- call -----
def call(
    stage: str,
    prompt: str,
    *, #after this all arguments must be passed as name parameters
    expect_files: int | None = None,
    repair_round: int = 0,
    strict: bool = True,
) -> StageRecord:
    """
    Run one generation stage.

    `expect_files` — when given, the stage fails if the model returned fewer
    files than that. It is the difference between "the backend generated" and
    "the backend generated, and all seven files I asked for are on disk".
    """
    run_dir = config.RUNS_DIR / _RUN_ID
    stage_dir = run_dir / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    suffix = f".repair{repair_round}" if repair_round else ""
    (stage_dir / f"prompt{suffix}.md").write_text(prompt, encoding="utf-8")

    record = StageRecord(
        stage=stage,
        model=config.MODEL,
        started_at=datetime.now(timezone.utc).isoformat(),
        prompt_chars=len(prompt),
        repair_round=repair_round,
    )

    print(f"  → {stage}{suffix}: prompt {len(prompt):,} chars ...", end="", flush=True)
    t0 = time.perf_counter()
    response = ollama.chat(
        model=config.MODEL,
        messages=[{"role": "user", "content": prompt}],
        options=config.OPTIONS,
        stream=False,
        keep_alive="10m", #to keep model in memory
    )
    record.wall_seconds = round(time.perf_counter() - t0, 1)

    text = response.message.content or ""
    (stage_dir / f"response{suffix}.md").write_text(text, encoding="utf-8")

    raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    record.prompt_tokens = raw.get("prompt_eval_count", 0) or 0
    record.completion_tokens = raw.get("eval_count", 0) or 0
    eval_ns = raw.get("eval_duration", 0) or 0
    record.tokens_per_second = round(
        record.completion_tokens / (eval_ns / 1e9), 1) if eval_ns else 0.0
    record.done_reason = str(raw.get("done_reason", "") or "")

    unterminated = find_unterminated(text)
    record.truncated = record.done_reason == "length" or bool(unterminated)

    print(f" {record.wall_seconds}s, "
          f"in {record.prompt_tokens:,} tok, out {record.completion_tokens:,} tok")

    # --- context-window check ------------------------------------------
    # If the model ingested far fewer tokens than we sent, num_ctx silently
    # truncated the prompt and the model never saw the specification.
    if record.prompt_tokens:
        estimated = record.prompt_chars / 3.7
        if record.prompt_tokens < estimated * 0.6:
            raise RuntimeError(
                f"[{stage}] The model ingested only {record.prompt_tokens:,} tokens "
                f"of an estimated {estimated:,.0f}. The prompt was truncated by the "
                f"context window. Raise num_ctx in config.OPTIONS (currently "
                f"{config.OPTIONS['num_ctx']:,}) or reduce what this stage sends."
            )

    if record.truncated and strict:
        raise RuntimeError(
            f"[{stage}] Response was truncated "
            f"(done_reason={record.done_reason!r}, "
            f"{len(unterminated)} file(s) left unclosed: {unterminated[:5]}).\n"
            f"Raise num_predict (currently {config.OPTIONS['num_predict']:,}) or "
            f"split this stage into smaller ones."
        )

    pairs = parse_files(text)
    if not pairs:
        head = text[:400].replace("\n", " ")
        raise RuntimeError(
            f"[{stage}] No files found in the response. "
            f"The model probably ignored the output contract.\n"
            f"Response begins: {head!r}\n"
            f"Full response saved to {stage_dir / f'response{suffix}.md'}"
        )

    record.files_written, record.placeholder_hits = write_files(pairs)

    if expect_files is not None and len(record.files_written) < expect_files:
        raise RuntimeError(
            f"[{stage}] Expected at least {expect_files} files, got "
            f"{len(record.files_written)}: {record.files_written}"
        )

    for path in record.files_written:
        print(f"      {path}")
    if record.placeholder_hits:
        print(f"      !! {len(record.placeholder_hits)} placeholder marker(s):")
        for hit in record.placeholder_hits[:10]:
            print(f"         {hit}")

    _RECORDS.append(record)
    _flush_records()
    return record


# ------------------------------------------------------------- run log -----
_RUN_ID = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
_RECORDS: list[StageRecord] = []


def run_id() -> str:
    return _RUN_ID


def _flush_records() -> None:
    run_dir = config.RUNS_DIR / _RUN_ID
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "stages.json").write_text(
        json.dumps([asdict(r) for r in _RECORDS], indent=2), encoding="utf-8")


def summary() -> str:
    if not _RECORDS:
        return "no stages ran"
    total_s = sum(r.wall_seconds for r in _RECORDS)
    total_out = sum(r.completion_tokens for r in _RECORDS)
    files = sum(len(r.files_written) for r in _RECORDS)
    stubs = sum(len(r.placeholder_hits) for r in _RECORDS)
    return (
        f"{len(_RECORDS)} stages, {files} files, "
        f"{total_out:,} tokens generated, {total_s/60:.1f} min"
        + (f", {stubs} placeholder markers" if stubs else "")
    )
