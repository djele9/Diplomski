"""
prompts_backend.py — one prompt per backend stage.

Stages run in DEPENDENCY ORDER:

    scaffold -> models -> middlewares -> services -> controllers -> routers -> server

Each stage receives only the directories it depends on, not the whole tree.
"""

from __future__ import annotations

import config
import context

# The specification is loaded once by the pipeline and passed in, rather than
# being read at import time into a module-level global as the original did.


# ============================================================ shared =======
def _stack() -> str:
    return f"""\
## Technology, fixed — do not substitute

- Node.js {config.NODE_VERSION}
- Express 4.x
- TypeScript 5.x, compiled with `tsc`
- Mongoose 8.x
- Database MongoDB
- Module system: **{config.BACKEND_MODULE_SYSTEM}**

Because the project is CommonJS, relative imports carry **no file extension**:
write `import {{ User }} from '../models/user.model'`, never `'../models/user.model.js'`.
"""


def _output_contract(target_dir: str, manifest: str = "") -> str:
    block = f"""\
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
- One fenced block per file. No prose before the first `FILE:` line and none
  after the last closing fence.
"""
    if target_dir:
        block += f"\n- Every file in this stage belongs under `{target_dir}`.\n"
    if manifest:
        block += f"\n### Files to produce in this stage\n\n{manifest}\n"
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


def _error_contract() -> str:
    return """\
## Error and status-code contract

Use these consistently across every stage:

| Status | When |
|---|---|
| 200 | Successful read or update |
| 201 | Resource created |
| 400 | Malformed request, or a validation rule violated |
| 401 | No credentials, or bad, expired or revoked credentials |
| 403 | Authenticated, but not permitted to do this |
| 404 | No such resource, or not visible to this caller |
| 409 | The request contradicts current state (duplicate, conflict, wrong status) |
| 413 | Upload too large |
| 415 | Unsupported content type or file type |

Errors are thrown as a typed `AppError` (defined in the scaffold stage) and
turned into a response by the central error middleware. Controllers do not
build error responses by hand.

An error response body is:

```json
{ "status": 400, "message": "Human readable.", "fieldErrors": [{ "field": "email", "message": "..." }] }
```

`fieldErrors` is present only for validation failures. An error response never
contains a stack trace, a file path, a database error string, or a library
version.
"""


def _architecture() -> str:
    return """\
## Where code goes

```
backend/src/
  config/       environment loading, database connection
  types/        shared TypeScript types and enums
  models/       Mongoose schemas and models only
  middlewares/  authentication, authorization, validation, uploads, errors
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


def _self_check() -> str:
    return """\
## Before you answer, check each of these

1. Does every file I import actually exist, either in the context above or in
   this same answer? No import of a file nobody has written.
2. Do my imports match the exact export style of the file they import from —
   default vs named?
3. Have I written every file completely, with no elision anywhere?
4. Does every function have an explicit return type, and is `any` absent?
5. Does every rule the specification states appear somewhere in the code?
6. Are all reads and writes going through Mongoose?
7. Is every path in a `FILE:` line starting with `backend/`?
"""


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


# ========================================================= 1. scaffold ====
def scaffold(spec: str) -> str:
    manifest = """\
- `backend/package.json` — dependencies and scripts. **Do not produce
  `package-lock.json`**; it will be generated by `npm install`.
- `backend/tsconfig.json`
- `backend/.env.example` — every variable the application reads, with safe
  placeholder values and a comment for each
- `backend/.gitignore`
- `backend/src/config/env.ts` — read and validate environment variables once at
  start-up; throw a clear error naming any that are missing
- `backend/src/config/database.ts` — Mongoose connection with sensible options
  and connection-error logging
- `backend/src/types/index.ts` — shared enums and types drawn from the
  specification (roles, statuses, and so on), plus the authenticated-request type
- `backend/src/utils/AppError.ts` — the typed error class the error contract
  above describes, with helpers for each status code
- `backend/src/utils/password.ts` — hashing and verification
- `backend/src/utils/token.ts` — sign and verify JSON Web Tokens
"""

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

Read the specification and include only the dependencies it actually requires —
for example, add a JWT library and a hashing library only if the specification
describes authentication, and a file-upload library only if it describes uploads.
""",
        _architecture(),
        _error_contract(),
        _hard_rules(),
        _output_contract("backend/", manifest),
        _spec_block(spec),
        _self_check(),
    )


# =========================================================== 2. models ====
def models(spec: str) -> str:
    return _assemble(
        "# Task: generate the Mongoose models",
        "You are a senior backend engineer. You write complete, compiling, "
        "production-quality TypeScript. You answer with code and nothing else.",
        _stack(),
        """\
## This stage

One file per entity, in `backend/src/models/`, named `<entity>.model.ts`.

Derive the entities from the specification: every noun the scenarios create,
read, list, filter or constrain is a candidate. Read the `Background:` blocks
and the `Examples:` tables especially closely — they reveal the fields and
their shapes more precisely than the prose does.

For each model:

- A TypeScript interface for the document, exported.
- A Mongoose schema whose validation mirrors every constraint the
  specification states: required fields, min and max length, numeric bounds,
  enumerations, and regular-expression formats. If a scenario says a value has
  exactly eight digits, the schema enforces exactly eight digits.
- Indexes for every field the specification searches, sorts or requires to be
  unique. Compound and partial indexes where the rule is conditional.
- `{ timestamps: true }` unless the specification implies otherwise.
- Any field holding a secret must be `select: false`, so it is never returned
  by an ordinary query.
- A `toJSON` transform that removes `__v` and every secret field.

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
        _self_check(),
    )


# ====================================================== 3. middlewares ====
def middlewares(spec: str) -> str:
    manifest = """\
- `backend/src/middlewares/auth.middleware.ts` — verify the token, attach the
  authenticated user to the request
- `backend/src/middlewares/authorize.middleware.ts` — role and ownership checks
- `backend/src/middlewares/validate.middleware.ts` — request-body and query
  validation
- `backend/src/middlewares/error.middleware.ts` — the central error handler,
  plus a 404 handler for unmatched routes
- `backend/src/middlewares/upload.middleware.ts` — only if the specification
  describes file uploads
"""
    return _assemble(
        "# Task: generate the middlewares",
        "You are a senior backend engineer with a security focus. You answer "
        "with code and nothing else.",
        _stack(),
        """\
## This stage

Middlewares come **before** controllers on purpose: controllers will be
generated next and will import exactly what you define here, so the names,
signatures and request augmentation you choose are the contract.

Requirements:

- **Authentication** reads the token from the `Authorization: Bearer` header,
  verifies its signature and expiry, loads the user, and attaches it to the
  request using the authenticated-request type from `src/types`. A missing,
  malformed, expired or revoked token is 401.
- **Authorization** is a factory — `authorize('ROLE_A', 'ROLE_B')` — that
  returns a middleware. The role comes **only** from the verified token. A role
  in a header, a query parameter or a request body is ignored. Wrong role is
  403, never 401 and never 404.
- **Ownership** checks that the caller may act on the specific resource, not
  merely that their role is right. One user must not reach another user's
  resources; one organisation must not reach another's.
- **Validation** collects every field error rather than stopping at the first,
  and returns them in the `fieldErrors` shape from the error contract.
- **The error handler** is the only place that turns an error into a response.
  It maps `AppError` to its status, maps Mongoose validation and duplicate-key
  errors to 400 and 409 respectively, and maps everything unrecognised to a
  bare 500. It logs the full detail server-side and returns none of it.
- **Uploads**, if the specification has them, enforce type by inspecting file
  content rather than trusting the extension or the client's content type, and
  enforce the size and any dimension limits the specification states. A file
  name from the client never becomes a path.

The error middleware is registered last, after all routes. Say so in a comment.
""",
        _error_contract(),
        _hard_rules(),
        _output_contract("backend/src/middlewares/", manifest),
        _spec_block(spec),
        _code_block("Existing code — scaffold and models",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "config",
                                         config.BACKEND_DIR / "src" / "utils",
                                         config.BACKEND_DIR / "src" / "models")),
        _self_check(),
    )


# ========================================================= 4. services ====
def services(spec: str) -> str:
    return _assemble(
        "# Task: generate the service layer",
        "You are a senior backend engineer. Business rules are your "
        "responsibility and you implement them exactly. You answer with code "
        "and nothing else.",
        _stack(),
        """\
## This stage

One file per entity or feature area, in `backend/src/services/`, named
`<area>.service.ts`. **This is where every business rule lives.** The
controllers generated in the next stage will contain no rules at all, so any
rule you leave out here will be missing from the application.

Work through the specification scenario by scenario. For each one ask: what
does this require the system to refuse, and under what exact condition? Then
implement that condition.

Pay particular attention to:

- **Boundaries.** Where a rule names a number — a count, a length, a duration,
  a limit — implement the comparison exactly. "12 hours or more before" is
  `>=`, not `>`. Getting this wrong is the single most common defect in
  generated code, and the specification's `Examples:` tables usually state the
  boundary case explicitly.
- **Rules that span documents.** "At most N per parent", "unique within a
  parent", "this total may not exceed that count". A plain index cannot express
  these. Read the current state and write inside one MongoDB transaction
  (`session`), so two simultaneous requests cannot both pass the check.
- **Overlap and conflict.** Where the specification forbids two things
  occupying the same slot, implement the overlap test correctly: half-open
  intervals, so `[a,b)` and `[c,d)` overlap when `a < d && c < b`. Ranges that
  merely touch do not overlap.
- **State transitions.** Where an entity has a status, enforce which
  transitions are legal and reject the rest with 409.
- **Time.** Never call `new Date()` inside a rule. Accept the current time as a
  parameter with a default, so the rule can be unit-tested at a fixed instant.

Each service method throws `AppError` with the right status when a rule is
violated, and returns plain data on success. Services never touch `req` or
`res` and never import from `express`.
""",
        _architecture(),
        _error_contract(),
        _hard_rules(),
        _output_contract("backend/src/services/"),
        _spec_block(spec),
        _code_block("Existing code — scaffold, models and middlewares",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "config",
                                         config.BACKEND_DIR / "src" / "utils",
                                         config.BACKEND_DIR / "src" / "models",
                                         config.BACKEND_DIR / "src" / "middlewares")),
        _self_check(),
    )


# ====================================================== 5. controllers ====
def controllers(spec: str) -> str:
    return _assemble(
        "# Task: generate the controllers",
        "You are a senior backend engineer. You answer with code and nothing else.",
        _stack(),
        """\
## This stage

One file per feature area, in `backend/src/controllers/`, named
`<area>.controller.ts`, matching the services that already exist.

A controller handler does exactly four things:

1. Pull typed values out of `req` — params, query, body, the authenticated user.
2. Call **one** service method.
3. Send the result with the right status code.
4. Forward any thrown error to the error middleware.

It contains **no business rule**. No `if` that decides whether an action is
allowed, no limit comparison, no ownership test. Those already exist in the
services; call them.

Every handler is `async` and wrapped so that a rejected promise reaches the
error middleware rather than crashing the process — either `next(err)` in a
`catch`, or a shared `asyncHandler` wrapper (define it in `utils` and return
that file too if it does not already exist).

Never return a secret field. Shape the response to what the specification says
the client receives, and no more.
""",
        _architecture(),
        _error_contract(),
        _hard_rules(),
        _output_contract("backend/src/controllers/"),
        _spec_block(spec),
        _code_block("Existing code — models, middlewares and services",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "utils",
                                         config.BACKEND_DIR / "src" / "models",
                                         config.BACKEND_DIR / "src" / "middlewares",
                                         config.BACKEND_DIR / "src" / "services")),
        _self_check(),
    )


# ========================================================== 6. routers ====
def routers(spec: str) -> str:
    return _assemble(
        "# Task: generate the routers",
        "You are a senior backend engineer. You answer with code and nothing else.",
        _stack(),
        """\
## This stage

One file per feature area, in `backend/src/routers/`, named `<area>.routes.ts`.

Each file creates an `express.Router()`, wires paths to the middlewares and
controller handlers that already exist, and exports the router as the default
export.

Requirements:

- Import controllers and middlewares by their **real exported names**, taken
  from the existing code below. Do not invent a handler.
- Put the authentication and authorization middlewares on every route that the
  specification says is restricted, and on no route it says is public.
- Order routes so that a literal path is registered before a parameterised one
  that would also match it. `/items/search` must come before `/items/:id`, or
  the literal route is unreachable.
- Use REST-shaped paths consistent with the resource names already used in the
  models and controllers.
- Add a one-line comment above each route naming the scenario it serves.

At the top of each file, include a comment block listing every route the file
declares, as `METHOD /path`. The pipeline reads these to build the front end
against your real routes rather than guessed ones, so keep the list accurate.
""",
        _error_contract(),
        _hard_rules(),
        _output_contract("backend/src/routers/"),
        _spec_block(spec),
        _code_block("Existing code — middlewares and controllers",
                    context.collect_code(config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "middlewares",
                                         config.BACKEND_DIR / "src" / "controllers")),
        _self_check(),
    )


# =========================================================== 7. server ====
def server(spec: str) -> str:
    manifest = """\
- `backend/src/app.ts` — the Express application: middleware chain, router
  mounting, 404 handler, error handler
- `backend/src/server.ts` — the entry point: connect to MongoDB, run the
  bootstrap, start listening, handle shutdown signals
- `backend/src/seed/bootstrap.ts` — the initial-administrator bootstrap
  described below, only if the specification has an administrator role
- `backend/.env` — real local values matching `.env.example`
"""
    return _assemble(
        "# Task: generate the application entry point",
        "You are a senior backend engineer. You answer with code and nothing else.",
        _stack(),
        """\
## This stage

Wire everything that already exists into a running application.

`app.ts` assembles the middleware chain in this order, and the order matters:

1. security headers
2. CORS, configured from an environment variable, not `*`
3. body parsers with an explicit size limit
4. request logging
5. rate limiting on authentication routes, if the specification has them
6. static serving of the uploads directory, if the specification has uploads
7. all routers, mounted under their path prefixes
8. the 404 handler for unmatched routes
9. the error handler — **last**, after everything else

`server.ts` connects to MongoDB **before** listening, so the process fails
fast on a bad connection instead of accepting requests it cannot serve. It
handles `SIGINT` and `SIGTERM` by closing the server and the database
connection.

## Initial administrator

If — and only if — the specification describes an administrator role:

The application must have an administrator account available as soon as it
starts, and there must be **no public administrator registration route**.

At start-up, after connecting to MongoDB:

1. Check whether an administrator account already exists.
2. If none exists, create one from the environment variables
   `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
3. Hash the password with the same helper the rest of the application uses.
4. If an administrator already exists, change nothing — do not overwrite the
   account and do not reset its password.
5. Log which of the two happened.

The credentials are never hardcoded in source. Put them in `.env`:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin123!
```

and in `.env.example` with placeholder values. Refuse to start with a clear
error if they are absent while an administrator is required.
""",
        _hard_rules(),
        _output_contract("backend/", manifest),
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
        _self_check(),
    )
