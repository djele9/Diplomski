"""
context.py — assemble what a prompt is allowed to see.

Three jobs:

1. Load the specification once, recursively.
2. Give each generation stage only the existing code it actually needs, inside
   a character budget, and raise rather than silently overflow the window.
3. Extract the real HTTP surface from the generated backend, so the frontend
   is built against the routes that exist rather than routes it invents.

Point 3 is the fix for the most common class of runtime failure in this kind of
pipeline: everything compiles, and every request 404s, because the Angular
service calls /api/spaces/search while the router exposes /api/space/find.
"""

from __future__ import annotations

import re
from pathlib import Path

import config


# ----------------------------------------------------------- the spec -----
def load_specification() -> str:
    """
    Every .feature file, recursively, in a stable order.
    """
    if not config.FEATURES_DIR.exists():
        raise RuntimeError(f"Features directory does not exist: {config.FEATURES_DIR}")

    files = sorted(config.FEATURES_DIR.rglob("*.feature"))
    if not files:
        raise RuntimeError(f"No .feature files found under {config.FEATURES_DIR} (searched recursively)")

    parts = []
    for path in files:
        label = path.relative_to(config.FEATURES_DIR).as_posix()
        parts.append(f"\n\n===== {label} =====\n{path.read_text(encoding='utf-8')}")

    spec = "".join(parts)
    print(f"  specification: {len(files)} feature files, {len(spec):,} chars")
    return spec


# ------------------------------------------------- existing generated code --
TEXT_SUFFIXES = {
    ".ts", ".js", ".mjs", ".cjs", ".json", ".html", ".css", ".scss",
    ".env", ".md", ".yml", ".yaml",
}


def collect_code(*directories: Path, budget: int | None = None) -> str:
    """
    Concatenate the files under the given directories, newest-relevant first.

    A stage asks for the directories it
    depends on, not for everything: controllers need models, services and
    middlewares, but have no business reading routers. Dumping the whole tree
    into every prompt is what pushes the context past the window.

    Raises if the result exceeds the budget, rather than letting the model
    silently lose the tail of its own codebase.
    """
    budget = budget if budget is not None else config.CODE_CONTEXT_BUDGET_CHARS

    chunks: list[str] = []
    total = 0
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            if path.name in config.FORBIDDEN_OUTPUT_FILES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            rel = path.relative_to(config.OUTPUT_DIR).as_posix()
            chunk = f"\n\n===== EXISTING FILE: {rel} =====\n{content}"
            chunks.append(chunk)
            total += len(chunk)

    if total > budget:
        listing = "\n".join(
            f"    {c.splitlines()[1][len('===== EXISTING FILE: '):]}" for c in chunks[:40]
        )
        raise RuntimeError(
            f"Code context is {total:,} chars, over the {budget:,} budget.\n"
            f"Narrow the directories this stage asks for, or raise "
            f"CODE_CONTEXT_BUDGET_CHARS if the model's window allows it.\n"
            f"Files included:\n{listing}"
        )

    return "".join(chunks)


def describe_tree(*directories: Path) -> str:
    """A file listing without contents — cheap orientation for a prompt."""
    names = []
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                names.append(path.relative_to(config.OUTPUT_DIR).as_posix())
    return "\n".join(f"  {n}" for n in names) if names else "  (nothing generated yet)"


# ------------------------------------------------ backend HTTP surface -----
# router.get('/path', mw, handler)  /  router.route('/path').get(...)
_ROUTE_RE = re.compile(
    r"\brouter\s*\.\s*(get|post|put|patch|delete|all)\s*\(\s*[\"'`]([^\"'`]*)[\"'`]",
    re.IGNORECASE,
)
# app.use('/api/spaces', spacesRouter)
_MOUNT_RE = re.compile(
    r"\bapp\s*\.\s*use\s*\(\s*[\"'`](/[^\"'`]*)[\"'`]\s*,\s*([A-Za-z_$][\w$]*)",
)
# import spacesRouter from './routers/space.routes'
_IMPORT_RE = re.compile(
    r"\bimport\s+(?:\*\s+as\s+)?([A-Za-z_$][\w$]*)\s+from\s+[\"'`]([^\"'`]+)[\"'`]",
)
_REQUIRE_RE = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\s*\(\s*[\"'`]([^\"'`]+)[\"'`]",
)


def _module_key(module_or_file: str) -> str:
    """
    A comparison key that matches an import specifier to the file it names.

    The trap: Path("space.routes").stem is "space", because `.routes` looks
    like a suffix. So keying the import on .stem and the file on .stem gives
    "space" against "space.routes" and the mount prefix is never found — every
    route then appears unprefixed, and the front end is built against paths
    missing their /api/... root.

    Keying on the file NAME with only a real code extension removed makes both
    sides agree: "./routers/space.routes" and "space.routes.ts" both yield
    "space.routes".
    """
    name = Path(module_or_file).name
    for extension in (".ts", ".tsx", ".js", ".mjs", ".cjs"):
        if name.endswith(extension):
            return name[: -len(extension)]
    return name


def extract_api_surface() -> str:
    """
    Read the generated routers and server entry point, and report the real
    HTTP surface: METHOD + full path, with the mount prefix applied.

    This is handed to every frontend prompt. Without it the frontend guesses
    URLs from the Gherkin, and guesses differently from how the backend guessed.
    """
    backend_src = config.BACKEND_DIR / "src"
    if not backend_src.exists():
        return "  (backend not generated yet)"

    # Which router variable is mounted at which prefix, resolved through the
    # import that introduced the variable.
    mounts: dict[str, str] = {}   # router module key -> mount prefix
    for entry in list(backend_src.rglob("server.ts")) + list(backend_src.rglob("app.ts")):
        text = entry.read_text(encoding="utf-8")
        var_to_module: dict[str, str] = {}
        for rx in (_IMPORT_RE, _REQUIRE_RE):
            for var, module in rx.findall(text):
                var_to_module[var] = _module_key(module) #var = "authRouter" module = "./routers/auth.routes"
        for prefix, var in _MOUNT_RE.findall(text): #prefix = "/api/auth" var = "authRouter"
            if var in var_to_module:
                mounts[var_to_module[var]] = prefix.rstrip("/")

    # var_to_module = {
    #     "authRouter": "auth.routes"
    # }

    #mounts = {
    # "auth.routes": "/api/auth"
    # }

    lines: list[str] = []
    router_files = sorted(
        p for p in backend_src.rglob("*.ts")
        if any(k in p.as_posix() for k in ("/routers/", "/routes/"))
    )
    for path in router_files:
        prefix = mounts.get(_module_key(path.name), "")
        text = path.read_text(encoding="utf-8")
        found = _ROUTE_RE.findall(text)
        if not found:
            continue
        rel = path.relative_to(config.OUTPUT_DIR).as_posix()
        lines.append(f"\n  from {rel}" + (f"  (mounted at {prefix})" if prefix else ""))
        for method, route in found:
            full = (prefix + route).replace("//", "/")
            # router.get('/', ...) under a prefix is the prefix itself, not
            # "<prefix>/" — a trailing slash here would be copied verbatim into
            # the front-end service and produce a different URL.
            if len(full) > 1:
                full = full.rstrip("/")
            lines.append(f"    {method.upper():<6} {full or '/'}")

    if not lines:
        return (
            "  (no routes could be extracted — check that routers use\n"
            "   router.<method>('/path', ...) and are mounted with app.use)"
        )
    return "\n".join(lines)

#re.M omogućava da ^ znači početak svake linije, a ne samo početak celog stringa.
def count_scenarios(spec: str) -> dict[str, int]:
    """Rough size of the specification, for the run record."""
    return {
        "features": spec.count("\nFeature:") + spec.count("\n  Feature:"),
        "scenarios": len(re.findall(r"^\s*Scenario:", spec, re.M)),
        "scenario_outlines": len(re.findall(r"^\s*Scenario Outline:", spec, re.M)),
        "examples_rows": max(0, len(re.findall(r"^\s*\|.*\|\s*$", spec, re.M))),
    }
