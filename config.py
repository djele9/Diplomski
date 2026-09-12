"""
config.py — every setting in one place.

Nothing else in this package hardcodes a path, a model name or a generation
option. That matters for two reasons: you can point the pipeline at a different
application by changing FEATURES_DIR alone, and you can run the whole thing
across several models for the thesis comparison by changing MODEL.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

# --------------------------------------------------------------- paths -----
ROOT = Path(__file__).resolve().parent

# ---- the project ----------------------------------------------------------
#
# A "project" is one application domain: one brief, one generated specification,
# one generated application. They are kept side by side rather than one at a
# time, because a pipeline that can only hold one domain is a pipeline you
# cannot demonstrate is domain-independent — and "it worked for the one system I
# built it around" is the first thing an examiner will press on.
#
#     briefs/<project>.md          the handwritten brief
#     specs/<project>/<area>/*.feature    generated specification
#     apps/<project>/backend|frontend     generated application
#
# `set_project()` moves all of those at once. Nothing else in the codebase
# builds a path from a project name, so there is one place to get this right.
BRIEFS_DIR = ROOT / "briefs"
SPECS_ROOT = ROOT / "specs"
APPS_ROOT = ROOT / "apps"

PROJECT = "library-lending"

# The plain-language description of the application. This is the only
# handwritten input to the whole pipeline: the model writes the Gherkin from
# it, and the code is written from the Gherkin. Its numbered `C<n>:` capability
# lines are what make specification coverage measurable.
BRIEF_FILE = BRIEFS_DIR / f"{PROJECT}.md"

# The specification. rglob is used, so subdirectories work. As of the zero-shot
# stage this directory is normally GENERATED (see spec_generation.py) rather
# than handwritten.
FEATURES_DIR = SPECS_ROOT / PROJECT

# Everything generated lands here. Model-emitted paths are relative to this, so
# a model writing "backend/src/models/User.ts" produces
# apps/<project>/backend/src/models/User.ts
OUTPUT_DIR = APPS_ROOT / PROJECT
BACKEND_DIR = OUTPUT_DIR / "backend"
FRONTEND_DIR = OUTPUT_DIR / "frontend"

# Raw model responses, prompts and run metadata. Keeping these is what turns a
# code generator into an experiment you can write up.
RUNS_DIR = ROOT / "runs"


def set_project(name: str) -> None:
    """
    Point every path at one project.

    Call this before anything else reads a path. Modules read these as
    `config.X` at call time rather than binding them at import, so switching
    projects mid-process works — which is what running one comparison across
    several domains requires.
    """
    global PROJECT, BRIEF_FILE, FEATURES_DIR, OUTPUT_DIR, BACKEND_DIR, FRONTEND_DIR
    PROJECT = name
    BRIEF_FILE = BRIEFS_DIR / f"{name}.md"
    FEATURES_DIR = SPECS_ROOT / name
    OUTPUT_DIR = APPS_ROOT / name
    BACKEND_DIR = OUTPUT_DIR / "backend"
    FRONTEND_DIR = OUTPUT_DIR / "frontend"


def available_projects() -> list[str]:
    """Every brief in briefs/, by name."""
    if not BRIEFS_DIR.exists():
        return []
    return sorted(p.stem for p in BRIEFS_DIR.glob("*.md")
                  if p.stem.upper() != "TEMPLATE")


# --------------------------------------------------------------- model -----
# Override per run with --model. The candidate set for the comparison lives in
# MODEL_CANDIDATES below; this default is only what you get if you pass nothing.
MODEL = "gemma4:31b:cloud"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# The models the thesis compares. Edit to match what you have actually pulled —
# `ollama list` is the authority, tags drift. Keeping the list here rather than
# in a shell script means the run record and the candidate set cannot disagree.
#
# A large or hosted model kept in this list is useful as a REFERENCE CEILING:
# it tells you how much of a failure is the pipeline's fault and how much is the
# small model's. Mark it as such in the write-up rather than ranking it against
# the local ones as though it were a peer.
MODEL_CANDIDATES = (
    "qwen3-coder:30b",
    "devstral-small:24b",
    "mistral:7b",
    "llama3.1:8b",
)

# Generation options.
#
# num_ctx MUST be set explicitly. Ollama otherwise falls back to the model's
# default context — often 4096 — and silently discards everything past it.
# This is the single most common cause of nonsense output.
#
# 49152 rather than 131072: the largest prompt this pipeline has actually
# produced was 35,075 tokens (backend-5-controllers, run-20260911T143100Z), so
# 128k was four times what any stage needed. On a 7B-14B model held in VRAM the
# KV cache for a 128k window is the difference between running and an OOM, and
# it is dead weight even when it fits. Raise it only if a stage reports that it
# was truncated by the window — llm.call detects that explicitly.
#
# repeat_penalty is 1.0, not 1.1. Code is legitimately repetitive: imports,
# similar CRUD handlers, the same guard clause in twenty places. A repetition
# penalty pushes the model to vary tokens it should repeat, which produces
# renamed variables and subtly broken syntax.
OPTIONS = {
    "temperature": 0.1,
    "top_p": 0.9,
    "top_k": 40,
    "seed": 42,
    "repeat_penalty": 1.0,
    "num_ctx": 49152,
    "num_predict": 16000,
}

REQUEST_TIMEOUT_SECONDS = 1800

# Characters per token, used to estimate prompt size before sending and to
# detect after the fact that the window silently ate the prompt. Measured at
# roughly 3.2-3.8 on this codebase's prompts; 3.7 is the conservative end.
CHARS_PER_TOKEN = 3.7


# ---------------------------------------------------------- generation -----
# How many characters of existing generated code a single prompt may carry.
# 120k characters is about 32k tokens, which sits inside num_ctx above with room
# for the specification and the answer.
#
# Overflow is handled by DROPPING files and telling the model which ones are
# missing (see context.collect_code), not by raising and not by silently
# truncating. A model that knows it cannot see space.service.ts will say so; a
# model handed a silently shortened context will invent its contents.
CODE_CONTEXT_BUDGET_CHARS = 120_000

# How many times to feed compiler errors back and ask for corrections.
MAX_REPAIR_ROUNDS = 3

# How many times to feed the Gherkin linter's findings back at the zero-shot
# specification stage. Kept separate from MAX_REPAIR_ROUNDS because the two
# answer different questions and you will want to vary them independently —
# in particular, 0 here gives you the unaided first-attempt condition.
MAX_SPEC_REPAIR_ROUNDS = 2

# What a stage is allowed to emit. A model that ignores the output contract and
# returns "src/models/user.model.ts" instead of "backend/src/models/user.model.ts"
# would otherwise land the file at app/src/... — outside both projects, where it
# compiles against nothing and breaks the build for a reason that takes an hour
# to find. llm.safe_destination repairs a path that is unambiguously missing its
# root and rejects one that is ambiguous.
EXPECTED_ROOTS = ("backend/", "frontend/")

# Directories that may appear immediately under a project root. Used to decide
# whether a rootless path like "src/models/x.ts" can be safely repaired.
PROJECT_SUBDIRS = ("src", "public", "assets", "test", "tests", "e2e")

# Markers that mean the model elided part of a file instead of writing it.
#
# Split into two tiers, because a flat substring scan produces false positives
# on perfectly good code. A real example: a registration form containing the
# help text
#
#     "Optional — a default image will be used if omitted."
#
# is complete and correct, but a naive search for "OMITTED" flags it.
#
# STRONG markers are phrases that essentially never appear in working code, so
# they are flagged wherever they occur.
PLACEHOLDER_MARKERS_STRONG = (
    "OMITTED FOR BREVITY",
    "REST OF CODE",
    "REST OF FILE",
    "REST OF THE CODE",
    "REST OF THE FILE",
    "YOUR CODE HERE",
    "ADD YOUR CODE",
    "IMPLEMENT HERE",
    "IMPLEMENT THIS",
    "CODE HERE",
    "... rest of",
    "...rest of",
    "remaining fields",
    "remaining code",
    "and so on",
)

# WEAK markers are ordinary English that only signals an elision when it sits
# in a COMMENT. "TODO" inside a string literal may be a label; "// TODO" is a
# stub. "omitted" in help text is prose; "<!-- omitted -->" is a missing chunk.
PLACEHOLDER_MARKERS_WEAK = (
    "TODO",
    "FIXME",
    "OMITTED",
    "SAME AS ABOVE",
    "SAME AS BEFORE",
    "UNCHANGED",
    "ETC.",
    "SNIP",
    "TRUNCATED",
    "ELIDED",
)

# How a comment opens, per file type. Weak markers are only flagged inside one.
COMMENT_PATTERNS = {
    ".ts":   (r"//.*$", r"/\*.*?\*/"),
    ".tsx":  (r"//.*$", r"/\*.*?\*/"),
    ".js":   (r"//.*$", r"/\*.*?\*/"),
    ".mjs":  (r"//.*$", r"/\*.*?\*/"),
    ".cjs":  (r"//.*$", r"/\*.*?\*/"),
    ".css":  (r"/\*.*?\*/",),
    ".scss": (r"//.*$", r"/\*.*?\*/"),
    ".html": (r"<!--.*?-->",),
    ".env":  (r"#.*$",),
    ".yml":  (r"#.*$",),
    ".yaml": (r"#.*$",),
    # JSON has no comments, and Markdown is prose. Weak markers are not
    # meaningful in either, so only strong ones are checked there.
    ".json": (),
    ".md":   (),
}

# Files whose fenced content is markdown, and may therefore legitimately
# contain ``` inside it. Everything else closes at its FIRST closing fence,
# which is what stops a chatty model's trailing usage example from being
# appended into the source file it follows. See llm.parse_files.
MARKDOWN_FENCE_LANGUAGES = ("md", "markdown", "mdx")
MARKDOWN_SUFFIXES = (".md", ".markdown", ".mdx")


# Files an LLM must never be asked to write. A generated lockfile contains
# invented integrity hashes and makes `npm ci` fail; run `npm install` instead.
FORBIDDEN_OUTPUT_FILES = (
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
)


# ------------------------------------------------------------- toolchain ---
NODE_VERSION = "22.21.0"
ANGULAR_VERSION = "20.3.6"

# CommonJS is pinned deliberately. Node ESM requires explicit .js extensions on
# relative TypeScript imports ("./models/User.js" for a file named User.ts),
# which models get wrong constantly. CommonJS removes an entire class of
# generated-code failures for no practical cost in this application.
BACKEND_MODULE_SYSTEM = "commonjs"


def resolve_tool(name: str) -> str:
    """
    Find an executable across platforms.

    On Windows `npm` and `npx` are `npm.cmd` and `npx.cmd`; subprocess without
    shell=True will not find the extensionless name. Hardcoding the `.cmd`
    suffix instead — which the previous version did in two places out of three —
    fails everywhere else, and fails SILENTLY: FileNotFoundError becomes exit
    code 127, which the compile step reads as "the output format was not
    recognised" rather than "the command does not exist".

    That is exactly what happened to `ng build`: it used bare `npx` while the
    tsc step used `npx.cmd`, so on Windows the Angular TEMPLATE check never ran
    at all and the frontend was only ever type-checked as plain TypeScript.
    """
    found = shutil.which(name)
    if found:
        return found
    for candidate in (f"{name}.cmd", f"{name}.exe", f"{name}.bat"):
        found = shutil.which(candidate)
        if found:
            return found
    # Return the bare name so the failure is a clear "command not found: npm"
    # from compilers.run rather than an exception here at import time.
    return name


NPM = resolve_tool("npm")
NPX = resolve_tool("npx")
