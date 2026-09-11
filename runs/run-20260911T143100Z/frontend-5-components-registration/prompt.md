# Task: generate the registration components

You are a senior Angular engineer who builds clean, accessible, responsive interfaces with Bootstrap. You answer with code and nothing else.

## Technology, fixed — do not substitute

- Angular 20.3.6
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

## This stage — **registration only**

Generate the components for the **registration** area of the specification and
nothing else. Other areas are generated in their own stages; do not produce
them here, and do not produce placeholder versions of them.

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

## Areas already generated

  - auth

Reuse the shared components among them rather than writing new ones that do
the same thing.

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

- Every file in this stage belongs under `frontend/src/app/components/`.

## The backend HTTP surface — the only routes that exist

These were extracted from the generated backend routers. They are the real
endpoints. Call these exact methods and paths; do not invent, rename or guess.

```

  from backend/src/routers/admin.routes.ts  (mounted at /api/admin)
    GET    /api/admin/statistics
    GET    /api/admin/registration-requests
    POST   /api/admin/registration-requests/:requestId/approve
    POST   /api/admin/registration-requests/:requestId/reject
    GET    /api/admin/users
    GET    /api/admin/users/:userId
    PUT    /api/admin/users/:userId/status
    PUT    /api/admin/users/:userId/role
    DELETE /api/admin/users/:userId
    GET    /api/admin/companies
    GET    /api/admin/spaces
    GET    /api/admin/reservations

  from backend/src/routers/auth.routes.ts  (mounted at /api/auth)
    POST   /api/auth/login
    POST   /api/auth/admin/login
    POST   /api/auth/forgot-password
    GET    /api/auth/reset-password/:token
    POST   /api/auth/reset-password/:token
    POST   /api/auth/refresh
    POST   /api/auth/logout
    GET    /api/auth/me

  from backend/src/routers/company.routes.ts  (mounted at /api/companies)
    POST   /api/companies/companies
    GET    /api/companies/companies/:companyId
    GET    /api/companies/admin/companies
    PUT    /api/companies/admin/companies/:companyId
    DELETE /api/companies/admin/companies/:companyId
    GET    /api/companies/companies/:companyId/managers/count
    GET    /api/companies/admin/companies/:companyNumber/pending-managers/count

  from backend/src/routers/registration.routes.ts  (mounted at /api/auth)
    POST   /api/auth/register/member
    POST   /api/auth/register/manager
    GET    /api/auth/admin/registration-requests
    POST   /api/auth/admin/registration-requests/:requestId/approve
    POST   /api/auth/admin/registration-requests/:requestId/reject
    GET    /api/auth/check-username
    GET    /api/auth/check-email

  from backend/src/routers/reservation.routes.ts  (mounted at /api/reservations)
    POST   /api/reservations/reservations
    GET    /api/reservations/reservations
    GET    /api/reservations/reservations/:reservationId
    GET    /api/reservations/reservations/company
    POST   /api/reservations/reservations/:reservationId/cancel
    POST   /api/reservations/reservations/:reservationId/confirm
    POST   /api/reservations/reservations/:reservationId/complete
    GET    /api/reservations/spaces/:spaceId/availability

  from backend/src/routers/space.routes.ts  (mounted at /api/spaces)
    POST   /api/spaces/spaces
    GET    /api/spaces/spaces/public
    GET    /api/spaces/spaces/:spaceId
    GET    /api/spaces/spaces/company
    PUT    /api/spaces/spaces/:spaceId
    DELETE /api/spaces/spaces/:spaceId
    PATCH  /api/spaces/spaces/:spaceId/toggle-active

  from backend/src/routers/user.routes.ts  (mounted at /api/users)
    GET    /api/users/profile
    PUT    /api/users/profile
    POST   /api/users/profile/password
    DELETE /api/users/profile/image
    POST   /api/users/profile/image
    GET    /api/users/admin/users
    GET    /api/users/admin/users/:userId
    PUT    /api/users/admin/users/:userId/status
    PUT    /api/users/admin/users/:userId/role
    DELETE /api/users/admin/users/:userId

  from backend/src/routes/admin.ts
    GET    /users
    GET    /statistics
    GET    /spaces/pending

  from backend/src/routes/auth.ts
    POST   /login
    POST   /admin/login
    POST   /register/member
    POST   /register/manager
    POST   /forgot-password
    GET    /reset-password/:token
    POST   /reset-password
    GET    /me
    POST   /logout
    GET    /admin/registration-requests
    POST   /admin/registration-requests/approve
    POST   /admin/registration-requests/reject

  from backend/src/routes/images.ts
    POST   /profile-image
    GET    /uploads/:filename
    GET    /default-avatar.png
```

Where a path contains `:param`, substitute the value in the front-end service.

## The specification

What follows is every `.feature` file for this application. Each `===== name =====`
header begins a separate Gherkin file; they all describe the same system. They
are the complete and authoritative requirements, including everything the user
interface must do.

Read the `@ui` scenarios especially closely: they describe what must be on
screen, what is enabled and disabled, what is sorted, and what messages appear.

================ BEGIN GHERKIN SPECIFICATION ================


===== auth/admin-login.feature =====
@auth @security @vibe-part-1 @zero-shot
Feature: Non-public sign-in for the Administrator
  As the system Administrator
  I want a sign-in form that is not advertised anywhere in the public interface
  So that the administrative entry point is not obvious to ordinary visitors

  The Administrator form has the same two fields as the public form but lives on
  its own route. No link to it appears on the landing page or in any public menu.

  Background:
    Given the following administrator account exists:
      | username | password      | role  |
      | admin    | Admin#2026zx  | ADMIN |
    And an approved Member "ana.jovic" with password "Ana#2026pass" exists

  @positive
  Scenario: Administrator signs in through the dedicated route
    Given a Guest opens the route "/admin/login"
    When the Guest submits the administrator sign-in form with username "admin" and password "Admin#2026zx"
    Then the sign-in succeeds
    And the response contains an authentication token whose role claim is "ADMIN"
    And the user is redirected to the administrator dashboard

  @negative
  Scenario: Administrator cannot sign in through the public form
    Given a Guest opens the route "/login"
    When the Guest submits the sign-in form with username "admin" and password "Admin#2026zx"
    Then the sign-in fails with HTTP status 401
    And no authentication token is issued

  @negative
  Scenario Outline: Wrong administrator credentials are refused
    Given a Guest opens the route "/admin/login"
    When the Guest submits the administrator sign-in form with username "<username>" and password "<password>"
    Then the sign-in fails with HTTP status 401
    And the message "Invalid username or password." is displayed

    Examples:
      | username | password      |
      | admin    | Admin#2026aa  |
      | Admin    | Admin#2026zx  |
      | admin    |               |
      | ana.jovic| Ana#2026pass  |

  @ui
  Scenario: The administrator route is not discoverable from the public interface
    Given a Guest is on the landing page
    Then no hyperlink whose target is "/admin/login" is present anywhere in the document
    And no navigation menu item labelled "Administrator" is displayed
    And the sitemap and robots directives do not advertise "/admin/login"

  @security
  Scenario: A Member's token cannot reach administrator endpoints
    Given the Member "ana.jovic" is signed in
    When the Member requests the endpoint "GET /api/admin/users" with their own token
    Then the request fails with HTTP status 403
    And no user records are returned

  @security
  Scenario Outline: Every administrator endpoint rejects non-administrator roles
    Given a user with role "<role>" is signed in
    When that user requests the endpoint "<endpoint>"
    Then the request fails with HTTP status 403

    Examples:
      | role    | endpoint                              |
      | MEMBER  | GET /api/admin/users                  |
      | MEMBER  | GET /api/admin/registration-requests  |
      | MEMBER  | GET /api/admin/spaces/pending         |
      | MEMBER  | GET /api/admin/statistics             |
      | MANAGER | GET /api/admin/users                  |
      | MANAGER | GET /api/admin/registration-requests  |
      | MANAGER | GET /api/admin/spaces/pending         |
      | MANAGER | GET /api/admin/statistics             |

  @security
  Scenario: An unauthenticated request to an administrator endpoint is rejected
    When an unauthenticated request is made to "GET /api/admin/users"
    Then the request fails with HTTP status 401


===== auth/login.feature =====
@auth @vibe-part-1 @zero-shot
Feature: Public sign-in for Members and Space Managers
  As a Member or a Space Manager
  I want to sign in with my username and password
  So that I can reach the functionality my role grants me

  The public sign-in form lives at the route /login and is linked from the
  landing page. Administrators do not use this form (see admin-login.feature).

  Background:
    Given the following approved users exist:
      | username   | password      | role    | status   |
      | ana.jovic  | Ana#2026pass  | MEMBER  | APPROVED |
      | marko.spc  | Marko*1work   | MANAGER | APPROVED |
    And the following users exist but are not approved:
      | username   | password      | role    | status   |
      | pera.novi  | Pera#2026abc  | MEMBER  | PENDING  |
      | zorz.odbi  | Zorz#2026abc  | MANAGER | REJECTED |
    And a Guest is on the public sign-in page

  @positive @api
  Scenario: Member signs in with valid credentials
    When the Guest submits the sign-in form with username "ana.jovic" and password "Ana#2026pass"
    Then the sign-in succeeds
    And the response contains an authentication token whose role claim is "MEMBER"
    And the user is redirected to the member dashboard
    And the main menu shows the items "Profile", "Search and reserve" and "Sign out"

  @positive @api
  Scenario: Space Manager signs in with valid credentials
    When the Guest submits the sign-in form with username "marko.spc" and password "Marko*1work"
    Then the sign-in succeeds
    And the response contains an authentication token whose role claim is "MANAGER"
    And the user is redirected to the manager dashboard
    And the main menu shows the items "Profile", "Spaces", "Import from file", "Reservations", "Calendar", "Reports" and "Sign out"

  @negative @api
  Scenario Outline: Sign-in is refused for bad credentials
    When the Guest submits the sign-in form with username "<username>" and password "<password>"
    Then the sign-in fails with HTTP status 401
    And the message "Invalid username or password." is displayed
    And no authentication token is issued

    Examples: wrong password, unknown user, empty fields
      | username   | password      |
      | ana.jovic  | Ana#2026wrong |
      | ana.jovic  |               |
      | nepostoji  | Ana#2026pass  |
      |            | Ana#2026pass  |
      |            |               |

  @negative @security
  Scenario: The failure message does not reveal whether the username exists
    When the Guest submits the sign-in form with username "ana.jovic" and password "Ana#2026wrong"
    And the Guest submits the sign-in form with username "nepostoji" and password "Ana#2026wrong"
    Then both attempts return HTTP status 401
    And both attempts display exactly the same message

  @negative @security
  Scenario Outline: Users whose registration is not approved cannot sign in
    When the Guest submits the sign-in form with username "<username>" and password "<password>"
    Then the sign-in fails with HTTP status 403
    And the message "<message>" is displayed

    Examples:
      | username   | password      | message                                                      |
      | pera.novi  | Pera#2026abc  | Your registration is still awaiting administrator approval.  |
      | zorz.odbi  | Zorz#2026abc  | Your registration request was rejected.                      |

  @negative @security
  Scenario: A Member cannot sign in through the administrator form
    When the Guest submits the administrator sign-in form with username "ana.jovic" and password "Ana#2026pass"
    Then the sign-in fails with HTTP status 401
    And no authentication token is issued

  @security @api
  Scenario: Passwords are never returned by the sign-in endpoint
    When the Guest submits the sign-in form with username "ana.jovic" and password "Ana#2026pass"
    Then the sign-in succeeds
    And the response body contains no field named "password"
    And the response body contains no field named "passwordHash"

  @security
  Scenario: Stored passwords are not readable
    When the stored record for username "ana.jovic" is inspected directly in the database
    Then the stored password value is not equal to "Ana#2026pass"
    And the stored password value is a one-way hash with a per-user salt

  @ui @positive
  Scenario: The sign-in page offers a way to recover a forgotten password
    Then a link labelled "Forgotten password?" is displayed below the sign-in form
    And activating that link opens the route "/forgot-password"

  @positive @ui
  Scenario: A signed-in Member can sign out from any page
    Given the Member "ana.jovic" is signed in
    And the Member is on the space details page for "Dorcol Hub"
    When the Member activates "Sign out"
    Then the authentication token is discarded
    And the Member is returned to the landing page
    And requesting the member dashboard again returns HTTP status 401


===== auth/password-reset.feature =====
@auth @vibe-part-1 @zero-shot
Feature: Forgotten password recovery
  As a Member or Space Manager who has forgotten my password
  I want to request a temporary reset link and choose a new password
  So that I can regain access without contacting an administrator

  The reset link is valid for exactly 30 minutes from the moment it was
  requested, and it may be used only once.

  Background:
    Given the following approved users exist:
      | username  | email                | password     |
      | ana.jovic | ana.jovic@primer.rs  | Ana#2026pass |
      | marko.spc | marko@spc-doo.rs     | Marko*1work  |
    And the current time is "2026-03-10 09:00:00"

  @positive
  Scenario Outline: A reset link is issued for a known username or email
    Given a Guest is on the route "/forgot-password"
    When the Guest submits the recovery form with the identifier "<identifier>"
    Then a reset token is created for the user "ana.jovic"
    And the reset token expires at "2026-03-10 09:30:00"
    And a message telling the user to check their inbox is displayed
    And a reset link containing that token is delivered to "ana.jovic@primer.rs"

    Examples: the same user is found by either identifier
      | identifier           |
      | ana.jovic            |
      | ana.jovic@primer.rs  |

  @positive
  Scenario: A valid reset link lets the user set a new password
    Given a reset token "T-VALID" was issued for "ana.jovic" at "2026-03-10 09:00:00"
    And the current time is "2026-03-10 09:20:00"
    When the Guest opens the reset link for token "T-VALID"
    Then the new-password form is displayed
    When the Guest submits the new password "Ana#2026new" twice
    Then the password change succeeds
    And signing in as "ana.jovic" with "Ana#2026new" succeeds
    And signing in as "ana.jovic" with "Ana#2026pass" fails with HTTP status 401

  @negative @security
  Scenario: A reset link older than 30 minutes is refused
    Given a reset token "T-OLD" was issued for "ana.jovic" at "2026-03-10 09:00:00"
    And the current time is "2026-03-10 09:30:01"
    When the Guest opens the reset link for token "T-OLD"
    Then the request fails with HTTP status 410
    And the message "This reset link has expired. Please request a new one." is displayed
    And the new-password form is not displayed

  @negative @security
  Scenario: A reset link at exactly 30 minutes is still accepted
    Given a reset token "T-EDGE" was issued for "ana.jovic" at "2026-03-10 09:00:00"
    And the current time is "2026-03-10 09:30:00"
    When the Guest opens the reset link for token "T-EDGE"
    Then the new-password form is displayed

  @negative @security
  Scenario: A reset link cannot be used twice
    Given a reset token "T-ONCE" was issued for "ana.jovic" at "2026-03-10 09:00:00"
    And the current time is "2026-03-10 09:05:00"
    And the Guest has already set the new password "Ana#2026new" using token "T-ONCE"
    When the Guest opens the reset link for token "T-ONCE" again
    Then the request fails with HTTP status 410
    And the message "This reset link has already been used." is displayed

  @negative @security
  Scenario: An unknown or tampered token is refused
    When the Guest opens the reset link for token "T-DOES-NOT-EXIST"
    Then the request fails with HTTP status 410
    And no password is changed for any user

  @negative @security
  Scenario: Requesting a reset for an unknown identifier does not disclose account existence
    Given a Guest is on the route "/forgot-password"
    When the Guest submits the recovery form with the identifier "nepostojeci@primer.rs"
    Then the response has HTTP status 200
    And the same "check your inbox" message is displayed as for a known identifier
    And no reset token is created
    And no message is delivered

  @negative @validation
  Scenario Outline: The new password must satisfy the password policy
    Given a reset token "T-VALID" was issued for "ana.jovic" at "2026-03-10 09:00:00"
    And the current time is "2026-03-10 09:05:00"
    When the Guest submits the new password "<password>" twice
    Then the password change fails with HTTP status 400
    And the message "<message>" is displayed
    And the password for "ana.jovic" is unchanged

    Examples:
      | password        | message                                            |
      | Ab#1cde         | Password must be between 8 and 12 characters.      |
      | Abcdefg#1234x   | Password must be between 8 and 12 characters.      |
      | abcdef#1        | Password must contain at least one uppercase letter.|
      | Abcdefg#        | Password must contain at least one digit.          |
      | Abcdefg1        | Password must contain at least one special character.|
      | 1Abcdef#        | Password must begin with a letter.                 |
      | #Abcdef1        | Password must begin with a letter.                 |

  @negative @validation
  Scenario: The two new-password fields must match
    Given a reset token "T-VALID" was issued for "ana.jovic" at "2026-03-10 09:00:00"
    And the current time is "2026-03-10 09:05:00"
    When the Guest submits the new password "Ana#2026new" and the confirmation "Ana#2026NEW"
    Then the password change fails with HTTP status 400
    And the message "The two passwords do not match." is displayed

  @security
  Scenario: All outstanding reset tokens are invalidated once one is used
    Given a reset token "T-ONE" was issued for "ana.jovic" at "2026-03-10 09:00:00"
    And a reset token "T-TWO" was issued for "ana.jovic" at "2026-03-10 09:02:00"
    And the current time is "2026-03-10 09:05:00"
    When the Guest sets the new password "Ana#2026new" using token "T-ONE"
    And the Guest opens the reset link for token "T-TWO"
    Then the request fails with HTTP status 410


===== registration/manager-registration.feature =====
@registration @vibe-part-1 @zero-shot
Feature: Space Manager registration and company constraints
  As a visitor who operates coworking premises
  I want to register as a Space Manager on behalf of my company
  So that after approval I can publish and manage that company's Spaces

  A Space Manager submits everything a Member submits plus four company fields.
  Company identity is enforced by two national identifiers with strict formats,
  and a company may never have more than two Space Managers at the same time.

  Background:
    Given the following company exists:
      | name          | headquartersAddress   | companyNumber | taxId     |
      | SPC Radionica | Bulevar Kralja 12, BG | 12345678      | 101234567 |
    And the following approved Space Managers represent "SPC Radionica":
      | username  |
      | marko.spc |
    And a Guest is on the route "/register"
    And the Guest has selected the account type "Space Manager"

  @positive @api
  Scenario: A visitor registers as the manager of a brand-new company
    When the Guest submits the registration form with:
      | field               | value                  |
      | username            | jelena.hub             |
      | password            | Jelena#26x             |
      | firstName           | Jelena                 |
      | lastName            | Ilic                   |
      | phone               | +381631112223          |
      | email               | jelena@nova-firma.rs   |
      | companyName         | Nova Firma             |
      | headquartersAddress | Nemanjina 4, Beograd   |
      | companyNumber       | 87654321               |
      | taxId               | 987654321              |
    And the Guest attaches the profile image "avatar-150x150.jpg"
    Then the registration succeeds with HTTP status 201
    And a registration request for "jelena.hub" is created with status "PENDING"
    And the role of the created account is "MANAGER"
    And a company "Nova Firma" with companyNumber "87654321" and taxId "987654321" exists

  @positive @api
  Scenario: A second manager may join an existing company
    When the Guest submits a valid Space Manager registration for "nikola.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration succeeds with HTTP status 201
    And "nikola.spc" is associated with the existing company "SPC Radionica"
    And no duplicate company record is created

  @negative @api
  Scenario: A third manager for the same company is refused
    Given the approved Space Manager "nikola.spc" also represents "SPC Radionica"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration fails with HTTP status 409
    And the message "This company already has the maximum of two space managers." is displayed
    And no registration request is created

  @negative @api
  Scenario: A pending manager still counts towards the company limit
    Given a registration request for "nikola.spc" representing "SPC Radionica" exists with status "PENDING"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration fails with HTTP status 409
    And the message "This company already has the maximum of two space managers." is displayed

  @positive @api
  Scenario: A rejected manager does not count towards the company limit
    Given a registration request for "nikola.spc" representing "SPC Radionica" exists with status "REJECTED"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration succeeds with HTTP status 201

  @positive @api
  Scenario: Removing a manager frees a slot
    Given the approved Space Manager "nikola.spc" also represents "SPC Radionica"
    And the Administrator deletes the account "nikola.spc"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration succeeds with HTTP status 201

  @negative @validation
  Scenario Outline: The company number must be exactly eight digits
    When the Guest submits a valid Space Manager registration with the companyNumber "<companyNumber>"
    Then the registration fails with HTTP status 400
    And the field "companyNumber" is marked with the message "Company number must be exactly 8 digits."

    Examples: too short, too long, non-numeric, spaced
      | companyNumber |
      | 1234567       |
      | 123456789     |
      | 1234567a      |
      | 1234 5678     |
      |               |
      | -1234567      |

  @positive @validation
  Scenario: A company number beginning with zero is valid
    When the Guest submits a valid Space Manager registration with the companyNumber "01234567"
    Then the registration succeeds with HTTP status 201

  @negative @validation
  Scenario Outline: The tax identification number must be exactly nine digits and must not begin with zero
    When the Guest submits a valid Space Manager registration with the taxId "<taxId>"
    Then the registration fails with HTTP status 400
    And the field "taxId" is marked with the message "<message>"

    Examples:
      | taxId      | message                                       |
      | 12345678   | Tax ID must be exactly 9 digits.              |
      | 1234567890 | Tax ID must be exactly 9 digits.              |
      | 12345678a  | Tax ID must be exactly 9 digits.              |
      |            | Tax ID is required.                           |
      | 012345678  | Tax ID must not begin with zero.              |
      | 000000000  | Tax ID must not begin with zero.              |

  @positive @validation
  Scenario Outline: Tax identification numbers at the edge of the rule are accepted
    When the Guest submits a valid Space Manager registration with the taxId "<taxId>"
    Then the registration succeeds with HTTP status 201

    Examples:
      | taxId     |
      | 100000000 |
      | 999999999 |

  @negative @api
  Scenario: The company number is unique across companies
    When the Guest submits a valid Space Manager registration with the companyName "Druga Firma", the companyNumber "12345678" and the taxId "222333444"
    Then the registration fails with HTTP status 409
    And the message "A different company is already registered with that company number." is displayed

  @negative @api
  Scenario: The tax identification number is unique across companies
    When the Guest submits a valid Space Manager registration with the companyName "Druga Firma", the companyNumber "55556666" and the taxId "101234567"
    Then the registration fails with HTTP status 409
    And the message "A different company is already registered with that tax ID." is displayed

  @negative @validation
  Scenario Outline: The remaining company fields are mandatory
    When the Guest submits a valid Space Manager registration but leaves "<field>" empty
    Then the registration fails with HTTP status 400
    And the field "<field>" is marked with the message "<message>"

    Examples:
      | field               | message                          |
      | companyName         | Company name is required.        |
      | headquartersAddress | Headquarters address is required.|

  @security @api
  Scenario: Company constraints are enforced on the server, not only in the browser
    When a request is sent directly to "POST /api/auth/register" with role "MANAGER", companyNumber "999" and taxId "0"
    Then the registration fails with HTTP status 400
    And the response body reports violations for both "companyNumber" and "taxId"


===== registration/member-registration.feature =====
@registration @vibe-part-1 @zero-shot
Feature: Member registration
  As a visitor
  I want to register as a Member of the coworking network
  So that after an Administrator approves me I can search for and reserve workspaces

  Registration never creates an active account directly: it creates a
  registration request with status PENDING that an Administrator must decide on.

  Background:
    Given the following users already exist:
      | username  | email               |
      | ana.jovic | ana.jovic@primer.rs |
    And a Guest is on the route "/register"
    And the Guest has selected the account type "Member"

  @positive @api
  Scenario: A visitor registers with complete, valid data
    When the Guest submits the registration form with:
      | field         | value                 |
      | username      | pera.peric            |
      | password      | Pera#2026ab           |
      | firstName     | Petar                 |
      | lastName      | Peric                 |
      | phone         | +381641234567         |
      | email         | pera.peric@primer.rs  |
    And the Guest attaches the profile image "avatar-200x200.png"
    Then the registration succeeds with HTTP status 201
    And a registration request for "pera.peric" is created with status "PENDING"
    And the role of the created account is "MEMBER"
    And the message "Your registration request has been submitted and is awaiting approval." is displayed
    And signing in as "pera.peric" with "Pera#2026ab" fails with HTTP status 403

  @positive
  Scenario: A visitor who uploads no image receives the system default image
    When the Guest submits a valid Member registration for "pera.peric" without attaching an image
    Then the registration succeeds with HTTP status 201
    And the profile image of "pera.peric" is the system default image

  @negative @validation @api
  Scenario: The username must be unique across all users
    When the Guest submits a valid Member registration using the username "ana.jovic"
    Then the registration fails with HTTP status 409
    And the message "That username is already taken." is displayed
    And no registration request is created

  @negative @validation @api
  Scenario: The email address must be unique across all users
    When the Guest submits a valid Member registration using the email "ana.jovic@primer.rs"
    Then the registration fails with HTTP status 409
    And the message "An account with that email address already exists." is displayed
    And no registration request is created

  @negative @validation
  Scenario Outline: Mandatory fields are rejected when empty
    When the Guest submits a valid Member registration but leaves "<field>" empty
    Then the registration fails with HTTP status 400
    And the field "<field>" is marked with the message "<message>"
    And no registration request is created

    Examples:
      | field     | message                    |
      | username  | Username is required.      |
      | password  | Password is required.      |
      | firstName | First name is required.    |
      | lastName  | Last name is required.     |
      | phone     | Contact phone is required. |
      | email     | Email address is required. |

  @negative @validation
  Scenario Outline: The password must satisfy the password policy
    When the Guest submits a valid Member registration with the password "<password>"
    Then the registration fails with HTTP status 400
    And the field "password" is marked with the message "<message>"

    Examples: too short, too long, missing character class, wrong first character
      | password        | message                                             |
      | Ab#1cde         | Password must be between 8 and 12 characters.       |
      | Abcdefg#1234x   | Password must be between 8 and 12 characters.       |
      | abcdefg#1       | Password must contain at least one uppercase letter.|
      | Abcdefgh#       | Password must contain at least one digit.           |
      | Abcdefgh1       | Password must contain at least one special character.|
      | 1Abcde#f        | Password must begin with a letter.                  |
      | #Abcde1f        | Password must begin with a letter.                  |
      |                 | Password is required.                               |

  @positive @validation
  Scenario Outline: Passwords at the boundaries of the policy are accepted
    When the Guest submits a valid Member registration with the password "<password>"
    Then the registration succeeds with HTTP status 201

    Examples: exactly 8 and exactly 12 characters
      | password      |
      | Abcdef#1      |
      | Abcdefgh#123  |

  @negative @validation
  Scenario Outline: The email address must be well formed
    When the Guest submits a valid Member registration with the email "<email>"
    Then the registration fails with HTTP status 400
    And the field "email" is marked with the message "Enter a valid email address."

    Examples:
      | email             |
      | pera              |
      | pera@             |
      | @primer.rs        |
      | pera@primer       |
      | pera @primer.rs   |
      | pera@@primer.rs   |

  @negative @validation
  Scenario Outline: The contact phone must be a plausible phone number
    When the Guest submits a valid Member registration with the phone "<phone>"
    Then the registration fails with HTTP status 400
    And the field "phone" is marked with the message "Enter a valid contact phone number."

    Examples:
      | phone           |
      | abcdefg         |
      | 12              |
      | +381-64-abc     |
      | 06412345678901234 |

  @security @api
  Scenario: Client-side validation is not the only line of defence
    When a request is sent directly to "POST /api/auth/register" bypassing the browser form, with the password "weak"
    Then the registration fails with HTTP status 400
    And the response body reports a violation of the password policy
    And no registration request is created

  @security @api
  Scenario: A visitor cannot self-assign a privileged role
    When a request is sent directly to "POST /api/auth/register" with the field "role" set to "ADMIN"
    Then no account with role "ADMIN" is created
    And any account that is created has role "MEMBER"

  @security @api
  Scenario: A visitor cannot self-approve a registration
    When a request is sent directly to "POST /api/auth/register" with the field "status" set to "APPROVED"
    Then the created registration request has status "PENDING"
    And signing in with the new account fails with HTTP status 403


===== registration/profile-image-upload.feature =====
@registration @upload @vibe-part-1 @zero-shot
Feature: Profile image upload
  As a registering or existing user
  I want to upload my profile picture as a file
  So that my account shows my own image rather than the system default

  Images enter the system exclusively through a file-upload control. Supplying a
  link to an image hosted elsewhere is never an acceptable substitute. Accepted
  formats are JPG and PNG; accepted pixel dimensions are 100x100 through 300x300
  inclusive, in both directions.

  Background:
    Given a Guest is on the route "/register"

  @positive @validation
  Scenario Outline: Images inside the permitted envelope are accepted
    When the Guest attaches the profile image "<file>" of type "<mimeType>" measuring <width>x<height> pixels
    Then the upload is accepted
    And the attached image is shown as a preview beside the form

    Examples: the four corners of the permitted range and a typical case
      | file              | mimeType   | width | height |
      | min.png           | image/png  | 100   | 100    |
      | max.png           | image/png  | 300   | 300    |
      | wide.jpg          | image/jpeg | 300   | 100    |
      | tall.jpg          | image/jpeg | 100   | 300    |
      | avatar-200.jpg    | image/jpeg | 200   | 200    |

  @negative @validation
  Scenario Outline: Images outside the permitted pixel range are rejected
    When the Guest attaches the profile image "<file>" of type "image/png" measuring <width>x<height> pixels
    Then the upload fails with HTTP status 400
    And the message "The image must be between 100x100 and 300x300 pixels." is displayed
    And no file is stored on the server

    Examples: just under, just over, and far outside
      | file        | width | height |
      | tiny.png    | 99    | 100    |
      | tiny2.png   | 100   | 99     |
      | big.png     | 301   | 300    |
      | big2.png    | 300   | 301    |
      | huge.png    | 1920  | 1080   |
      | sliver.png  | 50    | 400    |

  @negative @validation
  Scenario Outline: Only JPG and PNG files are accepted
    When the Guest attaches the profile image "<file>" of type "<mimeType>" measuring 200x200 pixels
    Then the upload fails with HTTP status 415
    And the message "Only JPG and PNG images are accepted." is displayed
    And no file is stored on the server

    Examples:
      | file           | mimeType                 |
      | animation.gif  | image/gif                |
      | vector.svg     | image/svg+xml            |
      | photo.bmp      | image/bmp                |
      | scan.pdf       | application/pdf          |
      | modern.webp    | image/webp               |
      | archive.zip    | application/zip          |

  @negative @security
  Scenario: A file whose extension lies about its content is rejected
    When the Guest attaches a file named "payload.png" whose actual content is a PHP script
    Then the upload fails with HTTP status 415
    And the message "Only JPG and PNG images are accepted." is displayed
    And the decision is based on the file's inspected content, not on its file name

  @negative @security
  Scenario: An image supplied as an external link is not accepted
    When a request is sent directly to "POST /api/users/profile-image" with the body field "imageUrl" set to "https://example.com/avatar.png"
    Then the request fails with HTTP status 400
    And the message "The profile image must be uploaded as a file." is displayed
    And the server makes no outbound request to "example.com"

  @negative @security
  Scenario: The upload endpoint refuses oversized payloads
    When the Guest attaches a PNG file of 25 megabytes measuring 200x200 pixels
    Then the upload fails with HTTP status 413
    And the message "The uploaded file is too large." is displayed

  @negative @security
  Scenario Outline: The stored file name cannot be used to escape the upload directory
    When the Guest attaches a valid 200x200 PNG named "<fileName>"
    Then the stored file is written inside the configured upload directory only
    And the stored file name contains no path separator and no parent-directory segment

    Examples:
      | fileName                   |
      | ../../etc/passwd.png       |
      | ..\\..\\windows\\a.png     |
      | normal name (1).png        |
      | ćirilica-слика.png         |

  @positive
  Scenario: Omitting the image assigns the system default
    When the Guest submits a valid Member registration without attaching any image
    Then the registration succeeds with HTTP status 201
    And the profile image of the created account is the system default image
    And the default image is served from the application's own static assets

  @positive @ui
  Scenario: An existing user replaces their profile image from the profile page
    Given the Member "ana.jovic" is signed in
    And the profile image of "ana.jovic" is "old-avatar.png"
    When the Member opens the profile page
    And the Member attaches the profile image "new-avatar.png" of type "image/png" measuring 250x250 pixels
    And the Member saves the profile
    Then the profile image of "ana.jovic" is "new-avatar.png"
    And the previously stored file "old-avatar.png" is no longer referenced by any account

  @negative @security
  Scenario: A Member cannot replace another user's profile image
    Given the Member "ana.jovic" is signed in
    When a request is sent to "POST /api/users/marko.spc/profile-image" with a valid image
    Then the request fails with HTTP status 403
    And the profile image of "marko.spc" is unchanged


===== registration/registration-approval.feature =====
@registration @admin @vibe-part-1 @zero-shot
Feature: Administrator decision on registration requests
  As the Administrator
  I want to review every pending Member and Space Manager registration
  So that only vetted people become active users of the network

  Background:
    Given the Administrator "admin" is signed in
    And the following registration requests exist:
      | username    | role    | company       | submittedAt         | status   |
      | pera.novi   | MEMBER  |               | 2026-03-01 10:00:00 | PENDING  |
      | jelena.hub  | MANAGER | Nova Firma    | 2026-03-02 11:30:00 | PENDING  |
      | milan.stari | MEMBER  |               | 2026-02-20 08:15:00 | APPROVED |
      | zorz.odbi   | MANAGER | Stara Firma   | 2026-02-21 09:45:00 | REJECTED |

  @positive @ui
  Scenario: The pending list shows only undecided requests
    When the Administrator opens the registration requests page
    Then the table lists exactly the usernames "pera.novi" and "jelena.hub"
    And "milan.stari" is not listed
    And "zorz.odbi" is not listed
    And each row shows the username, full name, email, role, submission date and the actions "Approve" and "Reject"

  @positive @ui
  Scenario: Company details are shown for Space Manager requests only
    When the Administrator opens the registration requests page
    Then the row for "jelena.hub" shows the company name, headquarters address, company number and tax ID
    And the row for "pera.novi" shows no company details

  @positive @api
  Scenario: Approving a request activates the account
    When the Administrator approves the registration request for "pera.novi"
    Then the request status becomes "APPROVED"
    And signing in as "pera.novi" with their chosen password succeeds
    And "pera.novi" no longer appears in the pending list

  @positive @api
  Scenario: Rejecting a request keeps the account inactive
    When the Administrator rejects the registration request for "pera.novi"
    Then the request status becomes "REJECTED"
    And signing in as "pera.novi" fails with HTTP status 403
    And the message "Your registration request was rejected." is displayed to that user
    And "pera.novi" no longer appears in the pending list

  @positive @api
  Scenario: The username of a rejected applicant is released for reuse
    Given the Administrator rejected the registration request for "pera.novi"
    When a Guest submits a valid Member registration using the username "pera.novi"
    Then the registration succeeds with HTTP status 201

  @negative @api
  Scenario: The username of an approved user is not available
    When a Guest submits a valid Member registration using the username "milan.stari"
    Then the registration fails with HTTP status 409

  @negative @api
  Scenario Outline: A request that has already been decided cannot be decided again
    When the Administrator attempts to <action> the registration request for "<username>"
    Then the request fails with HTTP status 409
    And the message "This registration request has already been decided." is displayed
    And the status of "<username>" remains "<status>"

    Examples:
      | action  | username    | status   |
      | approve | milan.stari | APPROVED |
      | reject  | milan.stari | APPROVED |
      | approve | zorz.odbi   | REJECTED |
      | reject  | zorz.odbi   | REJECTED |

  @negative @api
  Scenario: Approving a manager would breach the two-manager company limit
    Given the company "SPC Radionica" already has two approved Space Managers
    And a registration request for "cetvrti.spc" representing "SPC Radionica" exists with status "PENDING"
    When the Administrator approves the registration request for "cetvrti.spc"
    Then the request fails with HTTP status 409
    And the message "This company already has the maximum of two space managers." is displayed
    And the status of "cetvrti.spc" remains "PENDING"

  @security
  Scenario Outline: Only the Administrator may decide registration requests
    Given a user with role "<role>" is signed in
    When that user attempts to approve the registration request for "pera.novi"
    Then the request fails with HTTP status 403
    And the status of "pera.novi" remains "PENDING"

    Examples:
      | role    |
      | MEMBER  |
      | MANAGER |

  @security
  Scenario: An unauthenticated visitor cannot see pending requests
    Given no user is signed in
    When a request is made to "GET /api/admin/registration-requests"
    Then the request fails with HTTP status 401

  @positive @ui
  Scenario: Pending requests can be sorted by submission date
    When the Administrator opens the registration requests page
    And the Administrator activates the "Submitted" column header
    Then the rows are ordered by submission date ascending
    When the Administrator activates the "Submitted" column header again
    Then the rows are ordered by submission date descending

================= END GHERKIN SPECIFICATION =================

## Front-end services, models and guards

These files already exist. Import from them and match their exports exactly.
Do not restate them unless you are deliberately changing one, in which case
return the complete changed file.

================ BEGIN EXISTING CODE ================


===== EXISTING FILE: frontend/src/app/services/admin.service.ts =====
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AdminStatistics, ApproveRegistrationResult, RejectRegistrationResult, DeleteResult, PaginationParams, PaginatedResult } from '../models/api.model';
import { RegistrationRequest } from '../models/registration-request.model';
import { User } from '../models/user.model';
import { Company } from '../models/company.model';
import { Space } from '../models/space.model';
import { ReservationWithDetails } from '../models/reservation.model';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getStatistics(): Observable<AdminStatistics> {
    return this.http.get<AdminStatistics>(`${this.apiUrl}/admin/statistics`);
  }

  getRegistrationRequests(params?: PaginationParams): Observable<PaginatedResult<RegistrationRequest>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<RegistrationRequest>>(`${this.apiUrl}/admin/registration-requests`, { params: httpParams });
  }

  approveRegistrationRequest(requestId: string): Observable<ApproveRegistrationResult> {
    return this.http.post<ApproveRegistrationResult>(`${this.apiUrl}/admin/registration-requests/${requestId}/approve`, {});
  }

  rejectRegistrationRequest(requestId: string): Observable<RejectRegistrationResult> {
    return this.http.post<RejectRegistrationResult>(`${this.apiUrl}/admin/registration-requests/${requestId}/reject`, {});
  }

  getUsers(params?: PaginationParams): Observable<PaginatedResult<User>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<User>>(`${this.apiUrl}/admin/users`, { params: httpParams });
  }

  getUser(userId: string): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/admin/users/${userId}`);
  }

  updateUserStatus(userId: string, status: string): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/admin/users/${userId}/status`, { status });
  }

  updateUserRole(userId: string, role: string): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/admin/users/${userId}/role`, { role });
  }

  deleteUser(userId: string): Observable<DeleteResult> {
    return this.http.delete<DeleteResult>(`${this.apiUrl}/admin/users/${userId}`);
  }

  getCompanies(params?: PaginationParams): Observable<PaginatedResult<Company>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Company>>(`${this.apiUrl}/admin/companies`, { params: httpParams });
  }

  getSpaces(params?: PaginationParams): Observable<PaginatedResult<Space>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Space>>(`${this.apiUrl}/admin/spaces`, { params: httpParams });
  }

  getReservations(params?: PaginationParams): Observable<PaginatedResult<ReservationWithDetails>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<ReservationWithDetails>>(`${this.apiUrl}/admin/reservations`, { params: httpParams });
  }
}


===== EXISTING FILE: frontend/src/app/services/auth.service.ts =====
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  LoginData,
  LoginResult,
  RefreshTokenData,
  RefreshTokenResult,
  JwtPayload,
  TokenPair,
  MeResponse,
  LogoutResponse,
  UserRole
} from '../models/auth.model';
import { RequestPasswordResetData, RequestPasswordResetResponse, VerifyPasswordResetTokenResponse, ConfirmPasswordResetData, ConfirmPasswordResetResponse } from '../models/password-reset.model';
import { RegisterMemberData, RegisterManagerData, RegistrationResponse, CheckAvailabilityResponse } from '../models/registration-request.model';
import { User } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  private readonly accessTokenKey = 'access_token';
  private readonly refreshTokenKey = 'refresh_token';
  private readonly userKey = 'current_user';

  private readonly _currentUser = signal<User | null>(null);
  readonly currentUser = this._currentUser.asReadonly();

  readonly isAuthenticated = computed(() => this._currentUser() !== null);
  readonly userRole = computed(() => this._currentUser()?.role ?? null);
  readonly isAdmin = computed(() => this._currentUser()?.role === UserRole.ADMIN);
  readonly isManager = computed(() => this._currentUser()?.role === UserRole.MANAGER);
  readonly isMember = computed(() => this._currentUser()?.role === UserRole.MEMBER);

  constructor() {
    this.restoreSession();
  }

  private restoreSession(): void {
    const accessToken = localStorage.getItem(this.accessTokenKey);
    const refreshToken = localStorage.getItem(this.refreshTokenKey);
    const userJson = localStorage.getItem(this.userKey);

    if (accessToken && refreshToken && userJson) {
      try {
        const user = JSON.parse(userJson) as User;
        this._currentUser.set(user);
      } catch {
        this.clearSession();
      }
    }
  }

  private saveSession(tokens: TokenPair, user: User): void {
    localStorage.setItem(this.accessTokenKey, tokens.accessToken);
    localStorage.setItem(this.refreshTokenKey, tokens.refreshToken);
    localStorage.setItem(this.userKey, JSON.stringify(user));
    this._currentUser.set(user);
  }

  private clearSession(): void {
    localStorage.removeItem(this.accessTokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
    this._currentUser.set(null);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.accessTokenKey);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.refreshTokenKey);
  }

  login(data: LoginData): Observable<LoginResult> {
    return this.http.post<LoginResult>(`${this.apiUrl}/auth/login`, data).pipe(
      tap(result => this.saveSession({ accessToken: result.accessToken, refreshToken: result.refreshToken }, {
        id: result.user.id,
        username: result.user.username,
        firstName: '',
        lastName: '',
        phone: '',
        email: '',
        role: result.user.role,
        status: 'APPROVED' as any,
        profileImage: '',
        createdAt: '',
        updatedAt: ''
      }))
    );
  }

  adminLogin(data: LoginData): Observable<LoginResult> {
    return this.http.post<LoginResult>(`${this.apiUrl}/auth/admin/login`, data).pipe(
      tap(result => this.saveSession({ accessToken: result.accessToken, refreshToken: result.refreshToken }, {
        id: result.user.id,
        username: result.user.username,
        firstName: '',
        lastName: '',
        phone: '',
        email: '',
        role: result.user.role,
        status: 'APPROVED' as any,
        profileImage: '',
        createdAt: '',
        updatedAt: ''
      }))
    );
  }

  logout(): Observable<LogoutResponse> {
    const refreshToken = this.getRefreshToken();
    return this.http.post<LogoutResponse>(`${this.apiUrl}/auth/logout`, { refreshToken } as RefreshTokenData).pipe(
      tap(() => this.clearSession()),
      catchError(err => {
        this.clearSession();
        return throwError(() => err);
      })
    );
  }

  refreshToken(): Observable<RefreshTokenResult> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return throwError(() => new Error('No refresh token available'));
    }
    return this.http.post<RefreshTokenResult>(`${this.apiUrl}/auth/refresh`, { refreshToken } as RefreshTokenData).pipe(
      tap(result => {
        localStorage.setItem(this.accessTokenKey, result.accessToken);
        localStorage.setItem(this.refreshTokenKey, result.refreshToken);
      })
    );
  }

  me(): Observable<MeResponse> {
    return this.http.get<MeResponse>(`${this.apiUrl}/auth/me`);
  }

  registerMember(data: RegisterMemberData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/member`, data);
  }

  registerManager(data: RegisterManagerData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/manager`, data);
  }

  checkUsernameAvailability(username: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('username', username);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-username`, { params });
  }

  checkEmailAvailability(email: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('email', email);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-email`, { params });
  }

  requestPasswordReset(data: RequestPasswordResetData): Observable<RequestPasswordResetResponse> {
    return this.http.post<RequestPasswordResetResponse>(`${this.apiUrl}/auth/forgot-password`, data);
  }

  verifyResetToken(token: string): Observable<VerifyPasswordResetTokenResponse> {
    return this.http.get<VerifyPasswordResetTokenResponse>(`${this.apiUrl}/auth/reset-password/${token}`);
  }

  confirmPasswordReset(token: string, data: ConfirmPasswordResetData): Observable<ConfirmPasswordResetResponse> {
    return this.http.post<ConfirmPasswordResetResponse>(`${this.apiUrl}/auth/reset-password/${token}`, data);
  }

  hasRole(role: UserRole): boolean {
    return this._currentUser()?.role === role;
  }

  hasAnyRole(roles: UserRole[]): boolean {
    const userRole = this._currentUser()?.role;
    return userRole ? roles.includes(userRole) : false;
  }
}


===== EXISTING FILE: frontend/src/app/services/company.service.ts =====
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Company, CompanyData, CompanyManagersCount, CompanyPendingManagersCount } from '../models/company.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class CompanyService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  createCompany(data: CompanyData): Observable<Company> {
    return this.http.post<Company>(`${this.apiUrl}/companies/companies`, data);
  }

  getCompany(companyId: string): Observable<Company> {
    return this.http.get<Company>(`${this.apiUrl}/companies/companies/${companyId}`);
  }

  getAdminCompanies(params?: PaginationParams): Observable<PaginatedResult<Company>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Company>>(`${this.apiUrl}/companies/admin/companies`, { params: httpParams });
  }

  updateCompany(companyId: string, data: Partial<CompanyData>): Observable<Company> {
    return this.http.put<Company>(`${this.apiUrl}/companies/admin/companies/${companyId}`, data);
  }

  deleteCompany(companyId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/companies/admin/companies/${companyId}`);
  }

  getManagersCount(companyId: string): Observable<CompanyManagersCount> {
    return this.http.get<CompanyManagersCount>(`${this.apiUrl}/companies/companies/${companyId}/managers/count`);
  }

  getPendingManagersCount(companyNumber: string): Observable<CompanyPendingManagersCount> {
    return this.http.get<CompanyPendingManagersCount>(`${this.apiUrl}/companies/admin/companies/${companyNumber}/pending-managers/count`);
  }
}


===== EXISTING FILE: frontend/src/app/services/index.ts =====
export * from './auth.service';
export * from './admin.service';
export * from './company.service';
export * from './registration.service';
export * from './reservation.service';
export * from './space.service';
export * from './user.service';


===== EXISTING FILE: frontend/src/app/services/registration.service.ts =====
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { RegistrationRequest, RegisterMemberData, RegisterManagerData, RegistrationResponse, CheckAvailabilityResponse } from '../models/registration-request.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class RegistrationService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  registerMember(data: RegisterMemberData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/member`, data);
  }

  registerManager(data: RegisterManagerData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/manager`, data);
  }

  getAdminRegistrationRequests(params?: PaginationParams): Observable<PaginatedResult<RegistrationRequest>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<RegistrationRequest>>(`${this.apiUrl}/auth/admin/registration-requests`, { params: httpParams });
  }

  approveRegistrationRequest(requestId: string): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/admin/registration-requests/${requestId}/approve`, {});
  }

  rejectRegistrationRequest(requestId: string): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/admin/registration-requests/${requestId}/reject`, {});
  }

  checkUsernameAvailability(username: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('username', username);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-username`, { params });
  }

  checkEmailAvailability(email: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('email', email);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-email`, { params });
  }
}


===== EXISTING FILE: frontend/src/app/services/reservation.service.ts =====
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Reservation, ReservationWithDetails, CreateReservationData, ReservationFilters } from '../models/reservation.model';
import { SpaceAvailabilityResponse } from '../models/space.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class ReservationService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  createReservation(data: CreateReservationData): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations`, data);
  }

  getReservations(filters?: ReservationFilters): Observable<PaginatedResult<ReservationWithDetails>> {
    let httpParams = new HttpParams();
    if (filters) {
      if (filters.page !== undefined) httpParams = httpParams.set('page', filters.page);
      if (filters.limit !== undefined) httpParams = httpParams.set('limit', filters.limit);
      if (filters.sortBy) httpParams = httpParams.set('sortBy', filters.sortBy);
      if (filters.sortOrder) httpParams = httpParams.set('sortOrder', filters.sortOrder);
      if (filters.status) httpParams = httpParams.set('status', filters.status);
    }
    return this.http.get<PaginatedResult<ReservationWithDetails>>(`${this.apiUrl}/reservations/reservations`, { params: httpParams });
  }

  getReservation(reservationId: string): Observable<ReservationWithDetails> {
    return this.http.get<ReservationWithDetails>(`${this.apiUrl}/reservations/reservations/${reservationId}`);
  }

  getCompanyReservations(filters?: ReservationFilters): Observable<PaginatedResult<ReservationWithDetails>> {
    let httpParams = new HttpParams();
    if (filters) {
      if (filters.page !== undefined) httpParams = httpParams.set('page', filters.page);
      if (filters.limit !== undefined) httpParams = httpParams.set('limit', filters.limit);
      if (filters.sortBy) httpParams = httpParams.set('sortBy', filters.sortBy);
      if (filters.sortOrder) httpParams = httpParams.set('sortOrder', filters.sortOrder);
      if (filters.status) httpParams = httpParams.set('status', filters.status);
    }
    return this.http.get<PaginatedResult<ReservationWithDetails>>(`${this.apiUrl}/reservations/reservations/company`, { params: httpParams });
  }

  cancelReservation(reservationId: string): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations/${reservationId}/cancel`, {});
  }

  confirmReservation(reservationId: string): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations/${reservationId}/confirm`, {});
  }

  completeReservation(reservationId: string): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations/${reservationId}/complete`, {});
  }

  checkSpaceAvailability(spaceId: string, startTime: string, endTime: string): Observable<SpaceAvailabilityResponse> {
    const params = new HttpParams()
      .set('startTime', startTime)
      .set('endTime', endTime);
    return this.http.get<SpaceAvailabilityResponse>(`${this.apiUrl}/reservations/spaces/${spaceId}/availability`, { params });
  }
}


===== EXISTING FILE: frontend/src/app/services/space.service.ts =====
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Space, CreateSpaceData, UpdateSpaceData, PublicSpaceFilters } from '../models/space.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class SpaceService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  createSpace(data: CreateSpaceData): Observable<Space> {
    return this.http.post<Space>(`${this.apiUrl}/spaces/spaces`, data);
  }

  getPublicSpaces(filters?: PublicSpaceFilters): Observable<PaginatedResult<Space>> {
    let httpParams = new HttpParams();
    if (filters) {
      if (filters.page !== undefined) httpParams = httpParams.set('page', filters.page);
      if (filters.limit !== undefined) httpParams = httpParams.set('limit', filters.limit);
      if (filters.sortBy) httpParams = httpParams.set('sortBy', filters.sortBy);
      if (filters.sortOrder) httpParams = httpParams.set('sortOrder', filters.sortOrder);
      if (filters.city) httpParams = httpParams.set('city', filters.city);
      if (filters.minCapacity !== undefined) httpParams = httpParams.set('minCapacity', filters.minCapacity);
      if (filters.maxPricePerHour !== undefined) httpParams = httpParams.set('maxPricePerHour', filters.maxPricePerHour);
      if (filters.amenities?.length) {
        filters.amenities.forEach(amenity => {
          httpParams = httpParams.append('amenities', amenity);
        });
      }
    }
    return this.http.get<PaginatedResult<Space>>(`${this.apiUrl}/spaces/spaces/public`, { params: httpParams });
  }

  getSpace(spaceId: string): Observable<Space> {
    return this.http.get<Space>(`${this.apiUrl}/spaces/spaces/${spaceId}`);
  }

  getCompanySpaces(params?: PaginationParams): Observable<PaginatedResult<Space>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Space>>(`${this.apiUrl}/spaces/spaces/company`, { params: httpParams });
  }

  updateSpace(spaceId: string, data: UpdateSpaceData): Observable<Space> {
    return this.http.put<Space>(`${this.apiUrl}/spaces/spaces/${spaceId}`, data);
  }

  deleteSpace(spaceId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/spaces/spaces/${spaceId}`);
  }

  toggleSpaceActive(spaceId: string): Observable<Space> {
    return this.http.patch<Space>(`${this.apiUrl}/spaces/spaces/${spaceId}/toggle-active`, {});
  }
}


===== EXISTING FILE: frontend/src/app/services/user.service.ts =====
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { User, UserProfile, UpdateProfileData, ChangePasswordData, PublicUser } from '../models/user.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.apiUrl}/users/profile`);
  }

  updateProfile(data: UpdateProfileData): Observable<UserProfile> {
    return this.http.put<UserProfile>(`${this.apiUrl}/users/profile`, data);
  }

  changePassword(data: ChangePasswordData): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/users/profile/password`, data);
  }

  deleteProfileImage(): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/users/profile/image`);
  }

  uploadProfileImage(file: File): Observable<{ profileImage: string }> {
    const formData = new FormData();
    formData.append('image', file);
    return this.http.post<{ profileImage: string }>(`${this.apiUrl}/users/profile/image`, formData);
  }

  getAdminUsers(params?: PaginationParams): Observable<PaginatedResult<PublicUser>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<PublicUser>>(`${this.apiUrl}/users/admin/users`, { params: httpParams });
  }

  getAdminUser(userId: string): Observable<PublicUser> {
    return this.http.get<PublicUser>(`${this.apiUrl}/users/admin/users/${userId}`);
  }

  updateAdminUserStatus(userId: string, status: string): Observable<PublicUser> {
    return this.http.put<PublicUser>(`${this.apiUrl}/users/admin/users/${userId}/status`, { status });
  }

  updateAdminUserRole(userId: string, role: string): Observable<PublicUser> {
    return this.http.put<PublicUser>(`${this.apiUrl}/users/admin/users/${userId}/role`, { role });
  }

  deleteAdminUser(userId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/users/admin/users/${userId}`);
  }
}


===== EXISTING FILE: frontend/src/app/models/api.model.ts =====
export interface FieldError {
  field: string;
  message: string;
}

export interface ErrorResponse {
  status: number;
  message: string;
  fieldErrors?: FieldError[];
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface AdminStatistics {
  totalUsers: number;
  pendingRegistrations: number;
  totalCompanies: number;
  totalSpaces: number;
  usersByRole: Record<string, number>;
}

export interface ApproveRegistrationResult {
  message: string;
  user: {
    id: string;
    username: string;
    role: string;
    status: string;
  };
}

export interface RejectRegistrationResult {
  message: string;
  user: {
    id: string;
    username: string;
    role: string;
    status: string;
  };
}

export interface DeleteResult {
  message: string;
}


===== EXISTING FILE: frontend/src/app/models/auth.model.ts =====
import { UserRole } from './user-role.enum';

export interface LoginData {
  username: string;
  password: string;
}

export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    username: string;
    role: UserRole;
  };
}

export interface RefreshTokenData {
  refreshToken: string;
}

export interface RefreshTokenResult {
  accessToken: string;
  refreshToken: string;
}

export interface JwtPayload {
  sub: string;
  username: string;
  role: UserRole;
  iat?: number;
  exp?: number;
}

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

export interface MeResponse {
  id: string;
  username: string;
  role: UserRole;
}

export interface LogoutResponse {
  message: string;
}


===== EXISTING FILE: frontend/src/app/models/company.model.ts =====
export interface Company {
  id: string;
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CompanyData {
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
}

export interface CompanyManagersCount {
  count: number;
}

export interface CompanyPendingManagersCount {
  count: number;
}


===== EXISTING FILE: frontend/src/app/models/index.ts =====
export * from './user-role.enum';
export * from './user-status.enum';
export * from './registration-status.enum';
export * from './reservation-status.enum';
export * from './user.model';
export * from './company.model';
export * from './registration-request.model';
export * from './password-reset.model';
export * from './space.model';
export * from './reservation.model';
export * from './auth.model';
export * from './api.model';


===== EXISTING FILE: frontend/src/app/models/password-reset.model.ts =====
export interface PasswordResetToken {
  id: string;
  userId: string;
  expiresAt: string;
  usedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface RequestPasswordResetData {
  identifier: string;
}

export interface RequestPasswordResetResponse {
  message: string;
}

export interface VerifyPasswordResetTokenResponse {
  valid: boolean;
}

export interface ConfirmPasswordResetData {
  newPassword: string;
  confirmPassword: string;
}

export interface ConfirmPasswordResetResponse {
  message: string;
}


===== EXISTING FILE: frontend/src/app/models/registration-request.model.ts =====
import { UserRole } from './user-role.enum';
import { RegistrationStatus } from './registration-status.enum';

export interface RegistrationRequest {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
  status: RegistrationStatus;
  submittedAt: string;
  decidedAt?: string;
  decidedBy?: string;
  profileImage: string;
  createdAt: string;
  updatedAt: string;
}

export interface PendingRegistrationRequest extends RegistrationRequest {
  // Same as RegistrationRequest but status is always PENDING
}

export interface RegisterMemberData {
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  profileImage?: string;
}

export interface RegisterManagerData extends RegisterMemberData {
  companyName: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
}

export interface RegistrationResponse {
  message: string;
  request: {
    id: string;
    username: string;
    role: UserRole;
    status: RegistrationStatus;
  };
}

export interface CheckAvailabilityResponse {
  available: boolean;
}


===== EXISTING FILE: frontend/src/app/models/registration-status.enum.ts =====
export enum RegistrationStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}


===== EXISTING FILE: frontend/src/app/models/reservation-status.enum.ts =====
export enum ReservationStatus {
  PENDING = 'PENDING',
  CONFIRMED = 'CONFIRMED',
  CANCELLED = 'CANCELLED',
  COMPLETED = 'COMPLETED',
}


===== EXISTING FILE: frontend/src/app/models/reservation.model.ts =====
import { ReservationStatus } from './reservation-status.enum';

export interface Reservation {
  id: string;
  userId: string;
  spaceId: string;
  startTime: string;
  endTime: string;
  status: ReservationStatus;
  totalPrice: number;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ReservationWithDetails extends Reservation {
  user?: {
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    email: string;
    profileImage: string;
  };
  space?: {
    id: string;
    name: string;
    address: string;
    city: string;
    pricePerHour: number;
    pricePerDay: number;
  };
  company?: {
    id: string;
    name: string;
  };
}

export interface CreateReservationData {
  spaceId: string;
  startTime: string;
  endTime: string;
  notes?: string;
}

export interface ReservationFilters {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  status?: ReservationStatus;
}


===== EXISTING FILE: frontend/src/app/models/space.model.ts =====
export interface Space {
  id: string;
  name: string;
  description: string;
  address: string;
  city: string;
  capacity: number;
  amenities: string[];
  images: string[];
  companyId: string;
  pricePerHour: number;
  pricePerDay: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSpaceData {
  name: string;
  description: string;
  address: string;
  city: string;
  capacity: number;
  amenities?: string[];
  images?: string[];
  companyId: string;
  pricePerHour: number;
  pricePerDay: number;
}

export interface UpdateSpaceData {
  name?: string;
  description?: string;
  address?: string;
  city?: string;
  capacity?: number;
  amenities?: string[];
  images?: string[];
  pricePerHour?: number;
  pricePerDay?: number;
  isActive?: boolean;
}

export interface PublicSpaceFilters {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  city?: string;
  minCapacity?: number;
  maxPricePerHour?: number;
  amenities?: string[];
}

export interface SpaceAvailabilityResponse {
  available: boolean;
  conflictingReservations?: Array<{
    id: string;
    startTime: string;
    endTime: string;
  }>;
}


===== EXISTING FILE: frontend/src/app/models/user-role.enum.ts =====
export enum UserRole {
  MEMBER = 'MEMBER',
  MANAGER = 'MANAGER',
  ADMIN = 'ADMIN',
}


===== EXISTING FILE: frontend/src/app/models/user-status.enum.ts =====
export enum UserStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}


===== EXISTING FILE: frontend/src/app/models/user.model.ts =====
import { UserRole } from './user-role.enum';
import { UserStatus } from './user-status.enum';

export interface User {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  companyId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile extends User {
  // UserProfile from backend includes all User fields
  // No additional fields based on backend user.service.ts
}

export interface UpdateProfileData {
  firstName?: string;
  lastName?: string;
  phone?: string;
  email?: string;
  profileImage?: string;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface PublicUser {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  companyId?: string;
  createdAt: string;
}


===== EXISTING FILE: frontend/src/app/guards/auth.guard.ts =====
// Guards are a convenience for the user, not a security boundary.
// Anyone can edit the bundle. The server is what enforces access,
// and the specification's authorization scenarios test the server
// independently of anything the browser does.

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state): boolean | UrlTree => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  const returnUrl = state.url;
  return router.createUrlTree(['/login'], { queryParams: { returnUrl } });
};


===== EXISTING FILE: frontend/src/app/guards/guest.guard.ts =====
// Guards are a convenience for the user, not a security boundary.
// Anyone can edit the bundle. The server is what enforces access,
// and the specification's authorization scenarios test the server
// independently of anything the browser does.

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const guestGuard: CanActivateFn = (): boolean | UrlTree => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return true;
  }

  const userRole = authService.userRole();

  if (userRole === 'ADMIN') {
    return router.createUrlTree(['/admin/dashboard']);
  }

  if (userRole === 'MANAGER') {
    return router.createUrlTree(['/manager/dashboard']);
  }

  return router.createUrlTree(['/member/dashboard']);
};


===== EXISTING FILE: frontend/src/app/guards/role.guard.ts =====
// Guards are a convenience for the user, not a security boundary.
// Anyone can edit the bundle. The server is what enforces access,
// and the specification's authorization scenarios test the server
// independently of anything the browser does.

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { UserRole } from '../models/user-role.enum';

export const roleGuard: CanActivateFn = (route, state): boolean | UrlTree => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    const returnUrl = state.url;
    return router.createUrlTree(['/login'], { queryParams: { returnUrl } });
  }

  const allowedRoles = route.data['roles'] as UserRole[] | undefined;

  if (!allowedRoles || allowedRoles.length === 0) {
    return true;
  }

  const userRole = authService.userRole();

  if (userRole && allowedRoles.includes(userRole)) {
    return true;
  }

  return router.createUrlTree(['/']);
};

================= END EXISTING CODE =================

## Components already on disk

```
  frontend/src/app/components/admin-login/admin-login.css
  frontend/src/app/components/admin-login/admin-login.html
  frontend/src/app/components/admin-login/admin-login.ts
  frontend/src/app/components/forgot-password/forgot-password.css
  frontend/src/app/components/forgot-password/forgot-password.html
  frontend/src/app/components/forgot-password/forgot-password.ts
  frontend/src/app/components/login/login.css
  frontend/src/app/components/login/login.html
  frontend/src/app/components/login/login.ts
  frontend/src/app/components/register/register.css
  frontend/src/app/components/register/register.html
  frontend/src/app/components/register/register.ts
  frontend/src/app/components/reset-password/reset-password.css
  frontend/src/app/components/reset-password/reset-password.html
  frontend/src/app/components/reset-password/reset-password.ts
```

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
