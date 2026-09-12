"""
prompts_backend.py — one prompt per backend stage, shaped by the domain.

Stages run in DEPENDENCY ORDER:

    scaffold -> models -> middlewares -> services -> controllers -> routers -> server

Each stage receives only the directories it depends on, not the whole tree.

## Why the prompts are assembled rather than written out

An earlier version of this file asked every specification for an authentication
middleware, an authorization middleware, a JWT helper, a password hasher and an
initial-administrator bootstrap. That is right for an application with accounts
and wrong for a public catalogue, a timetable, a calculator or a survey — and
the failure is not benign. Models comply: ask for a login system and you get
one, wired into an application nobody signs into, while the stage is scored as
having "failed" because it returned three files where the manifest listed six.

So the manifests here are data, computed from a `domain_profile.Profile` that was read
off the specification itself (see domain_profile.py). A domain with no accounts is
never asked for a guard; a domain with no uploads is never told about file-type
sniffing; a domain with no dates never reads the half-open-interval rule. The
prompt gets shorter and more accurate at the same time, which also means small
models spend their context on the domain rather than on advice about features it
does not have.

`expect_files` follows from the same manifest, so the pass mark for a stage is
the number of files that stage actually asked for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import config
import context
from domain_profile import Profile


# ======================================================= manifest model ====
@dataclass(frozen=True)
class Entry:
    path: str
    note: str
    required: bool = True


def render_manifest(entries: list[Entry]) -> str:
    lines = []
    for entry in entries:
        suffix = "" if entry.required else "  *(only if it makes sense here)*"
        lines.append(f"- `{entry.path}` — {entry.note}{suffix}")
    return "\n".join(lines)


def minimum(entries: list[Entry]) -> int:
    return sum(1 for entry in entries if entry.required)


# ============================================================ shared =======
def _stack() -> str:
    return f"""\
## Technology, fixed — do not substitute

- Node.js {config.NODE_VERSION}
- Express 4.x
- TypeScript >= 5.8.0 <= 6.0.0, compiled with `tsc`
- Mongoose 8.x
- Database MongoDB 8.2.1
- Module system: **{config.BACKEND_MODULE_SYSTEM}**

Because the project is CommonJS, relative imports carry **no file extension**:
write `import {{ User }} from '../models/user.model'`, never `'../models/user.model.js'`.
"""


def _output_contract(target_dir: str, entries: list[Entry] | None = None) -> str:
    block = """\
## Output contract

Return **only** files, each in exactly this form:

FILE: relative/path/to/file.ext

```language
COMPLETE FILE CONTENT
```

Rules for the path:

- It is relative to the project root, and **begins with `backend/`**.
- Example: `FILE: backend/src/models/user.model.ts`
- Do not prefix it with `app/`, `./` or an absolute path.

Rules for the content:

- The block holds the **entire file**, ready to compile. Not a diff, not a
  fragment, not an excerpt.
- **Exactly one fenced block per `FILE:` line.** The block closes with a single
  ``` and the next thing in your answer is either the next `FILE:` line or the
  end. Do not add a usage example, a shell command, an explanation or a summary
  after a file — a second fenced block under one `FILE:` line corrupts that
  file.
- No prose before the first `FILE:` line and none after the last closing fence.
"""
    if target_dir:
        block += f"\n- Every file in this stage belongs under `{target_dir}`.\n"
    if entries:
        block += f"\n### Files to produce in this stage\n\n{render_manifest(entries)}\n"
    return block


def _hard_rules() -> str:
    return """\
## Hard rules

**Completeness.** Every file is finished code. The following never appear in
your answer, in any form, including inside comments:

    TODO, FIXME, IMPLEMENT HERE, IMPLEMENT THIS, ADD YOUR CODE, YOUR CODE HERE,
    REST OF CODE, REST OF FILE, OMITTED, OMITTED FOR BREVITY, "... rest of",
    "same as above", "unchanged", "etc."

If a file is long, write it out in full anyway. A shortened file is a failed
answer, not a concise one.

**Persistence.** All data lives in MongoDB and is read and written through
Mongoose. No in-memory arrays standing in for collections, no hardcoded
fixtures, no JSON files used as storage, no seeded demo objects inside a
controller.

**TypeScript.** `strict` is on. No `any` — use a real type, a generic, or
`unknown` with a narrowing check. Every exported function has an explicit
return type. No `@ts-ignore`.

**Server-side truth.** Assume every request was crafted by hand rather than
sent by your own front end. A rule enforced only in the browser is not
enforced. Validate on the server, every time.

**No invention.** Use only the collections, fields, routes and rules that the
specification and the existing code establish. If the specification is silent
on something, choose the simplest behaviour consistent with it — do not invent
a new endpoint or entity.
"""


def _error_contract(prof: Profile) -> str:
    """
    The status codes this application can actually produce.

    Listing 401 and 403 for a specification with no accounts invites a model to
    invent an authentication scheme to justify them.
    """
    rows = [
        ("200", "Successful read or update"),
        ("201", "Resource created"),
        ("400", "Malformed request, or a validation rule violated"),
    ]
    if prof.authentication:
        rows.append(("401", "No credentials, or bad, expired or revoked credentials"))
    if prof.authorization:
        rows.append(("403", "Authenticated, but not permitted to do this"))
    rows.append(("404", "No such resource, or not visible to this caller"))
    rows.append(("409", "The request contradicts current state (duplicate, conflict, "
                        "wrong status)"))
    if prof.uploads:
        rows.append(("413", "Upload too large"))
        rows.append(("415", "Unsupported content type or file type"))

    table = "\n".join(f"| {code} | {when} |" for code, when in rows)
    return f"""\
## Error and status-code contract

Use these consistently across every stage, and use no others:

| Status | When |
|---|---|
{table}

Errors are thrown as a typed `AppError` (defined in the scaffold stage) and
turned into a response by the central error middleware. Controllers do not
build error responses by hand.

An error response body is:

```json
{{ "status": 400, "message": "Human readable.", "fieldErrors": [{{ "field": "email", "message": "..." }}] }}
```

`fieldErrors` is present only for validation failures. An error response never
contains a stack trace, a file path, a database error string, or a library
version.
"""


def _architecture(prof: Profile) -> str:
    middlewares = "validation, errors"
    if prof.authentication:
        middlewares = "authentication, " + middlewares
    if prof.authorization:
        middlewares = middlewares.replace("validation", "authorization, validation")
    if prof.uploads:
        middlewares += ", uploads"
    return f"""\
## Where code goes

```
backend/src/
  config/       environment loading, database connection
  types/        shared TypeScript types and enums
  models/       Mongoose schemas and models only
  middlewares/  {middlewares}
  services/     ALL business rules. Pure logic over the models.
  controllers/  HTTP only: read the request, call a service, send a response
  routers/      route tables wiring paths to middlewares and controllers
  utils/        small shared helpers
```

The division that matters: **a business rule lives in a service, never in a
controller**. A controller reads `req`, calls one service method, and maps the
result to a status code. It contains no `if` that expresses a domain rule.

This is not decoration. Rules in services can be unit-tested without HTTP;
rules inline in controllers cannot.
"""


def _self_check(prof: Profile) -> str:
    checks = [
        "Does every file I import actually exist, either in the context above or "
        "in this same answer? No import of a file nobody has written.",
        "Do my imports match the exact export style of the file they import from — "
        "default vs named?",
        "Have I written every file completely, with no elision anywhere?",
        "Does every function have an explicit return type, and is `any` absent?",
        "Does every rule the specification states appear somewhere in the code?",
        "Are all reads and writes going through Mongoose?",
    ]
    if prof.authorization:
        checks.append("Is every rule about who may do what enforced on the server, "
                      "not merely reflected in what the client is shown?")
    checks.append("Is every path in a `FILE:` line starting with `backend/`?")
    body = "\n".join(f"{i}. {text}" for i, text in enumerate(checks, start=1))
    return f"## Before you answer, check each of these\n\n{body}\n"


def _spec_block(spec: str) -> str:
    return f"""\
## The specification

What follows is every `.feature` file for this application. Each `===== name =====`
header begins a separate Gherkin file; they all describe the same system. They
are the complete and authoritative requirements.

================ BEGIN GHERKIN SPECIFICATION ================
{spec}
================= END GHERKIN SPECIFICATION =================
"""


def _code_block(title: str, body: str) -> str:
    if not body.strip():
        return ""
    return f"""\
## {title}

These files already exist. Import from them, match their exports exactly, and
do not restate them in your answer unless you are deliberately changing one —
in which case return the complete changed file.

================ BEGIN EXISTING CODE ================
{body}
================= END EXISTING CODE =================
"""


def _assemble(*sections: str) -> str:
    return "\n\n".join(s.strip() for s in sections if s and s.strip()) + "\n"


def _entity_floor(prof: Profile) -> int:
    """How many files a per-entity stage must produce at minimum."""
    return max(1, round(prof.entities_hint / 3))


# ========================================================= 1. scaffold ====
def scaffold_manifest(prof: Profile) -> list[Entry]:
    entries = [
        Entry("backend/package.json",
              "dependencies and scripts. **Do not produce `package-lock.json`**; "
              "it will be generated by `npm install`"),
        Entry("backend/tsconfig.json", "compiler settings"),
        Entry("backend/.env.example",
              "every variable the application reads, with safe placeholder values "
              "and a comment for each"),
        Entry("backend/.gitignore", "node_modules, dist, .env"),
        Entry("backend/src/config/env.ts",
              "read and validate environment variables once at start-up; throw a "
              "clear error naming any that are missing"),
        Entry("backend/src/config/database.ts",
              "Mongoose connection with sensible options and connection-error logging"),
        Entry("backend/src/types/index.ts",
              "shared enums and types drawn from the specification"),
        Entry("backend/src/utils/AppError.ts",
              "the typed error class the error contract above describes, with "
              "helpers for each status code"),
    ]
    if prof.authentication:
        entries.append(Entry("backend/src/utils/password.ts",
                             "hashing and verification"))
        entries.append(Entry("backend/src/utils/token.ts",
                             "sign and verify JSON Web Tokens"))
    if prof.money:
        entries.append(Entry("backend/src/utils/money.ts",
                             "integer-minor-unit arithmetic and formatting; see the "
                             "money rule below", required=False))
    return entries


def _dependency_guidance(prof: Profile) -> str:
    wanted = ["`express`, `mongoose`, `dotenv`, `cors`"]
    if prof.authentication:
        wanted.append("a JWT library and a password-hashing library")
    if prof.uploads:
        wanted.append("a multipart upload library and a file-type sniffer")
    if prof.email:
        wanted.append("an SMTP client")
    if prof.search:
        wanted.append("nothing extra — MongoDB queries are enough for filtering "
                      "and sorting")
    return ("Include exactly the dependencies this specification requires: "
            + "; ".join(wanted) + ". Add nothing else.")


def scaffold(spec: str, prof: Profile) -> str:
    return _assemble(
        "# Task: generate the backend scaffold",
        "You are a senior backend engineer. You write complete, compiling, "
        "production-quality TypeScript. You answer with code and nothing else.",
        _stack(),
        f"""\
## This stage

This is the **first** stage. It fixes the decisions every later stage depends
on: the module system, the compiler settings, the shared types, and the error
class. Later stages will be given these files and must conform to them, so be
deliberate.

`tsconfig.json` must set at minimum:

```json
{{
  "target": "ES2022",
  "module": "{config.BACKEND_MODULE_SYSTEM}",
  "moduleResolution": "node",
  "strict": true,
  "esModuleInterop": true,
  "skipLibCheck": true,
  "forceConsistentCasingInFileNames": true,
  "outDir": "./dist",
  "rootDir": "./src",
  "resolveJsonModule": true
}}
```

`package.json` must include `typescript`, `@types/node`, `@types/express`, and
`@types/` packages for every dependency that needs them. Scripts: `build`
(`tsc`), `start` (`node dist/server.js`), `dev`.

{_dependency_guidance(prof)}
""",
        _architecture(prof),
        _error_contract(prof),
        _hard_rules(),
        _output_contract("backend/", scaffold_manifest(prof)),
        _spec_block(spec),
        _self_check(prof),
    )


# =========================================================== 2. models ====
def _model_rules(prof: Profile) -> str:
    rules = [
        "A TypeScript interface for the document, exported.",
        "A Mongoose schema whose validation mirrors every constraint the "
        "specification states: required fields, min and max length, numeric "
        "bounds, enumerations, and regular-expression formats. If a scenario "
        "says a value has exactly eight digits, the schema enforces exactly "
        "eight digits.",
        "Indexes for every field the specification searches, sorts or requires "
        "to be unique. Compound and partial indexes where the rule is "
        "conditional.",
        "`{ timestamps: true }` unless the specification implies otherwise.",
    ]
    if prof.authentication:
        rules.append("Any field holding a secret must be `select: false`, so it is "
                     "never returned by an ordinary query.")
        rules.append("A `toJSON` transform that removes `__v` and every secret field.")
    else:
        rules.append("A `toJSON` transform that removes `__v`.")
    if prof.state_machine:
        rules.append("Where the specification gives something a status, the field is "
                     "an enumeration of exactly the states it names — not a free "
                     "string.")
    if prof.money:
        rules.append("Money is stored as an integer number of minor units (cents), "
                     "never as a floating-point number. Name the field so that is "
                     "obvious.")
    if prof.scheduling:
        rules.append("Instants are stored as `Date`. A period is stored as its start "
                     "and its end, not as a start and a duration, because the "
                     "overlap rules are expressed on intervals.")
    return "\n".join(f"- {rule}" for rule in rules)


def models(spec: str, prof: Profile) -> str:
    return _assemble(
        "# Task: generate the Mongoose models",
        "You are a senior backend engineer. You write complete, compiling, "
        "production-quality TypeScript. You answer with code and nothing else.",
        _stack(),
        f"""\
## This stage

One file per entity, in `backend/src/models/`, named `<entity>.model.ts`.

Derive the entities from the specification: every noun the scenarios create,
read, list, filter or constrain is a candidate. Read the `Background:` blocks
and the `Examples:` tables especially closely — they reveal the fields and
their shapes more precisely than the prose does.

For each model:

{_model_rules(prof)}

**Uniqueness that spans documents** — "at most N of X per Y", "this name is
unique within that parent" — cannot be expressed as a plain unique index.
Add a comment on the schema naming the rule and saying that the service layer
enforces it inside a transaction. Do not silently omit it.

Export both the interface and the model from each file.
""",
        _hard_rules(),
        _output_contract("backend/src/models/"),
        _spec_block(spec),
        _code_block("Existing code — scaffold",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "config",
                                         config.BACKEND_DIR / "src" / "utils")),
        _self_check(prof),
    )


# ====================================================== 3. middlewares ====
def middlewares_manifest(prof: Profile) -> list[Entry]:
    entries: list[Entry] = []
    if prof.authentication:
        entries.append(Entry("backend/src/middlewares/auth.middleware.ts",
                             "verify the token, attach the authenticated user to "
                             "the request"))
    if prof.authorization:
        entries.append(Entry("backend/src/middlewares/authorize.middleware.ts",
                             "role and ownership checks"))
    entries.append(Entry("backend/src/middlewares/validate.middleware.ts",
                         "request-body and query validation"))
    entries.append(Entry("backend/src/middlewares/error.middleware.ts",
                         "the central error handler, plus a 404 handler for "
                         "unmatched routes"))
    if prof.uploads:
        entries.append(Entry("backend/src/middlewares/upload.middleware.ts",
                             "multipart handling with type and size limits"))
    return entries


def _middleware_rules(prof: Profile) -> str:
    rules = []
    if prof.authentication:
        rules.append(
            "**Authentication** reads the token from the `Authorization: Bearer` "
            "header, verifies its signature and expiry, loads the user, and "
            "attaches it to the request using the authenticated-request type from "
            "`src/types`. A missing, malformed, expired or revoked token is 401.")
    if prof.roles:
        rules.append(
            "**Authorization** is a factory — `authorize('ROLE_A', 'ROLE_B')` — "
            "that returns a middleware. The role comes **only** from the verified "
            "token. A role in a header, a query parameter or a request body is "
            "ignored. Wrong role is 403, never 401 and never 404.")
    if prof.authorization:
        rules.append(
            "**Ownership** checks that the caller may act on the specific "
            "resource, not merely that their role is right. One user must not "
            "reach another user's resources.")
    rules.append(
        "**Validation** collects every field error rather than stopping at the "
        "first, and returns them in the `fieldErrors` shape from the error "
        "contract.")
    rules.append(
        "**The error handler** is the only place that turns an error into a "
        "response. It maps `AppError` to its status, maps Mongoose validation and "
        "duplicate-key errors to 400 and 409 respectively, and maps everything "
        "unrecognised to a bare 500. It logs the full detail server-side and "
        "returns none of it.")
    if prof.uploads:
        rules.append(
            "**Uploads** enforce type by inspecting file content rather than "
            "trusting the extension or the client's content type, and enforce the "
            "size and any dimension limits the specification states. A file name "
            "from the client never becomes a path.")
    return "\n".join(f"- {rule}\n" for rule in rules)


def middlewares(spec: str, prof: Profile) -> str:
    return _assemble(
        "# Task: generate the middlewares",
        "You are a senior backend engineer with a security focus. You answer "
        "with code and nothing else.",
        _stack(),
        f"""\
## This stage

Middlewares come **before** controllers on purpose: controllers will be
generated next and will import exactly what you define here, so the names,
signatures and request augmentation you choose are the contract.

Requirements:

{_middleware_rules(prof)}
The error middleware is registered last, after all routes. Say so in a comment.
""",
        _error_contract(prof),
        _hard_rules(),
        _output_contract("backend/src/middlewares/", middlewares_manifest(prof)),
        _spec_block(spec),
        _code_block("Existing code — scaffold and models",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "config",
                                         config.BACKEND_DIR / "src" / "utils",
                                         config.BACKEND_DIR / "src" / "models")),
        _self_check(prof),
    )


# ========================================================= 4. services ====
def _service_rules(prof: Profile) -> str:
    """
    Only the rules this domain can actually break.

    The half-open-interval rule is essential advice for a booking system and
    noise for a catalogue. Noise is not free: it is context a small model spends
    instead of spending it on the specification.
    """
    rules = [
        ("**Boundaries.** Where a rule names a number — a count, a length, a "
         "duration, a limit — implement the comparison exactly. \"12 or more\" is "
         "`>=`, not `>`. Getting this wrong is the single most common defect in "
         "generated code, and the specification's `Examples:` tables usually "
         "state the boundary case explicitly."),
        ("**Rules that span documents.** \"At most N per parent\", \"unique "
         "within a parent\", \"this total may not exceed that count\". A plain "
         "index cannot express these. Read the current state and write inside "
         "one MongoDB transaction (`session`), so two simultaneous requests "
         "cannot both pass the check."),
    ]
    if prof.scheduling:
        rules.append(
            "**Overlap and conflict.** Where the specification forbids two things "
            "occupying the same slot, implement the overlap test correctly: "
            "half-open intervals, so `[a,b)` and `[c,d)` overlap when "
            "`a < d && c < b`. Ranges that merely touch do not overlap.")
        rules.append(
            "**Time.** Never call `new Date()` inside a rule. Accept the current "
            "time as a parameter with a default, so the rule can be unit-tested "
            "at a fixed instant.")
    if prof.state_machine:
        rules.append(
            "**State transitions.** Where an entity has a status, enforce which "
            "transitions are legal and reject the rest with 409.")
    if prof.money:
        rules.append(
            "**Money.** Arithmetic happens in integer minor units. Never sum "
            "floating-point currency, and round only at the final presentation "
            "step, using the rule the specification states.")
    if prof.search:
        rules.append(
            "**Searching and sorting.** Build the query from exactly the filters "
            "the caller supplied — an absent filter is not a filter matching "
            "everything written out, it is an absent clause. Sort only on the "
            "fields the specification names, rejecting anything else rather than "
            "passing it to the database.")
    if prof.import_export:
        rules.append(
            "**Bulk input.** Validate every entry before writing any of them, and "
            "write them in one transaction, so a file with one bad entry changes "
            "nothing. Report which entry and which field failed.")
    if prof.email:
        rules.append(
            "**Messages out.** Sending is a side effect at the edge of a rule, "
            "not part of it: the rule decides, then the message is sent. A "
            "failure to send never rolls back a decision that was correctly made, "
            "and never leaks whether an address is known.")
    return "\n\n".join(f"- {rule}" for rule in rules)


def services(spec: str, prof: Profile) -> str:
    return _assemble(
        "# Task: generate the service layer",
        "You are a senior backend engineer. Business rules are your "
        "responsibility and you implement them exactly. You answer with code "
        "and nothing else.",
        _stack(),
        f"""\
## This stage

One file per entity or feature area, in `backend/src/services/`, named
`<area>.service.ts`. **This is where every business rule lives.** The
controllers generated in the next stage will contain no rules at all, so any
rule you leave out here will be missing from the application.

Work through the specification scenario by scenario. For each one ask: what
does this require the system to refuse, and under what exact condition? Then
implement that condition. The `@negative` scenarios are the specification's own
list of what must be refused — none of them may be unimplemented.

Pay particular attention to:

{_service_rules(prof)}

Each service method throws `AppError` with the right status when a rule is
violated, and returns plain data on success. Services never touch `req` or
`res` and never import from `express`.
""",
        _architecture(prof),
        _error_contract(prof),
        _hard_rules(),
        _output_contract("backend/src/services/"),
        _spec_block(spec),
        _code_block("Existing code — scaffold, models and middlewares",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "config",
                                         config.BACKEND_DIR / "src" / "utils",
                                         config.BACKEND_DIR / "src" / "models",
                                         config.BACKEND_DIR / "src" / "middlewares")),
        _self_check(prof),
    )


# ====================================================== 5. controllers ====
def controllers(spec: str, prof: Profile) -> str:
    secrets = ("\nNever return a secret field. Shape the response to what the "
               "specification says the client receives, and no more.\n"
               if prof.authentication else
               "\nShape the response to what the specification says the client "
               "receives, and no more.\n")
    return _assemble(
        "# Task: generate the controllers",
        "You are a senior backend engineer. You answer with code and nothing else.",
        _stack(),
        f"""\
## This stage

One file per feature area, in `backend/src/controllers/`, named
`<area>.controller.ts`, matching the services that already exist.

A controller handler does exactly four things:

1. Pull typed values out of `req` — params, query, body{", the authenticated user"
   if prof.authentication else ""}.
2. Call **one** service method.
3. Send the result with the right status code.
4. Forward any thrown error to the error middleware.

It contains **no business rule**. No `if` that decides whether an action is
allowed, no limit comparison{", no ownership test" if prof.authorization else ""}.
Those already exist in the services; call them.

Every handler is `async` and wrapped so that a rejected promise reaches the
error middleware rather than crashing the process — either `next(err)` in a
`catch`, or a shared `asyncHandler` wrapper (define it in `utils` and return
that file too if it does not already exist).
{secrets}""",
        _architecture(prof),
        _error_contract(prof),
        _hard_rules(),
        _output_contract("backend/src/controllers/"),
        _spec_block(spec),
        _code_block("Existing code — models, middlewares and services",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "utils",
                                         config.BACKEND_DIR / "src" / "models",
                                         config.BACKEND_DIR / "src" / "middlewares",
                                         config.BACKEND_DIR / "src" / "services")),
        _self_check(prof),
    )


# ========================================================== 6. routers ====
def routers(spec: str, prof: Profile) -> str:
    # When the domain has no accounts, say nothing about them at all.
    #
    # The tempting alternative — "do not add an authentication middleware" — is
    # worse than silence. It puts the idea in front of the model, and a small
    # model asked not to think of a login screen will frequently produce one.
    # Describing only what the application is makes the omission natural rather
    # than forbidden.
    guard_rule = (
        "- Put the authentication and authorization middlewares on every route "
        "that the specification says is restricted, and on no route it says is "
        "public.\n" if prof.authentication else
        "- Every route in this application is reachable by anyone. Wire each one "
        "to its validation middleware and its controller handler, and to nothing "
        "else.\n")
    return _assemble(
        "# Task: generate the routers",
        "You are a senior backend engineer. You answer with code and nothing else.",
        _stack(),
        f"""\
## This stage

One file per feature area, in `backend/src/routers/`, named `<area>.routes.ts`.

Each file creates an `express.Router()`, wires paths to the middlewares and
controller handlers that already exist, and exports the router as the default
export.

Requirements:

- **Name the router variable exactly `router`**, declared as
  `const router = express.Router();`, and register each route as
  `router.get('/path', ...)`. Do not use `router.route('/path').get(...)`, and
  do not name the variable after the area (`authRouter`, `itemRouter`). The
  pipeline reads these declarations to build the front end against your real
  routes; a different shape means the front end is built against guesses.
- Import controllers and middlewares by their **real exported names**, taken
  from the existing code below. Do not invent a handler.
{guard_rule}- Order routes so that a literal path is registered before a parameterised one
  that would also match it. `/items/search` must come before `/items/:id`, or
  the literal route is unreachable.
- Use REST-shaped paths consistent with the resource names already used in the
  models and controllers.
- Add a one-line comment above each route naming the scenario it serves.

At the top of each file, include a comment block listing every route the file
declares, as `METHOD /path`.
""",
        _error_contract(prof),
        _hard_rules(),
        _output_contract("backend/src/routers/"),
        _spec_block(spec),
        _code_block("Existing code — middlewares and controllers",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "middlewares",
                                         config.BACKEND_DIR / "src" / "controllers")),
        _self_check(prof),
    )


# =========================================================== 7. server ====
def server_manifest(prof: Profile) -> list[Entry]:
    entries = [
        Entry("backend/src/app.ts",
              "the Express application: middleware chain, router mounting, "
              "404 handler, error handler"),
        Entry("backend/src/server.ts",
              "the entry point: connect to MongoDB, start listening, handle "
              "shutdown signals"),
        Entry("backend/.env", "real local values matching `.env.example`"),
    ]
    if prof.roles:
        entries.append(Entry("backend/src/seed/bootstrap.ts",
                             "the privileged-account bootstrap described below"))
    return entries


def _chain(prof: Profile) -> str:
    steps = ["security headers",
             "CORS, configured from an environment variable, not `*`",
             "body parsers with an explicit size limit",
             "request logging"]
    if prof.authentication:
        steps.append("rate limiting on the authentication routes")
    if prof.uploads:
        steps.append("static serving of the uploads directory")
    steps += ["all routers, mounted under their path prefixes",
              "the 404 handler for unmatched routes",
              "the error handler — **last**, after everything else"]
    return "\n".join(f"{i}. {text}" for i, text in enumerate(steps, start=1))


def _bootstrap(prof: Profile) -> str:
    if not prof.roles:
        return ""
    return """\
## The privileged account

The specification describes a privileged role. Such an account must exist as
soon as the application starts, and there must be **no public registration
route** that grants that role.

At start-up, after connecting to MongoDB:

1. Check whether such an account already exists.
2. If none exists, create one from environment variables.
3. Hash the password with the same helper the rest of the application uses.
4. If one already exists, change nothing — do not overwrite the account and do
   not reset its password.
5. Log which of the two happened.

The credentials are never hardcoded in source. Put them in `.env` and in
`.env.example` with placeholder values, and refuse to start with a clear error
if they are absent.
"""


def server(spec: str, prof: Profile) -> str:
    return _assemble(
        "# Task: generate the application entry point",
        "You are a senior backend engineer. You answer with code and nothing else.",
        _stack(),
        f"""\
## This stage

Wire everything that already exists into a running application.

`app.ts` assembles the middleware chain in this order, and the order matters:

{_chain(prof)}

`server.ts` connects to MongoDB **before** listening, so the process fails
fast on a bad connection instead of accepting requests it cannot serve. It
handles `SIGINT` and `SIGTERM` by closing the server and the database
connection.
""",
        _bootstrap(prof),
        _hard_rules(),
        _output_contract("backend/", server_manifest(prof)),
        _spec_block(spec),
        _code_block("Existing code — middlewares, routers and models",
                    context.collect_code(config.BACKEND_DIR / "src" / "config",
                                         config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "utils",
                                         config.BACKEND_DIR / "src" / "models",
                                         config.BACKEND_DIR / "src" / "middlewares",
                                         config.BACKEND_DIR / "src" / "routers")),
        f"""\
## Files already on disk

```
{context.describe_tree(config.BACKEND_DIR)}
```
""",
        _self_check(prof),
    )


# ============================================================= stages ======
@dataclass(frozen=True)
class Stage:
    name: str
    build: Callable[[str, Profile], str]
    minimum: Callable[[Profile], int]


STAGES: list[Stage] = [
    Stage("backend-1-scaffold",    scaffold,
          lambda p: minimum(scaffold_manifest(p))),
    Stage("backend-2-models",      models,      _entity_floor),
    Stage("backend-3-middlewares", middlewares,
          lambda p: minimum(middlewares_manifest(p))),
    Stage("backend-4-services",    services,    _entity_floor),
    Stage("backend-5-controllers", controllers, _entity_floor),
    Stage("backend-6-routers",     routers,     _entity_floor),
    Stage("backend-7-server",      server,
          lambda p: minimum(server_manifest(p))),
]
