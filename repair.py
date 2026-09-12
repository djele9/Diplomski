"""
repair.py — compile the generated code and feed the errors back.

This is the highest-value part of the pipeline. Generation produces code that is
*plausible*; compilation is the only thing that establishes whether it is
*correct enough to run*. Two or three rounds of "here are your errors, return
the corrected files" typically takes a project that does not build to one that
does.

It also produces the honest number for the write-up: "compiled after N repair
rounds" is a far better measure of a model than "produced N files".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import config
import llm
from compilers import (CompileResult, compile_angular, compile_typescript, run,
                       tool_command)

# The compiler-output parsing lives in compilers.py. It was extracted because
# getting it wrong fails silently in the worst direction: a parser that matches
# nothing reports zero errors, and the repair loop then announces a clean build
# over a broken one.


@dataclass
class InstallResult:
    ok: bool
    detail: str = ""


def install(project: Path) -> InstallResult:
    """
    `npm install`, not `npm ci`.

    The prompts forbid generating a lockfile precisely because a model-written
    one contains invented integrity hashes, and `npm ci` fails on it. Installing
    from package.json alone lets npm resolve and write a real lockfile.

    The result is RETURNED and recorded now. Previously it was discarded, so a
    failed install was followed by a compile that either type-checked against a
    TypeScript version npx downloaded on the spot, or failed for a reason that
    had nothing to do with the generated code — and either way the run record
    blamed the model.
    """
    if not (project / "package.json").exists():
        detail = f"no package.json in {project.name}"
        print(f"  {detail}, skipping install")
        return InstallResult(False, detail)

    stale = project / "package-lock.json"
    if stale.exists():
        stale.unlink()
        print("  removed a generated package-lock.json (integrity hashes are invented)")

    print(f"  npm install in {project.name} ...", end="", flush=True)
    code, output = run([config.NPM, "install", "--no-audit", "--no-fund"],
                       project, timeout=1200)
    print(" ok" if code == 0 else " FAILED")
    if code != 0:
        print(output[-3000:])
        return InstallResult(False, f"npm install exited {code}: {output[-500:].strip()}")
    return InstallResult(True)


def compile_backend() -> CompileResult:
    return compile_typescript(config.BACKEND_DIR)


def compile_frontend() -> CompileResult:
    return compile_angular(config.FRONTEND_DIR)


# ------------------------------------------------------------- prompting ---
def _repair_prompt(side: str, project: Path, result: CompileResult, spec: str) -> str:
    """
    Send back only the files that failed, plus the files they import.

    Sending the whole project again would work but wastes most of the window on
    code that already compiles, and invites the model to rewrite things that
    were fine.
    """
    import re

    wanted: set[Path] = set()
    for rel in result.errors_by_file:
        candidate = project / rel
        if candidate.exists() and candidate.is_file():
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

    # An Angular component's template and stylesheet are part of the unit the
    # compiler checks. A strictTemplates error is reported against the .ts file
    # but is usually caused by the .html, and sending the .ts alone asks the
    # model to fix a file that is not wrong.
    for path in list(wanted):
        if path.suffix == ".ts":
            for sibling_suffix in (".html", ".css"):
                sibling = path.with_suffix(sibling_suffix)
                if sibling.exists():
                    wanted.add(sibling)

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

Paths in this list are relative to the {side} project root. In your answer the
same file is written as `{root}<that path>`.

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
change. No prose before the first `FILE:` line and none after the last closing
fence — not a summary, not a usage example, nothing.

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
    root = "backend/" if side == "backend" else "frontend/"

    print(f"\n=== compiling {side} ===")
    result = compile_fn()
    print(f"  {result.summary()}")

    # A result that says nothing about the code is a pipeline fault, not a model
    # fault, and repairing on it would send the model an empty error list.
    # Worse, treating it as a pass would announce a clean build over a broken
    # one — which is precisely what the committed run did.
    if result.blocked():
        _report_blocked(side, result)
        _write_verdict(side, result, 0)
        return result

    round_number = 0
    while not result.ok and round_number < max_rounds:
        round_number += 1
        print(f"\n=== {side} repair round {round_number}/{max_rounds} ===")
        for rel, errs in sorted(result.errors_by_file.items())[:10]:
            print(f"  {rel}: {len(errs)} error(s) — {errs[0][:90]}")

        prompt = _repair_prompt(side, project, result, spec)
        try:
            record = llm.call(f"{side}-repair", prompt,
                              expected_root=root, repair_round=round_number)
        except llm.ModelUnavailable as exc:
            print(f"  repair stopped: {exc}")
            break
        if not record.files_written:
            print("  the repair returned no usable files; stopping")
            break

        previous = result.error_count
        result = compile_fn()
        print(f"  {result.summary()} (was {previous})")

        if result.blocked():
            _report_blocked(side, result)
            break

        if not result.ok and result.error_count >= previous:
            print("  no improvement this round; stopping rather than looping")
            break

    _write_verdict(side, result, round_number)

    if result.ok:
        print(f"\n  {side}: COMPILES"
              + (f" (after {round_number} repair round(s))" if round_number else ""))
    else:
        print(f"\n  {side}: STILL FAILING — {result.summary()}")
    return result


def _report_blocked(side: str, result: CompileResult) -> None:
    if result.tool_missing:
        print(f"\n  {side}: COMPILER COULD NOT BE RUN")
        print(f"  command: {result.command}")
        print("  The build tool was not found. Run `npm install` in the project,")
        print("  or check that Node.js is on PATH.")
        return
    print(f"\n  {side}: COMPILER OUTPUT NOT UNDERSTOOD")
    print(f"  command:   {result.command}")
    print(f"  exit code: {result.exit_code}")
    print("  The compiler failed but no errors could be parsed from its output.")
    print("  This is a bug in the parser, not in the generated code.")
    print("  First 40 lines of what it actually printed:\n")
    for line in result.raw.splitlines()[:40]:
        print(f"    {line}")
    print("\n  Add the format to compilers.parse_compiler_output and re-run.")


def _write_verdict(side: str, result: CompileResult, rounds: int) -> None:
    verdict = config.RUNS_DIR / llm.run_id() / f"{side}-compile.json"
    verdict.parent.mkdir(parents=True, exist_ok=True)
    verdict.write_text(json.dumps({
        "side": side,
        "ok": result.ok,
        "error_count": result.error_count,
        "repair_rounds_used": rounds,
        "exit_code": result.exit_code,
        "parse_failed": result.parse_failed,
        "tool_missing": result.tool_missing,
        "command": result.command,
        "errors_by_file": result.errors_by_file,
        # The tail of the raw output, so that a result you cannot explain six
        # weeks later can still be explained.
        "raw_tail": result.raw[-4000:],
    }, indent=2), encoding="utf-8")
    print(f"  compile record: {verdict}")
