"""
config.py — every setting in one place.

Nothing else in this package hardcodes a path, a model name or a generation
option. That matters for two reasons: you can point the pipeline at a different
application by changing FEATURES_DIR alone, and you can run the whole thing
across several models for the thesis comparison by changing MODEL.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------- paths -----
ROOT = Path(__file__).resolve().parent

# The specification. rglob is used, so subdirectories work — features/auth/*.feature
# as well as features/*.feature. The original glob('*.feature') silently found
# nothing when the suite was organised into folders.
FEATURES_DIR = ROOT / "features"

# Everything generated lands here. Model-emitted paths are relative to this, so
# a model writing "backend/src/models/User.ts" produces app/backend/src/models/User.ts
OUTPUT_DIR = ROOT / "app"
BACKEND_DIR = OUTPUT_DIR / "backend"
FRONTEND_DIR = OUTPUT_DIR / "frontend"

# Raw model responses, prompts and run metadata. Keeping these is what turns a
# code generator into an experiment you can write up.
RUNS_DIR = ROOT / "runs"


# --------------------------------------------------------------- model -----
MODEL = "nemotron-3-ultra:cloud"
OLLAMA_HOST = "http://localhost:11434"

# Generation options.
#
# num_ctx MUST be set explicitly. Ollama otherwise falls back to the model's
# default context — often 4096 — and silently discards everything past it.
# A prompt containing the whole specification plus the existing code is easily
# 50k+ tokens, so without this the model answers about a spec it never saw.
# This is the single most common cause of nonsense output.
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
    "num_ctx": 131072,
    "num_predict": 16000,
}

REQUEST_TIMEOUT_SECONDS = 1800


# ---------------------------------------------------------- generation -----
# How many characters of existing generated code a single prompt may carry.
# Roughly 3.7 characters per token, so 240k characters is about 65k tokens,
# leaving room for the specification and the answer inside a 128k window.
# Exceeding this raises rather than silently truncating.
CODE_CONTEXT_BUDGET_CHARS = 240_000

# How many times to feed compiler errors back and ask for corrections.
MAX_REPAIR_ROUNDS = 3

# Fail loudly when a model returns one of these instead of real code. The
# original prompts asked the model not to emit them but never checked.
PLACEHOLDER_MARKERS = (
    "TODO",
    "FIXME",
    "IMPLEMENT HERE",
    "IMPLEMENT THIS",
    "ADD YOUR CODE",
    "YOUR CODE HERE",
    "REST OF CODE",
    "REST OF FILE",
    "OMITTED",
    "OMITTED FOR BREVITY",
    "... rest of",
    "// ...",
    "/* ... */",
    "same as above",
    "unchanged",
)

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
