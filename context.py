"""
context.py — assemble what a prompt is allowed to see.

Three jobs:

1. Load the specification once, recursively.
2. Give each generation stage only the existing code it actually needs, inside
   a character budget, and be explicit with the model about anything that did
   not fit.
3. Extract the real HTTP surface from the generated backend, so the frontend
   is built against the routes that exist rather than routes it invents.

Point 3 is the fix for the most common class of runtime failure in this kind of
pipeline: everything compiles, and every request 404s, because the Angular
service calls /api/spaces/search while the router exposes /api/space/find.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import config


# ----------------------------------------------------------- the spec -----
def load_specification() -> str:
    """Every .feature file, recursively, in a stable order."""
    if not config.FEATURES_DIR.exists():
        raise RuntimeError(f"Features directory does not exist: {config.FEATURES_DIR}")

    files = sorted(config.FEATURES_DIR.rglob("*.feature"))
    if not files:
        raise RuntimeError(
            f"No .feature files found under {config.FEATURES_DIR} (searched recursively)")

    parts = []
    for path in files:
        label = path.relative_to(config.FEATURES_DIR).as_posix()
        parts.append(f"\n\n===== {label} =====\n{path.read_text(encoding='utf-8')}")

    spec = "".join(parts)
    print(f"  specification: {len(files)} feature files, {len(spec):,} chars")
    return spec


def spec_fingerprint(spec: str) -> str:
    """
    A content hash of the specification, recorded in the run manifest.

    Two runs are only comparable if they were given the same requirements. A
    directory path does not establish that — you will edit the feature files
    between runs, and six weeks later the manifest's `features_dir` will not
    tell you which version each model saw. The hash does.
    """
    return hashlib.sha256(spec.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------- existing generated code --
TEXT_SUFFIXES = {
    ".ts", ".js", ".mjs", ".cjs", ".json", ".html", ".css", ".scss",
    ".env", ".md", ".yml", ".yaml",
}


def collect_code(*directories: Path, budget: int | None = None) -> str:
    """
    Concatenate the files under the given directories, inside a budget.

    A stage asks for the directories it depends on, not for everything:
    controllers need models, services and middlewares, but have no business
    reading routers. Dumping the whole tree into every prompt is what pushes the
    context past the window.

    **Overflow behaviour.** The previous version raised, which killed the run at
    whichever stage first crossed the line — usually controllers, deep into an
    hour of generation, with nothing salvageable. Silent truncation is worse
    still: a model handed a context that stops mid-file will confidently invent
    the rest of it.

    So: include as many complete files as fit, and end the block with an
    explicit list of what was left out. A model that is TOLD `space.service.ts`
    is missing can say "I cannot see this export" or import conservatively. A
    model that is not told will guess. Smaller files are preferred when
    trimming, because the number of modules whose exports the model can see
    exactly is what prevents invented imports.
    """
    budget = budget if budget is not None else config.CODE_CONTEXT_BUDGET_CHARS

    entries: list[tuple[str, str]] = []          # (relative path, chunk)
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
            except (UnicodeDecodeError, OSError):
                continue
            rel = path.relative_to(config.OUTPUT_DIR).as_posix()
            entries.append((rel, f"\n\n===== EXISTING FILE: {rel} =====\n{content}"))

    total = sum(len(chunk) for _, chunk in entries)
    if total <= budget:
        return "".join(chunk for _, chunk in entries)

    # Over budget: keep the most files we can, then say what is missing.
    keep: set[str] = set()
    used = 0
    for rel, chunk in sorted(entries, key=lambda e: len(e[1])):
        if used + len(chunk) > budget:
            continue
        keep.add(rel)
        used += len(chunk)

    omitted = [rel for rel, _ in entries if rel not in keep]
    print(f"  ! code context {total:,} chars over the {budget:,} budget — "
          f"{len(omitted)} file(s) omitted, and the prompt says which")

    body = "".join(chunk for rel, chunk in entries if rel in keep)
    listing = "\n".join(f"  - {rel}" for rel in omitted)
    body += f"""

===== FILES OMITTED FROM THIS CONTEXT =====
The following files exist in the project but did not fit in this prompt:

{listing}

You cannot see their contents. Do not guess at what they export. If you need
something from one of them, import it under the name the naming convention
implies and add a one-line comment saying which file you could not see.
"""
    return body


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
_HTTP_METHODS = "get|post|put|patch|delete|all|options|head"

# const router = Router()  /  const authRouter: Router = express.Router()
_ROUTER_DECL_RE = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::\s*[\w.<>]+\s*)?=\s*"
    r"(?:[A-Za-z_$][\w$]*\s*\.\s*)?Router\s*\(",
)

# app.use('/api/spaces', spacesRouter)  — the app variable may be called anything
_MOUNT_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*\.\s*use\s*\(\s*[\"'`](/[^\"'`]*)[\"'`]\s*,\s*"
    r"([A-Za-z_$][\w$]*)",
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


def _router_variables(text: str) -> list[str]:
    """
    The names this file gives its routers.

    The previous version matched the literal string `router.get(...)`, and
    nothing in the prompts required that name. A model writing the perfectly
    ordinary

        const authRouter = express.Router();
        authRouter.post('/login', ...)

    produced zero extracted routes, so the frontend was generated against
    guessed URLs — and the result was recorded as a weak model rather than as a
    regex that assumed a variable name. The prompt now asks for `router`, and
    this finds whatever the model actually used either way.
    """
    found = list(dict.fromkeys(_ROUTER_DECL_RE.findall(text)))
    return found or ["router"]


def _routes_in_text(text: str) -> list[tuple[str, str]]:
    """
    (METHOD, path) for every route in one router file, in source order.

    Handles both forms:
        router.get('/x', handler)
        router.route('/x').get(handler).post(handler)
    The chained form was named in the old comment but never actually matched,
    because `route` was missing from the method alternation.
    """
    found: list[tuple[int, str, str]] = []

    for variable in _router_variables(text):
        escaped = re.escape(variable)

        direct = re.compile(
            rf"\b{escaped}\s*\.\s*({_HTTP_METHODS})\s*\(\s*[\"'`]([^\"'`]*)[\"'`]",
            re.IGNORECASE,
        )
        for match in direct.finditer(text):
            found.append((match.start(), match.group(1), match.group(2)))

        chained = re.compile(
            rf"\b{escaped}\s*\.\s*route\s*\(\s*[\"'`]([^\"'`]*)[\"'`]\s*\)",
            re.IGNORECASE,
        )
        for match in chained.finditer(text):
            path = match.group(1)
            tail = text[match.end(): match.end() + 800]
            end = tail.find(";")
            segment = tail if end == -1 else tail[:end]
            for method in re.finditer(rf"\.\s*({_HTTP_METHODS})\s*\(", segment,
                                      re.IGNORECASE):
                found.append((match.start() + method.start(), method.group(1), path))

    found.sort(key=lambda item: item[0])
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple[str, str]] = []
    for _, method, path in found:
        key = (method.lower(), path)
        if key in seen:
            continue
        seen.add(key)
        ordered.append((method, path))
    return ordered


def _mount_prefixes(backend_src: Path) -> dict[str, str]:
    """{router module key: mount prefix} read from the server entry points."""
    mounts: dict[str, str] = {}
    entries = (list(backend_src.rglob("server.ts"))
               + list(backend_src.rglob("app.ts"))
               + list(backend_src.rglob("index.ts")))
    for entry in entries:
        try:
            text = entry.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        variable_to_module: dict[str, str] = {}
        for pattern in (_IMPORT_RE, _REQUIRE_RE):
            for variable, module in pattern.findall(text):
                variable_to_module[variable] = _module_key(module)
        for _, prefix, variable in _MOUNT_RE.findall(text):
            if variable in variable_to_module:
                mounts[variable_to_module[variable]] = prefix.rstrip("/")
    return mounts


def api_surface_routes() -> list[tuple[str, str, str]]:
    """(source file, METHOD, full path) for every route, machine-readable."""
    backend_src = config.BACKEND_DIR / "src"
    if not backend_src.exists():
        return []

    mounts = _mount_prefixes(backend_src)
    rows: list[tuple[str, str, str]] = []

    router_files = sorted(
        p for p in backend_src.rglob("*.ts")
        if any(key in p.as_posix() for key in ("/routers/", "/routes/"))
    )
    for path in router_files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        prefix = mounts.get(_module_key(path.name), "")
        rel = path.relative_to(config.OUTPUT_DIR).as_posix()
        for method, route in _routes_in_text(text):
            full = (prefix + route).replace("//", "/")
            # router.get('/', ...) under a prefix is the prefix itself, not
            # "<prefix>/" — a trailing slash here would be copied verbatim into
            # the front-end service and produce a different URL.
            if len(full) > 1:
                full = full.rstrip("/")
            rows.append((rel, method.upper(), full or "/"))
    return rows


def extract_api_surface() -> str:
    """
    The real HTTP surface, formatted for a prompt: METHOD + full path, with the
    mount prefix applied.

    This is handed to every frontend prompt. Without it the frontend guesses
    URLs from the Gherkin, and guesses differently from how the backend guessed.
    """
    backend_src = config.BACKEND_DIR / "src"
    if not backend_src.exists():
        return "  (backend not generated yet)"

    rows = api_surface_routes()
    if not rows:
        return (
            "  (no routes could be extracted — check that routers use\n"
            "   router.<method>('/path', ...) and are mounted with app.use)"
        )

    lines: list[str] = []
    current = ""
    mounts = _mount_prefixes(backend_src)
    for rel, method, full in rows:
        if rel != current:
            prefix = mounts.get(_module_key(Path(rel).name), "")
            lines.append(f"\n  from {rel}" + (f"  (mounted at {prefix})" if prefix else ""))
            current = rel
        lines.append(f"    {method:<6} {full}")
    return "\n".join(lines)


def surface_is_usable(surface: str) -> bool:
    return "not generated yet" not in surface and "no routes could be extracted" not in surface


# --------------------------------------------------------- spec metrics ----
def count_scenarios(spec: str) -> dict[str, int]:
    """Rough size of the specification, for the run record."""
    return {
        # Counted with a line-anchored regex. The previous version counted the
        # literal substrings "\nFeature:" and "\n  Feature:", which misses any
        # other indentation and double-counts nothing — it happened to be right
        # for this spec and would quietly be wrong for the next one.
        "features": len(re.findall(r"^\s*Feature:", spec, re.M)),
        "scenarios": len(re.findall(r"^\s*Scenario:", spec, re.M)),
        "scenario_outlines": len(re.findall(r"^\s*Scenario Outline:", spec, re.M)),
        "backgrounds": len(re.findall(r"^\s*Background:", spec, re.M)),
        # Table rows minus one header row per Examples block is the number of
        # concrete cases; the raw row count overstates it.
        "examples_rows": max(0, len(re.findall(r"^\s*\|.*\|\s*$", spec, re.M))
                             - len(re.findall(r"^\s*Examples:", spec, re.M))),
    }
