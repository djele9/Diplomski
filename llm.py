"""
llm.py — call the model, parse the answer, write the files, record the run.

Two principles run through this module.

**Parsing must not corrupt.** The naive single regex

    r"FILE:\\s*([^\\r\\n]+)\\r?\\n\\s*```[^\\r\\n]*\\r?\\n(.*?)\\r?\\n```"

loses data silently in three ways: a truncated response never emits its final
closing fence, so the last file disappears without an error; a file whose
content contains a fenced block terminates early; and a response with one valid
file out of twelve looks like a success. All three are detected here.

**A failed stage is data, not an exception.** This pipeline exists to compare
models, and the interesting models are the small ones that sometimes truncate,
chatter, or ignore the output contract. If the first such stage aborts the run,
the weakest models produce no measurements at all and the comparison is
restricted to the models that did not need measuring. So `call` records the
failure on the StageRecord and returns; the pipeline decides what to do next and
the run record keeps the evidence either way.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

import config

# `ollama` is imported inside call() rather than here. Everything in this module
# except the model call itself — the parser, the path guard, the stub scanner —
# is pure and testable, and test_pipeline.py exercises all of it. Importing the
# client at module scope would make that suite require a running Ollama install
# to test code that never talks to one.


# ------------------------------------------------------------- records -----
@dataclass
class StageRecord:
    """One stage of generation. Serialised verbatim into runs/<id>/stages.json."""

    stage: str
    model: str
    started_at: str
    wall_seconds: float = 0.0
    prompt_chars: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tokens_per_second: float = 0.0
    tokens_per_second_source: str = ""     # "eval_duration" or "wall_clock"
    done_reason: str = ""
    truncated: bool = False
    context_overflow: bool = False
    files_written: list[str] = field(default_factory=list)
    files_expected: int = 0
    paths_repaired: list[str] = field(default_factory=list)
    paths_rejected: list[str] = field(default_factory=list)
    unterminated_files: list[str] = field(default_factory=list)
    chatter_files: list[str] = field(default_factory=list)
    placeholder_hits: list[str] = field(default_factory=list)
    repair_round: int = 0
    ok: bool = True
    failure: str = ""

    def label(self) -> str:
        return f"{self.stage}{f'.repair{self.repair_round}' if self.repair_round else ''}"


class ModelUnavailable(RuntimeError):
    """The model could not be reached or run at all. Not a generation failure."""


# ------------------------------------------------------------- parsing -----
_FILE_MARKER = re.compile(r"^\s*FILE:\s*(.+?)\s*$")
_FENCE = re.compile(r"^\s*```(?P<lang>[A-Za-z0-9_+-]*)")


@dataclass
class ParsedFile:
    path: str
    content: str
    closed: bool = True
    trailing_chatter: bool = False


def _is_markdown(raw_path: str, language: str) -> bool:
    if language.lower() in config.MARKDOWN_FENCE_LANGUAGES:
        return True
    return raw_path.lower().endswith(config.MARKDOWN_SUFFIXES)


def parse_files(response_text: str) -> list[ParsedFile]:
    """
    Extract one ParsedFile per `FILE:` marker.

    Fence handling is the subtle part, and the previous rule — content runs from
    the first fence to the LAST fence in the block — was wrong in a way that
    biases a model comparison.

    It was chosen so that a generated README could contain ``` inside it. But it
    also means that when a model writes the file, closes the fence, and then adds
    a second fenced block (a usage example, a shell command, "here's how to run
    it"), everything between the two blocks — the closing fence, the prose, the
    opening fence of the example — is written INTO the source file. The file then
    fails to compile, and the failure is recorded against the model's code
    quality when it was really the parser's.

    That bias is not random. Terse models close cleanly; chatty small models add
    the example. So the rule systematically penalised exactly the models this
    thesis is about.

    The rule here: close at the FIRST closing fence, except for markdown files,
    where nested fences are expected and the last fence wins. Anything after the
    closing fence is recorded as `trailing_chatter` — a per-model metric worth
    reporting rather than a silent correction.
    """
    lines = response_text.splitlines()

    markers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        match = _FILE_MARKER.match(line)
        if match:
            markers.append((i, match.group(1).strip()))

    results: list[ParsedFile] = []
    for index, (start, raw_path) in enumerate(markers):
        end = markers[index + 1][0] if index + 1 < len(markers) else len(lines)
        block = lines[start + 1:end]

        fences = [(i, m.group("lang") or "")
                  for i, l in enumerate(block) if (m := _FENCE.match(l))]
        if not fences:
            results.append(ParsedFile(raw_path, "", closed=False))
            continue
        if len(fences) < 2:
            # An unterminated block is the signature of a truncated response.
            # Keep what there is — a partially written file is more useful for
            # diagnosis than nothing — but mark it unclosed so it is never
            # counted as a delivered file.
            opened = fences[0][0]
            results.append(ParsedFile(raw_path, "\n".join(block[opened + 1:]),
                                      closed=False))
            continue

        opened, language = fences[0]
        closed_at = fences[-1][0] if _is_markdown(raw_path, language) else fences[1][0]
        content = "\n".join(block[opened + 1:closed_at])
        chatter = any(line.strip() for line in block[closed_at + 1:])
        results.append(ParsedFile(raw_path, content, closed=True,
                                  trailing_chatter=chatter))

    return results


# --------------------------------------------------------- stub scanning ---
def scan_placeholders(path: str, content: str) -> list[str]:
    """
    Report stub markers the prompt forbade, without crying wolf.

    A flat substring scan is not good enough. A registration form whose help
    text reads "a default image will be used if omitted" is complete and
    correct, but a search for "OMITTED" flags it — and once a check produces
    false positives people stop reading it, which is worse than not having it.

    So: STRONG markers ("OMITTED FOR BREVITY", "REST OF CODE") are flagged
    anywhere. WEAK markers (bare "TODO", "omitted", "unchanged") are flagged
    only inside a comment, where they cannot be ordinary prose or a UI string.

    Each hit reports the line number and the line, so it can be judged rather
    than guessed at.
    """
    hits: list[str] = []
    flagged_lines: set[int] = set()          # one report per line, not three
    lines = content.splitlines()

    # --- strong markers: anywhere -------------------------------------
    for number, line in enumerate(lines, start=1):
        upper = line.upper()
        for marker in config.PLACEHOLDER_MARKERS_STRONG:
            if marker.upper() in upper:
                hits.append(f"{path}:{number}: [strong] {marker} — {line.strip()[:100]}")
                flagged_lines.add(number)
                break

    # --- weak markers: only inside comments ---------------------------
    suffix = Path(path).suffix.lower()
    comment_patterns = config.COMMENT_PATTERNS.get(suffix)
    if comment_patterns is None:
        comment_patterns = (r"//.*$", r"/\*.*?\*/")      # sensible default

    if comment_patterns:
        combined = re.compile("|".join(comment_patterns), re.S | re.M)
        for match in combined.finditer(content):
            comment = match.group(0)
            upper = comment.upper()
            for marker in config.PLACEHOLDER_MARKERS_WEAK:
                if marker in upper:
                    number = content[: match.start()].count("\n") + 1
                    if number in flagged_lines:
                        break                # already reported by a strong marker
                    snippet = " ".join(comment.split())[:100]
                    hits.append(f"{path}:{number}: [weak] {marker} in comment — {snippet}")
                    flagged_lines.add(number)
                    break

    # --- an empty body is an elision the markers would miss -----------
    if suffix in (".ts", ".tsx", ".js", ".mjs", ".cjs"):
        for number, line in enumerate(lines, start=1):
            if number in flagged_lines:
                continue
            if re.search(r"\)\s*(:\s*[\w<>\[\]|, ]+\s*)?\{\s*\}\s*$", line) and \
               not re.search(r"\b(constructor|interface|type|enum|ngOnInit|ngOnDestroy)\b", line):
                hits.append(f"{path}:{number}: [weak] empty function body — {line.strip()[:100]}")
                flagged_lines.add(number)

    return hits


# ------------------------------------------------------------- writing -----
class PathRejected(ValueError):
    """A model-supplied path that must not be written."""


# Files that legitimately sit at a project root, used to decide whether a path
# missing its `backend/` or `frontend/` prefix can be repaired unambiguously.
_ROOT_LEVEL_FILES = {
    "package.json", "tsconfig.json", "tsconfig.app.json", "tsconfig.spec.json",
    "tsconfig.build.json", "angular.json", ".env", ".env.example", ".gitignore",
    "nodemon.json", ".eslintrc.json", "eslint.config.js", "README.md",
}


def safe_destination(raw_path: str, expected_root: str | None = None,
                     base: Path | None = None,
                     allowed_suffixes: tuple[str, ...] | None = None) -> tuple[Path, str]:
    """
    Resolve a model-supplied path under `base` (OUTPUT_DIR unless given).

    `base` is what lets the specification stage share this guard: it writes into
    the features directory rather than app/, but needs exactly the same
    protection against absolute paths, traversal and stray file types.

    Returns (destination, note). `note` is empty when the path arrived correct,
    and describes the repair when one was applied.

    The rejection checks run on the RAW path, before any normalisation.
    `"/etc/passwd".lstrip("./")` is `"etc/passwd"` and `"../../x".lstrip("./")`
    is `"x"` — so stripping first would turn both an absolute path and a
    traversal into innocent-looking relative paths and write them without
    complaint. Reject first, normalise second.

    The root check is new, and it matters more than it looks. Every prompt
    demands paths begin with `backend/` or `frontend/`, and nothing used to
    enforce it. A model that returns `src/models/user.model.ts` had the file
    written to app/src/models/user.model.ts — outside both projects, compiled by
    neither, while the stage still counted it toward `expect_files` and passed.
    The build then fails somewhere unrelated.
    """
    base = base or config.OUTPUT_DIR
    candidate = raw_path.strip().replace("\\", "/")

    if candidate.startswith("/") or re.match(r"^[A-Za-z]:", candidate):
        raise PathRejected(f"absolute path: {raw_path}")
    if ".." in Path(candidate).parts:
        raise PathRejected(f"path escape: {raw_path}")

    # Only now strip a leading "./", and only that exact prefix.
    while candidate.startswith("./"):
        candidate = candidate[2:]
    if not candidate:
        raise PathRejected(f"empty path: {raw_path!r}")

    path = Path(candidate)
    if path.name in config.FORBIDDEN_OUTPUT_FILES:
        raise PathRejected(
            f"{path.name}: a generated lockfile contains invented integrity "
            f"hashes and breaks `npm ci`. Run `npm install` instead."
        )
    if allowed_suffixes and path.suffix.lower() not in allowed_suffixes:
        raise PathRejected(
            f"{raw_path}: this stage writes only {', '.join(allowed_suffixes)} files"
        )

    note = ""
    parts = path.parts

    # Models sometimes prefix the directory they were shown. Strip it — but when
    # that directory is the app root, only when what follows is a project root,
    # so that a frontend path like "app/components/login/login.ts" is not
    # silently decapitated.
    if len(parts) > 1 and parts[0] == base.name and \
            (expected_root is None or f"{parts[1]}/" in config.EXPECTED_ROOTS):
        path = Path(*parts[1:])
        parts = path.parts
        note = f"stripped '{base.name}/' prefix"

    if expected_root:
        root = expected_root.rstrip("/")
        if parts and parts[0] == root:
            pass                                    # correct as sent
        elif parts and f"{parts[0]}/" in config.EXPECTED_ROOTS:
            raise PathRejected(
                f"{raw_path}: this stage writes under '{expected_root}', but the "
                f"path targets '{parts[0]}/'"
            )
        elif parts and (parts[0] in config.PROJECT_SUBDIRS
                        or (len(parts) == 1 and path.name in _ROOT_LEVEL_FILES)):
            # Unambiguous: "src/..." or a known root-level file, missing only
            # its project prefix. Repair it and say so.
            path = Path(root) / path
            note = (note + "; " if note else "") + f"prepended '{expected_root}'"
        else:
            raise PathRejected(
                f"{raw_path}: does not start with '{expected_root}' and cannot be "
                f"repaired unambiguously"
            )

    destination = base / path
    try:
        destination.resolve().relative_to(base.resolve())
    except ValueError as exc:
        raise PathRejected(f"{raw_path}: resolves outside the output directory") from exc
    return destination, note


def write_files(parsed: list[ParsedFile], expected_root: str | None,
                base: Path | None = None,
                allowed_suffixes: tuple[str, ...] | None = None
                ) -> tuple[list[str], list[str], list[str], list[str]]:
    """
    Write every closed file. Returns (written, repaired, rejected, placeholders).

    An unclosed file is never written. It is truncated by definition, so writing
    it would put a half-finished source file on disk where the next stage reads
    it as though it were complete — which produces a second broken stage and
    makes the first one hard to identify.
    """
    base = base or config.OUTPUT_DIR
    written: list[str] = []
    repaired: list[str] = []
    rejected: list[str] = []
    placeholders: list[str] = []

    for item in parsed:
        if not item.closed:
            continue
        try:
            destination, note = safe_destination(item.path, expected_root,
                                                 base, allowed_suffixes)
        except PathRejected as exc:
            rejected.append(str(exc))
            continue
        if note:
            repaired.append(f"{item.path} -> {note}")
        placeholders.extend(scan_placeholders(item.path, item.content))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(item.content.rstrip() + "\n", encoding="utf-8")
        written.append(destination.relative_to(base).as_posix())

    return written, repaired, rejected, placeholders


# ---------------------------------------------------------------- call -----
def call(
    stage: str,
    prompt: str,
    *,
    expect_files: int | None = None,
    expected_root: str | None = None,
    output_base: Path | None = None,
    allowed_suffixes: tuple[str, ...] | None = None,
    model: str | None = None,
    repair_round: int = 0,
) -> StageRecord:
    """
    Run one generation stage.

    Never raises for a generation problem — truncation, an ignored output
    contract, too few files, rejected paths. Those set `record.ok = False` and
    `record.failure`, and the caller decides. A failure to reach the model at
    all raises ModelUnavailable, because that is a broken run rather than a
    measurement.

    `expect_files` — when given, the stage is marked failed if the model returned
    fewer files than that. It is the difference between "the backend generated"
    and "the backend generated, and all seven files I asked for are on disk".
    """
    run_dir = config.RUNS_DIR / _RUN_ID
    stage_dir = run_dir / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    suffix = f".repair{repair_round}" if repair_round else ""
    (stage_dir / f"prompt{suffix}.md").write_text(prompt, encoding="utf-8")

    # `model` lets one run use a different model for one stage — specifically,
    # generating the specification with one model and the code with another, so
    # that code quality is not confounded by specification quality.
    active_model = model or config.MODEL

    record = StageRecord(
        stage=stage,
        model=active_model,
        started_at=datetime.now(timezone.utc).isoformat(),
        prompt_chars=len(prompt),
        files_expected=expect_files or 0,
        repair_round=repair_round,
    )

    import ollama

    print(f"  → {stage}{suffix}: prompt {len(prompt):,} chars ...", end="", flush=True)
    t0 = time.perf_counter()
    try:
        response = ollama.chat(
            model=active_model,
            messages=[{"role": "user", "content": prompt}],
            options=config.OPTIONS,
            stream=False,
            keep_alive="10m",
        )
    except Exception as exc:                      # connection, model not pulled, OOM
        record.wall_seconds = round(time.perf_counter() - t0, 1)
        record.ok = False
        record.failure = f"model call failed: {type(exc).__name__}: {exc}"
        print(f" FAILED after {record.wall_seconds}s")
        _RECORDS.append(record)
        _flush_records()
        raise ModelUnavailable(record.failure) from exc

    record.wall_seconds = round(time.perf_counter() - t0, 1)

    text = response.message.content or ""
    (stage_dir / f"response{suffix}.md").write_text(text, encoding="utf-8")

    raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    record.prompt_tokens = raw.get("prompt_eval_count", 0) or 0
    record.completion_tokens = raw.get("eval_count", 0) or 0
    record.done_reason = str(raw.get("done_reason", "") or "")

    # Throughput. `eval_duration` is absent from some backends — every stage of
    # the committed run recorded 0.0 tokens/s because of it — and throughput is
    # a headline metric when the question is which small model is practical to
    # run. Fall back to wall-clock, and record which measure was used so the two
    # are never silently mixed in a table. Wall-clock includes model load time,
    # so it reads lower; that is a real cost, but it is a different number.
    eval_ns = raw.get("eval_duration", 0) or 0
    if eval_ns:
        record.tokens_per_second = round(record.completion_tokens / (eval_ns / 1e9), 1)
        record.tokens_per_second_source = "eval_duration"
    elif record.wall_seconds > 0 and record.completion_tokens:
        record.tokens_per_second = round(record.completion_tokens / record.wall_seconds, 1)
        record.tokens_per_second_source = "wall_clock"

    parsed = parse_files(text)
    record.unterminated_files = [p.path for p in parsed if not p.closed]
    record.chatter_files = [p.path for p in parsed if p.trailing_chatter]
    record.truncated = record.done_reason == "length" or bool(record.unterminated_files)

    print(f" {record.wall_seconds}s, "
          f"in {record.prompt_tokens:,} tok, out {record.completion_tokens:,} tok"
          f"{' [TRUNCATED]' if record.truncated else ''}")

    # --- context-window check ------------------------------------------
    # If the model ingested far fewer tokens than we sent, num_ctx silently
    # truncated the prompt and the model never saw the specification. Everything
    # downstream of that is measuring the wrong thing.
    if record.prompt_tokens:
        estimated = record.prompt_chars / config.CHARS_PER_TOKEN
        if record.prompt_tokens < estimated * 0.6:
            record.context_overflow = True
            record.ok = False
            record.failure = (
                f"prompt truncated by the context window: the model ingested "
                f"{record.prompt_tokens:,} tokens of an estimated {estimated:,.0f}. "
                f"Raise num_ctx (currently {config.OPTIONS['num_ctx']:,}) or reduce "
                f"what this stage sends."
            )

    written, repaired, rejected, placeholders = write_files(
        parsed, expected_root, output_base, allowed_suffixes)
    record.files_written = written
    record.paths_repaired = repaired
    record.paths_rejected = rejected
    record.placeholder_hits = placeholders

    # --- verdict ---------------------------------------------------------
    problems: list[str] = []
    if record.context_overflow:
        problems.append(record.failure)
    if not parsed:
        head = text[:300].replace("\n", " ")
        problems.append(f"no FILE: markers in the response; it begins {head!r}")
    if record.truncated:
        problems.append(
            f"response truncated (done_reason={record.done_reason!r}, "
            f"{len(record.unterminated_files)} file(s) unclosed: "
            f"{record.unterminated_files[:5]}) — raise num_predict (currently "
            f"{config.OPTIONS['num_predict']:,}) or split this stage"
        )
    if rejected:
        problems.append(f"{len(rejected)} path(s) rejected: {rejected[:3]}")
    if expect_files is not None and len(written) < expect_files:
        problems.append(f"expected at least {expect_files} files, wrote {len(written)}")

    if problems:
        record.ok = False
        record.failure = "; ".join(problems)

    for path in written:
        print(f"      {path}")
    for note in repaired:
        print(f"      ~ path repaired: {note}")
    for note in rejected:
        print(f"      ! path REJECTED: {note}")
    if record.chatter_files:
        print(f"      ~ {len(record.chatter_files)} file(s) had prose after the "
              f"closing fence (recorded, not written)")
    if placeholders:
        print(f"      !! {len(placeholders)} placeholder marker(s):")
        for hit in placeholders[:10]:
            print(f"         {hit}")
    if not record.ok:
        print(f"      ** STAGE FAILED: {record.failure}")

    _RECORDS.append(record)
    _flush_records()
    return record


# ------------------------------------------------------------- run log -----
_RUN_ID = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
_RECORDS: list[StageRecord] = []


def run_id() -> str:
    return _RUN_ID


def set_run_id(value: str) -> None:
    """Used when several models are driven from one outer script."""
    global _RUN_ID
    _RUN_ID = value


def records() -> list[StageRecord]:
    return list(_RECORDS)


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
    failed = [r.label() for r in _RECORDS if not r.ok]
    parts = [
        f"{len(_RECORDS)} stages ({len(failed)} failed)",
        f"{files} files",
        f"{total_out:,} tokens generated",
        f"{total_s/60:.1f} min",
    ]
    if stubs:
        parts.append(f"{stubs} placeholder markers")
    line = ", ".join(parts)
    if failed:
        line += f"\n  failed stages: {', '.join(failed)}"
    return line
