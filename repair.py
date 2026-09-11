"""
repair.py — compile the generated code and feed the errors back.

This is the highest-value part of the pipeline and the one the original had no
equivalent of. Generation produces code that is *plausible*; compilation is the
only thing that establishes whether it is *correct enough to run*. Two or three
rounds of "here are your errors, return the corrected files" typically takes a
project that does not build to one that does.

It also produces the honest number for the write-up: "compiled after N repair
rounds" is a far better measure of a model than "produced N files".
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import config
import llm


@dataclass
class CompileResult:
    ok: bool
    error_count: int
    errors_by_file: dict[str, list[str]]
    raw: str

    def summary(self) -> str:
        if self.ok:
            return "compiles cleanly"
        return (f"{self.error_count} error(s) across "
                f"{len(self.errors_by_file)} file(s)")


# tsc:  src/x.ts(12,5): error TS2304: Cannot find name 'foo'.
_TSC_ERROR = re.compile(
    r"^(?P<file>[^\s(][^(]*)\((?P<line>\d+),(?P<col>\d+)\):\s*"
    r"(?P<severity>error|warning)\s+(?P<code>TS\d+):\s*(?P<message>.*)$"
)
# ng build: X [ERROR] TS2304: Cannot find name 'foo' [plugin angular-compiler]
#             src/app/x.ts:12:5:
_NG_ERROR = re.compile(r"\[ERROR\]\s*(?P<message>.*?)(?:\s*\[plugin.*?\])?$")
_NG_LOCATION = re.compile(r"^\s*(?P<file>[\w./\-]+\.\w+):(?P<line>\d+):(?P<col>\d+)")


def _run(command: list[str], cwd: Path, timeout: int = 900) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return 127, f"command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s: {' '.join(command)}"


def install(project: Path) -> bool:
    """
    `npm install`, not `npm ci`.

    The prompts forbid generating a lockfile precisely because a model-written
    one contains invented integrity hashes, and `npm ci` fails on it. Installing
    from package.json alone lets npm resolve and write a real lockfile.
    """
    if not (project / "package.json").exists():
        print(f"  no package.json in {project}, skipping install")
        return False
    stale = project / "package-lock.json"
    if stale.exists():
        stale.unlink()
        print("  removed a generated package-lock.json (integrity hashes are invented)")
    print(f"  npm install in {project.name} ...", end="", flush=True)
    code, output = _run(["npm", "install", "--no-audit", "--no-fund"], project, timeout=1200)
    print(" ok" if code == 0 else " FAILED")
    if code != 0:
        print(output[-3000:])
    return code == 0


def compile_backend() -> CompileResult:
    project = config.BACKEND_DIR
    if not (project / "tsconfig.json").exists():
        return CompileResult(False, 1, {"<project>": ["no tsconfig.json"]}, "")

    code, output = _run(["npx", "--yes", "tsc", "--noEmit", "-p", "tsconfig.json"], project)
    errors: dict[str, list[str]] = {}
    for line in output.splitlines():
        m = _TSC_ERROR.match(line.strip())
        if m and m.group("severity") == "error":
            rel = m.group("file").replace("\\", "/").lstrip("./")
            errors.setdefault(rel, []).append(
                f"line {m.group('line')}:{m.group('col')} {m.group('code')}: {m.group('message')}"
            )
    total = sum(len(v) for v in errors.values())
    return CompileResult(code == 0 and total == 0, total, errors, output)


def compile_frontend() -> CompileResult:
    project = config.FRONTEND_DIR
    if not (project / "package.json").exists():
        return CompileResult(False, 1, {"<project>": ["no package.json"]}, "")

    # ng build type-checks templates as well, which plain tsc does not.
    code, output = _run(
        ["npx", "--yes", "ng", "build", "--configuration", "development"],
        project, timeout=1200,
    )
    errors: dict[str, list[str]] = {}
    pending: str | None = None
    for line in output.splitlines():
        loc = _NG_LOCATION.match(line)
        if loc and pending:
            rel = loc.group("file").replace("\\", "/").lstrip("./")
            errors.setdefault(rel, []).append(
                f"line {loc.group('line')}:{loc.group('col')} {pending}")
            pending = None
            continue
        m = _NG_ERROR.search(line)
        if m:
            pending = m.group("message").strip()
    # Errors reported without a location still count.
    if pending:
        errors.setdefault("<unlocated>", []).append(pending)
    for line in output.splitlines():
        m = _TSC_ERROR.match(line.strip())
        if m and m.group("severity") == "error":
            rel = m.group("file").replace("\\", "/").lstrip("./")
            entry = f"line {m.group('line')}:{m.group('col')} {m.group('code')}: {m.group('message')}"
            if entry not in errors.get(rel, []):
                errors.setdefault(rel, []).append(entry)

    total = sum(len(v) for v in errors.values())
    return CompileResult(code == 0 and total == 0, total, errors, output)


# ------------------------------------------------------------- prompting ---
def _repair_prompt(side: str, project: Path, result: CompileResult, spec: str) -> str:
    """
    Send back only the files that failed, plus the files they import.

    Sending the whole project again would work but wastes most of the window on
    code that already compiles, and invites the model to rewrite things that
    were fine.
    """
    wanted: set[Path] = set()
    for rel in result.errors_by_file:
        candidate = project / rel
        if candidate.exists():
            wanted.add(candidate)

    # Pull in the direct imports of each failing file, since the fix is often
    # "this export is named differently over there".
    import_re = re.compile(r"""from\s+['"](\.[^'"]+)['"]""")
    for path in list(wanted):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for rel_import in import_re.findall(text):
            for suffix in (".ts", ".tsx", "/index.ts", ".html", ".css"):
                neighbour = (path.parent / (rel_import + suffix)).resolve()
                if neighbour.exists() and neighbour.is_file():
                    wanted.add(neighbour)
                    break

    blocks = []
    for path in sorted(wanted):
        try:
            rel = path.relative_to(config.OUTPUT_DIR).as_posix()
            blocks.append(f"\n\n===== {rel} =====\n{path.read_text(encoding='utf-8')}")
        except (OSError, ValueError, UnicodeDecodeError):
            continue

    error_report = "\n".join(
        f"\n{rel}\n" + "\n".join(f"  {e}" for e in errs)
        for rel, errs in sorted(result.errors_by_file.items())
    )

    root = "backend/" if side == "backend" else "frontend/"
    return f"""\
# Task: fix the compiler errors

The generated {side} does not compile. Below are the exact compiler errors and
the source of every file involved. Return corrected files.

## Compiler errors ({result.error_count} in {len(result.errors_by_file)} file(s))

```
{error_report}
```

## The files involved

================ BEGIN SOURCE ================
{''.join(blocks)}
================= END SOURCE =================

## How to fix them

Work through the errors one at a time and fix the **cause**, not the symptom.

- `Cannot find name` or `Cannot find module` — the import path is wrong, or the
  thing was never written. Correct the path, or correct the import to match
  what the target file actually exports.
- `has no exported member` — default versus named export mismatch. Look at the
  exporting file above and match it.
- `Type X is not assignable to type Y` — fix the type, do not cast it away.
- `implicitly has an 'any' type` — declare the real type.
- Never silence an error with `any`, `as unknown as`, `@ts-ignore`, or by
  loosening `tsconfig.json`. Those hide the defect instead of removing it.
- If two files genuinely disagree about a name or a shape, change whichever one
  is wrong relative to the specification, and return both.

## Output contract

Return **only** the files you changed, each complete, in exactly this form:

FILE: {root}path/to/file.ext

```language
COMPLETE FILE CONTENT
```

Complete files, not diffs and not fragments. Do not return a file you did not
change. No prose before the first `FILE:` line or after the last fence.

## Reminder of the requirements

The corrected code must still satisfy the specification. Do not delete a
feature to make an error go away.

================ BEGIN GHERKIN SPECIFICATION ================
{spec}
================= END GHERKIN SPECIFICATION =================
"""


def repair_loop(side: str, spec: str, max_rounds: int | None = None) -> CompileResult:
    """Compile, and while it fails, ask the model to fix what the compiler said."""
    max_rounds = max_rounds if max_rounds is not None else config.MAX_REPAIR_ROUNDS
    project = config.BACKEND_DIR if side == "backend" else config.FRONTEND_DIR
    compile_fn = compile_backend if side == "backend" else compile_frontend

    print(f"\n=== compiling {side} ===")
    result = compile_fn()
    print(f"  {result.summary()}")

    round_number = 0
    while not result.ok and round_number < max_rounds:
        round_number += 1
        print(f"\n=== {side} repair round {round_number}/{max_rounds} ===")
        for rel, errs in sorted(result.errors_by_file.items())[:10]:
            print(f"  {rel}: {len(errs)} error(s) — {errs[0][:90]}")

        prompt = _repair_prompt(side, project, result, spec)
        try:
            llm.call(f"{side}-repair", prompt, repair_round=round_number, strict=False)
        except RuntimeError as exc:
            print(f"  repair call failed: {exc}")
            break

        previous = result.error_count
        result = compile_fn()
        print(f"  {result.summary()} (was {previous})")

        if not result.ok and result.error_count >= previous:
            print("  no improvement this round; stopping rather than looping")
            break

    verdict = config.RUNS_DIR / llm.run_id() / f"{side}-compile.json"
    verdict.parent.mkdir(parents=True, exist_ok=True)
    verdict.write_text(json.dumps({
        "side": side,
        "ok": result.ok,
        "error_count": result.error_count,
        "repair_rounds_used": round_number,
        "errors_by_file": result.errors_by_file,
    }, indent=2), encoding="utf-8")

    if result.ok:
        print(f"\n  {side}: COMPILES"
              + (f" (after {round_number} repair round(s))" if round_number else ""))
    else:
        print(f"\n  {side}: STILL FAILING — {result.summary()}")
        print(f"  full compiler output and per-file errors: {verdict}")
    return result
