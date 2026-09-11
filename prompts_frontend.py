"""
prompts_frontend.py — one prompt per front-end stage.

Stages run in DEPENDENCY ORDER:

    scaffold -> models -> services -> guards -> components -> app

Two changes matter most compared with the original prompts.

First, every front-end stage is given the **real HTTP surface** extracted from
the generated routers. Without it the front end infers URLs from the Gherkin
and infers them differently from how the backend did, so everything compiles
and every request 404s.

Second, the prompts require Angular's built-in control flow (`@if`, `@for`)
rather than the structural directives. `*ngIf` and `*ngFor` need `CommonModule`
in a standalone component's `imports`, and models forget that constantly —
which is a compile error every time. The built-in syntax needs no import at
all, so an entire class of generated-code failure disappears.
"""

from __future__ import annotations

import config
import context

FRONTEND_SRC = config.FRONTEND_DIR / "src"


# ============================================================ shared =======
def _stack() -> str:
    return f"""\
## Technology, fixed — do not substitute

- Angular {config.ANGULAR_VERSION}
- TypeScript, HTML, CSS
- Bootstrap 5 and Bootstrap Icons
- **Standalone components only.** There is no `NgModule` anywhere in this
  project — not `AppModule`, not a feature module, not `SharedModule`.

### Angular 20 idioms that are required here

| Use | Not |
|---|---|
| `@if`, `@for`, `@switch`, `@empty` in templates | `*ngIf`, `*ngFor`, `*ngSwitch` |
| `inject(Service)` | constructor parameter injection |
| `signal()`, `computed()`, `effect()` for component state | mutable public fields |
| `input()` and `output()` functions | `@Input()` and `@Output()` decorators |
| Functional guards: `export const x: CanActivateFn = ...` | class guards implementing `CanActivate` |
| Functional interceptors: `HttpInterceptorFn` | class interceptors with `HTTP_INTERCEPTORS` |
| `provideHttpClient()`, `provideRouter()` in `app.config.ts` | `HttpClientModule`, `RouterModule.forRoot()` |
| `loadComponent` / `loadChildren` for routes | eager imports of every page |

The control-flow point is not stylistic. `*ngIf` requires `CommonModule` in a
standalone component's `imports` array; `@if` requires nothing. Using the
built-in syntax removes a whole class of compile errors.

Templates and styles live in separate files — `templateUrl` and `styleUrl`,
never inline `template:` or `styles:`.
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

- It is relative to the project root, and **begins with `frontend/`**.
- Example: `FILE: frontend/src/app/services/auth.service.ts`
- Do not prefix it with `app/`, `./` or an absolute path.

Rules for the content:

- The block holds the **entire file**, ready to compile. Not a diff, not a
  fragment, not an excerpt.
- A component means three files — `.ts`, `.html`, `.css` — each returned in
  full, each with its own `FILE:` line.
- No prose before the first `FILE:` line and none after the last closing fence.
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
your answer, in any form, including inside comments and inside templates:

    TODO, FIXME, IMPLEMENT HERE, IMPLEMENT THIS, ADD YOUR CODE, YOUR CODE HERE,
    REST OF CODE, REST OF FILE, OMITTED, OMITTED FOR BREVITY, "... rest of",
    "same as above", "unchanged", "etc."

If a template is long, write it out in full anyway.

**No fabricated data.** Every value shown to the user comes from the backend
API over HTTP. No hardcoded arrays of demo rows, no mock service, no local JSON
file standing in for a request, no `of([...])` returning invented objects.
An empty list before the request resolves is correct; a list of invented
objects is not.

**TypeScript.** `strict` is on. No `any` — use a real type or `unknown` with
narrowing. Every service method has an explicit return type. No `@ts-ignore`.

**Only real endpoints.** Call only the routes listed in the HTTP surface
section. If something the specification describes has no route there, leave a
comment saying so rather than inventing a URL.

**Accessibility and markup.** Labels are associated with their inputs, buttons
have discernible text, and Bootstrap classes are used as Bootstrap intends.
"""


def _api_surface() -> str:
    return f"""\
## The backend HTTP surface — the only routes that exist

These were extracted from the generated backend routers. They are the real
endpoints. Call these exact methods and paths; do not invent, rename or guess.

```
{context.extract_api_surface()}
```

Where a path contains `:param`, substitute the value in the front-end service.
"""


def _spec_block(spec: str) -> str:
    return f"""\
## The specification

What follows is every `.feature` file for this application. Each `===== name =====`
header begins a separate Gherkin file; they all describe the same system. They
are the complete and authoritative requirements, including everything the user
interface must do.

Read the `@ui` scenarios especially closely: they describe what must be on
screen, what is enabled and disabled, what is sorted, and what messages appear.

================ BEGIN GHERKIN SPECIFICATION ================
{spec}
================= END GHERKIN SPECIFICATION =================
"""


def _code_block(title: str, body: str) -> str:
    if not body.strip():
        return ""
    return f"""\
## {title}

These files already exist. Import from them and match their exports exactly.
Do not restate them unless you are deliberately changing one, in which case
return the complete changed file.

================ BEGIN EXISTING CODE ================
{body}
================= END EXISTING CODE =================
"""


def _self_check() -> str:
    return """\
## Before you answer, check each of these

1. Does every file I import exist, either in the context above or in this same
   answer?
2. Does every component I reference appear in the importing component's
   `imports` array?
3. Have I used `@if` and `@for` rather than `*ngIf` and `*ngFor`?
4. Does every component have all three of its files, each complete?
5. Does every HTTP call use a route from the HTTP surface section, verbatim?
6. Is `any` absent, and does every service method declare its return type?
7. Is every path in a `FILE:` line starting with `frontend/`?
"""


def _assemble(*sections: str) -> str:
    return "\n\n".join(s.strip() for s in sections if s and s.strip()) + "\n"


# ========================================================= 1. scaffold ====
def scaffold(spec: str) -> str:
    manifest = """\
- `frontend/package.json` — **do not produce `package-lock.json`**; it will be
  generated by `npm install`
- `frontend/angular.json` — with Bootstrap's CSS and Bootstrap Icons' CSS in
  the `styles` array, and Bootstrap's JS bundle in `scripts`
- `frontend/tsconfig.json`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.spec.json`
- `frontend/.gitignore`
- `frontend/src/index.html`
- `frontend/src/main.ts`
- `frontend/src/styles.css` — global styles and any Bootstrap overrides
- `frontend/src/environments/environment.ts` — `apiUrl` for development
- `frontend/src/environments/environment.production.ts`
"""
    return _assemble(
        "# Task: generate the Angular project scaffold",
        "You are a senior Angular engineer. You write complete, compiling, "
        "production-quality code. You answer with code and nothing else.",
        _stack(),
        f"""\
## This stage

This is the **first** front-end stage. It fixes the compiler settings and the
build configuration that every later stage depends on, so be deliberate.

`tsconfig.json` must set `"strict": true`, `"noImplicitOverride": true`,
`"noPropertyAccessFromIndexSignature": true`, `"noImplicitReturns": true` and
Angular's `strictTemplates` under `angularCompilerOptions`.

`angular.json` must use the `@angular/build:application` builder, and must
reference Bootstrap and Bootstrap Icons from `node_modules`, not from a CDN.

`environment.ts` exports an object with `apiUrl` pointing at the backend —
`http://localhost:3000/api` unless the backend configuration below says
otherwise. Every service will read the base URL from here, so no component
ever contains a literal URL.

`package.json` pins Angular {config.ANGULAR_VERSION} and includes `bootstrap`
and `bootstrap-icons`. Do not add a state-management library, a component
library, or anything else the specification does not require.

`main.ts` uses `bootstrapApplication(App, appConfig)`. `App` and `appConfig`
are generated in the final stage; import them from `./app/app` and
`./app/app.config` so the reference resolves once that stage runs.
""",
        _hard_rules(),
        _output_contract("frontend/", manifest),
        _spec_block(spec),
        _code_block("Backend configuration — for the API base URL and CORS origin",
                    context.collect_code(config.BACKEND_DIR / "src" / "config")),
        _self_check(),
    )


# =========================================================== 2. models ====
def models(spec: str) -> str:
    return _assemble(
        "# Task: generate the front-end models",
        "You are a senior Angular engineer. You answer with code and nothing else.",
        _stack(),
        """\
## This stage

TypeScript interfaces and enums in `frontend/src/app/models/`, one file per
entity, named `<entity>.model.ts`.

These describe the JSON the backend actually sends and receives. Derive them
from the **backend models and controllers** shown below, not from guesswork:

- Field names must match the backend's `toJSON` output exactly, including
  whether the identifier is `id` or `_id`.
- A field the backend removes before sending — a password hash, an internal
  flag — must not appear here at all.
- Dates arrive as ISO strings over HTTP. Type them as `string`, and convert to
  `Date` in the component if you need to.
- Where the backend uses an enumeration, declare the same enumeration here with
  the same string values.

Also declare the request and response shapes the API uses: the body each POST
and PUT sends, and the envelope each list endpoint returns, including the error
shape `{ status, message, fieldErrors? }`.

No classes, no decorators — interfaces, type aliases and enums only.
""",
        _hard_rules(),
        _output_contract("frontend/src/app/models/"),
        _spec_block(spec),
        _api_surface(),
        _code_block("Backend models, types and controllers — the source of truth for these shapes",
                    context.collect_code(config.BACKEND_DIR / "src" / "models",
                                         config.BACKEND_DIR / "src" / "types",
                                         config.BACKEND_DIR / "src" / "controllers")),
        _self_check(),
    )


# ========================================================= 3. services ====
def services(spec: str) -> str:
    return _assemble(
        "# Task: generate the front-end services",
        "You are a senior Angular engineer. You answer with code and nothing else.",
        _stack(),
        """\
## This stage

Injectable services in `frontend/src/app/services/`, one per feature area,
named `<area>.service.ts`, each `@Injectable({ providedIn: 'root' })`.

Requirements:

- Inject `HttpClient` with `inject(HttpClient)`, not through a constructor.
- Build every URL from `environment.apiUrl`. No literal `http://` anywhere.
- Every method returns a typed `Observable<T>` using the interfaces from the
  models stage. Explicit return type on every method.
- Query parameters go through `HttpParams`, never string concatenation, so
  values are encoded correctly.
- An authentication service, if the specification has authentication, holds the
  current user in a `signal` and exposes it as a readonly signal. It persists
  the token, restores it on start-up, and clears it on sign-out. It exposes
  `isAuthenticated` and a role check as `computed` signals, so guards and
  templates read the same source.
- Do not catch errors here and turn them into empty results. Let them
  propagate; the interceptor and the components handle them. Swallowing an
  error is how a broken screen looks like an empty one.

Call only the routes in the HTTP surface section, exactly as written.
""",
        _hard_rules(),
        _output_contract("frontend/src/app/services/"),
        _api_surface(),
        _spec_block(spec),
        _code_block("Front-end models and scaffold",
                    context.collect_code(FRONTEND_SRC / "app" / "models",
                                         FRONTEND_SRC / "environments")),
        _self_check(),
    )


# =========================================== 4. guards and interceptors ===
def guards(spec: str) -> str:
    manifest = """\
- `frontend/src/app/guards/auth.guard.ts` — a `CanActivateFn` that redirects an
  unauthenticated visitor to the sign-in route
- `frontend/src/app/guards/role.guard.ts` — a `CanActivateFn` factory taking the
  allowed roles from the route's `data`
- `frontend/src/app/guards/guest.guard.ts` — keeps a signed-in user off the
  sign-in and registration routes
- `frontend/src/app/interceptors/auth.interceptor.ts` — an `HttpInterceptorFn`
  that attaches the bearer token
- `frontend/src/app/interceptors/error.interceptor.ts` — an `HttpInterceptorFn`
  that signs the user out on 401 and surfaces a readable message otherwise
"""
    return _assemble(
        "# Task: generate the guards and HTTP interceptors",
        "You are a senior Angular engineer with a security focus. You answer "
        "with code and nothing else.",
        _stack(),
        """\
## This stage

All guards are **functional** — `export const authGuard: CanActivateFn = (route, state) => ...`
using `inject()` inside the function body. No classes implementing `CanActivate`.
All interceptors are **functional** — `HttpInterceptorFn` — registered later
through `provideHttpClient(withInterceptors([...]))`.

Requirements:

- A guard that blocks navigation returns a `UrlTree` from `Router.createUrlTree`
  rather than calling `navigate` and returning `false`. That is what makes the
  redirect atomic.
- The auth guard preserves the attempted URL as a `returnUrl` query parameter,
  so the user lands where they were going after signing in.
- The role guard reads its allowed roles from `route.data['roles']`, so one
  guard serves every restricted route.
- The auth interceptor attaches the token only to requests aimed at
  `environment.apiUrl`. It must not attach it to third-party requests.
- The error interceptor treats 401 as "the session is gone": clear it and send
  the user to sign in. It must not do that for 403, which means the session is
  valid but the action is not permitted.

**State this clearly in a comment at the top of the guard file:** guards are a
convenience for the user, not a security boundary. Anyone can edit the bundle.
The server is what enforces access, and the specification's authorization
scenarios test the server independently of anything the browser does.
""",
        _hard_rules(),
        _output_contract("frontend/src/app/", manifest),
        _spec_block(spec),
        _code_block("Front-end services and models",
                    context.collect_code(FRONTEND_SRC / "app" / "services",
                                         FRONTEND_SRC / "app" / "models",
                                         FRONTEND_SRC / "environments")),
        _self_check(),
    )


# ======================================================= 5. components ====
def components(spec: str, area: str = "", areas_done: str = "") -> str:
    """
    `area` narrows the stage to one feature area.

    Generating every screen in one response is the most common cause of
    truncation in this pipeline: the answer is simply longer than the model can
    emit. The pipeline calls this once per area instead, which keeps each
    response well inside the limit and makes a failure affect one screen rather
    than all of them.
    """
    focus = f"""\
## This stage — **{area} only**

Generate the components for the **{area}** area of the specification and
nothing else. Other areas are generated in their own stages; do not produce
them here, and do not produce placeholder versions of them.
""" if area else """\
## This stage

Generate the page and shared components the specification requires.
"""

    already = f"""\
## Areas already generated

{areas_done}

Reuse the shared components among them rather than writing new ones that do
the same thing.
""" if areas_done else ""

    return _assemble(
        f"# Task: generate the {area or 'front-end'} components",
        "You are a senior Angular engineer who builds clean, accessible, "
        "responsive interfaces with Bootstrap. You answer with code and "
        "nothing else.",
        _stack(),
        focus,
        """\
Each component lives in its own folder under `frontend/src/app/components/`
and consists of exactly three files:

```
components/<name>/<name>.ts
components/<name>/<name>.html
components/<name>/<name>.css
```

The class is `standalone: true` with an explicit `imports` array listing every
component, directive and pipe its template uses. `@if` and `@for` need no
import; `FormsModule` or `ReactiveFormsModule` and `RouterLink` do.

Requirements:

- **Reactive forms** for anything with validation. Every validation rule the
  specification states appears as a validator, and the message shown is the one
  the specification names. Show a field's error only after it is touched.
- **Server errors are shown.** When a request fails with `fieldErrors`, map them
  onto the matching form controls. A validation failure the user cannot see is
  a broken screen.
- **Three visible states** for anything that loads: in progress, loaded, and
  empty. The empty state says why it is empty. A bare blank area is not a state.
- **Disabled means disabled.** Where the specification says a control is
  disabled under a condition, bind `[disabled]` to that condition rather than
  hiding the control.
- **Tables** that the specification says are sortable sort on a header click and
  toggle direction on a second click, with a visible indicator of the current
  column and direction.
- **Responsive.** Bootstrap's grid and utilities; usable at 375px wide with no
  horizontal scrolling of the page body.
- State is held in `signal()` and derived with `computed()`. Subscriptions that
  outlive the component are cleaned up with `takeUntilDestroyed`.
""",
        already,
        _hard_rules(),
        _output_contract("frontend/src/app/components/"),
        _api_surface(),
        _spec_block(spec),
        _code_block("Front-end services, models and guards",
                    context.collect_code(FRONTEND_SRC / "app" / "services",
                                         FRONTEND_SRC / "app" / "models",
                                         FRONTEND_SRC / "app" / "guards")),
        f"""\
## Components already on disk

```
{context.describe_tree(FRONTEND_SRC / "app" / "components")}
```
""",
        _self_check(),
    )


# ============================================================== 6. app ====
def app_shell(spec: str) -> str:
    manifest = """\
- `frontend/src/app/app.ts` — the root standalone component
- `frontend/src/app/app.html` — the shell: header, navigation, `<router-outlet />`, footer
- `frontend/src/app/app.css`
- `frontend/src/app/app.config.ts` — `ApplicationConfig` with the providers
- `frontend/src/app/app.routes.ts` — the route table
"""
    return _assemble(
        "# Task: generate the application shell, routes and providers",
        "You are a senior Angular engineer. You answer with code and nothing else.",
        _stack(),
        """\
## This stage

This is the **final** front-end stage. Wire together everything that already
exists.

`app.routes.ts`:

- Every route the specification names, at the exact path it names. If the
  specification puts an administrator sign-in on its own route, that route
  exists here and no navigation links to it.
- Lazy-loaded with `loadComponent`, so a visitor does not download screens
  their role cannot reach.
- Guards applied per route, with allowed roles in `data: { roles: [...] }`.
- Order matters: a literal path before a parameterised one that would also
  match it.
- A wildcard `**` route last, showing a not-found view that keeps the shell.

`app.config.ts` provides, at minimum:

```ts
provideRouter(routes, withComponentInputBinding()),
provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
provideZoneChangeDetection({ eventCoalescing: true }),
```

`app.html` is the shell every page sits inside:

- a header with the application name,
- navigation whose items depend on the signed-in role, read from the
  authentication service's signals,
- a sign-out control whenever someone is signed in,
- `<router-outlet />`,
- a footer.

Navigation is built from the role signals, so it updates without a reload when
someone signs in or out. Show only what that role may reach.

Do **not** generate `package-lock.json`, and do not generate a binary
`favicon.ico` — reference `favicon.ico` from `index.html` and leave the file to
be added by hand.
""",
        _hard_rules(),
        _output_contract("frontend/src/app/", manifest),
        _spec_block(spec),
        _code_block("Front-end guards, interceptors and services",
                    context.collect_code(FRONTEND_SRC / "app" / "guards",
                                         FRONTEND_SRC / "app" / "interceptors",
                                         FRONTEND_SRC / "app" / "services")),
        f"""\
## Components available to route to

```
{context.describe_tree(FRONTEND_SRC / "app" / "components")}
```
""",
        _self_check(),
    )
