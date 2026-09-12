"""
compilers.py — run the compilers and parse their output reliably.

Getting the parsing wrong fails SILENTLY in the worst possible direction: if the
parser matches nothing, the repair loop sees zero errors and reports a clean
compile while the build is broken. The committed run under
runs/run-20260911T143100Z is exactly that failure — `"ok": false` with
`"error_count": 0` on both sides, which says nothing about the generated code
and everything about the parser.

Four real traps, all verified against TypeScript and the Angular esbuild builder
rather than assumed:

1. **tsc has two output formats.** Piped to a subprocess it emits

       src/x.ts(4,17): error TS2304: Cannot find name 'compose'.

   but in a terminal, or when `"pretty": true` is set in tsconfig.json, it
   emits

       src/x.ts:4:17 - error TS2304: Cannot find name 'compose'.

   A parser written for one silently matches nothing on the other. The tsconfig
   case is the dangerous one: it applies even when piped, so the format flips
   based on a file the pipeline did not write.

2. **Pretty output is full of ANSI escapes.** `\x1b[96msrc/x.ts\x1b[0m:...`
   Any pattern anchored on a literal filename fails on it.

3. **Angular's esbuild builder splits an error across two lines** — the
   message on one, the location on the next — and marks it with `✘ [ERROR]`
   rather than anything tsc-shaped. The older webpack builder emits tsc-shaped
   lines instead. Both still occur in the wild.

4. **The command may not exist.** A missing `npx` is exit code 127 with no
   parseable output, which looks identical to an unrecognised format. It is
   reported separately, because the fix is completely different.

So: force the deterministic format where possible, strip ANSI regardless, accept
every format, and distinguish "no errors" from "could not tell".
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import config

# ---------------------------------------------------------------- ANSI -----
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    return _ANSI.sub("", text)


# ------------------------------------------------------------- patterns ----
# tsc, piped / --pretty false:
#   src/x.ts(4,17): error TS2304: Cannot find name 'compose'.
TSC_PLAIN = re.compile(
    r"^(?P<file>[^\s(][^(]*?)\((?P<line>\d+),(?P<col>\d+)\)\s*:\s*"
    r"(?P<severity>error|warning)\s+(?P<code>[A-Z]+\d+)\s*:\s*(?P<message>.*)$"
)

# tsc, --pretty true / terminal:
#   src/x.ts:4:17 - error TS2304: Cannot find name 'compose'.
# Angular's webpack builder also emits this, sometimes behind "Error: ".
TSC_PRETTY = re.compile(
    r"^(?:Error:\s*)?(?P<file>[^\s:][^:]*?):(?P<line>\d+):(?P<col>\d+)\s*-\s*"
    r"(?P<severity>error|warning)\s+(?P<code>[A-Z]+\d+)\s*:\s*(?P<message>.*)$"
)

# Angular esbuild builder, message line:
#   ✘ [ERROR] TS2304: Cannot find name 'compose'. [plugin angular-compiler]
NG_MESSAGE = re.compile(
    r"^\s*[✘✗x×]?\s*\[(?P<severity>ERROR|WARNING)\]\s*"
    r"(?:(?P<code>[A-Z]+\d+)\s*:\s*)?(?P<message>.*?)"
    r"(?:\s*\[plugin[^\]]*\])?\s*$"
)

# Angular esbuild builder, location line that follows it:
#       src/app/x.ts:17:17:
NG_LOCATION = re.compile(
    r"^\s+(?P<file>[^\s:][^:]*?\.\w+):(?P<line>\d+):(?P<col>\d+):?\s*$"
)

# "command not found" as reported by run() below.
_NOT_FOUND = re.compile(r"^command not found: ")


@dataclass
class CompileResult:
    ok: bool
    error_count: int
    errors_by_file: dict[str, list[str]]
    raw: str
    exit_code: int = 0
    parse_failed: bool = False
    command: str = ""
    tool_missing: bool = False

    def summary(self) -> str:
        if self.tool_missing:
            return f"could not run: {self.command}"
        if self.parse_failed:
            return (f"exit code {self.exit_code} but NO errors could be parsed "
                    f"— the output format was not recognised")
        if self.ok:
            return "compiles cleanly"
        return f"{self.error_count} error(s) across {len(self.errors_by_file)} file(s)"

    def blocked(self) -> bool:
        """True when the result says nothing about the code — a pipeline fault."""
        return self.tool_missing or self.parse_failed


# ------------------------------------------------------------ the parser ---
def parse_compiler_output(text: str) -> dict[str, list[str]]:
    """
    Extract errors from tsc or Angular output, in any of their formats.

    Returns {relative file path: [error description, ...]}.
    Warnings are ignored — only errors block a build.
    """
    text = strip_ansi(text)
    lines = text.splitlines()
    errors: dict[str, list[str]] = {}
    seen: set[tuple[str, str]] = set()

    def add(file: str, line: str, col: str, code: str, message: str) -> None:
        rel = file.replace("\\", "/").strip()
        while rel.startswith("./"):
            rel = rel[2:]
        entry = f"line {line}:{col} {code + ': ' if code else ''}{message}".strip()
        key = (rel, entry)
        if key in seen:
            return
        seen.add(key)
        errors.setdefault(rel, []).append(entry)

    pending: tuple[str, str] | None = None      # (code, message) awaiting a location

    for raw_line in lines:
        line = raw_line.rstrip()

        # --- Angular esbuild: a location line completing a pending message ---
        if pending is not None:
            location = NG_LOCATION.match(line)
            if location:
                code, message = pending
                add(location.group("file"), location.group("line"),
                    location.group("col"), code, message)
                pending = None
                continue
            # A blank line between message and location is normal; keep waiting.
            if not line.strip():
                continue
            # Anything else means the message had no location. Record it anyway,
            # so an error is never lost just because it was unlocated.
            code, message = pending
            add("<no location reported>", "0", "0", code, message)
            pending = None

        if not line.strip():
            continue

        # --- tsc, both formats ------------------------------------------
        for pattern in (TSC_PLAIN, TSC_PRETTY):
            match = pattern.match(line)
            if match:
                if match.group("severity").lower() == "error":
                    add(match.group("file"), match.group("line"), match.group("col"),
                        match.group("code"), match.group("message"))
                break
        else:
            # --- Angular esbuild message line ---------------------------
            message_match = NG_MESSAGE.match(line)
            if message_match and message_match.group("severity") == "ERROR":
                pending = (message_match.group("code") or "",
                           message_match.group("message").strip())

    if pending is not None:
        code, message = pending
        add("<no location reported>", "0", "0", code, message)

    return errors


# ------------------------------------------------------------- running -----
def run(command: list[str], cwd: Path, timeout: int = 900) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            # NO_COLOR and FORCE_COLOR=0 suppress ANSI in most Node tooling.
            # Belt and braces: strip_ansi runs regardless.
            env={**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0", "CI": "1"},
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return 127, f"command not found: {command[0]}"
    except OSError as exc:
        return 126, f"could not run {command[0]}: {exc}"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s: {' '.join(command)}"


def tool_command(project: Path, tool: str, *args: str) -> list[str]:
    """
    Prefer the binary npm already installed into the project.

    `npx --yes tsc` will happily DOWNLOAD a TypeScript release when the project
    does not have one — so a failed `npm install` turns into a type-check
    against a different compiler version than package.json pins, and the errors
    you then attribute to the model are partly the toolchain's. Using
    node_modules/.bin directly when it exists removes that variable; npx stays
    as the fallback so the pipeline still runs on a machine mid-setup.
    """
    binary = project / "node_modules" / ".bin" / tool
    for candidate in (binary, binary.with_suffix(".cmd"), binary.with_suffix(".exe")):
        if candidate.exists():
            return [str(candidate), *args]
    return [config.NPX, "--yes", tool, *args]


def _result_from(command: list[str], code: int, output: str) -> CompileResult:
    errors = parse_compiler_output(output)
    total = sum(len(v) for v in errors.values())
    missing = code == 127 and bool(_NOT_FOUND.match(output.strip()))
    return CompileResult(
        ok=(code == 0 and total == 0),
        error_count=total,
        errors_by_file=errors,
        raw=output,
        exit_code=code,
        # The safety net: a non-zero exit with nothing parsed means the parser
        # failed, not that the project is fine. Without this the repair loop
        # would announce a clean build over a broken one.
        parse_failed=(code != 0 and total == 0 and not missing),
        command=" ".join(command),
        tool_missing=missing,
    )


def compile_typescript(project: Path, tsconfig: str = "tsconfig.json",
                       timeout: int = 900) -> CompileResult:
    """
    Type-check with tsc.

    `--pretty false` is passed explicitly. It overrides `"pretty": true` in
    tsconfig.json, which would otherwise flip the output format based on a file
    the pipeline did not write — and a flipped format means zero errors parsed
    and a false "compiles cleanly".
    """
    if not (project / tsconfig).exists():
        return CompileResult(False, 1, {"<project>": [f"no {tsconfig}"]}, "",
                             exit_code=1, command=f"tsc -p {tsconfig}")

    command = tool_command(project, "tsc",
                           "--noEmit", "--pretty", "false", "-p", tsconfig)
    code, output = run(command, project, timeout)
    return _result_from(command, code, output)


def compile_angular(project: Path, timeout: int = 1200) -> CompileResult:
    """
    Check an Angular project.

    Two passes, cheapest first:

    1. `tsc --noEmit` over tsconfig.app.json. Fast, deterministic output, and
       catches every TypeScript error.
    2. `ng build`, only if the first pass is clean. It is the only thing that
       type-checks TEMPLATES, but it is slow and its output format is the
       awkward one, so there is no reason to pay for it while plain TypeScript
       errors are still outstanding.

    Pass 2 is not optional decoration. Angular's strictTemplates catches a whole
    class of generated-code defect that plain tsc cannot see: a binding to a
    property the component does not have, a component used in a template but
    missing from `imports`, a pipe that was never imported. A generated Angular
    app that passes only pass 1 has not been meaningfully checked.
    """
    app_config = "tsconfig.app.json" if (project / "tsconfig.app.json").exists() \
        else "tsconfig.json"

    first = compile_typescript(project, app_config, timeout)
    if not first.ok or first.blocked():
        return first

    command = tool_command(project, "ng",
                           "build", "--configuration", "development")
    code, output = run(command, project, timeout)
    return _result_from(command, code, output)
