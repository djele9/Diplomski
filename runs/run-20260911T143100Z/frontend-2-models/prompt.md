# Task: generate the front-end models

You are a senior Angular engineer. You answer with code and nothing else.

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

- Every file in this stage belongs under `frontend/src/app/models/`.

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

## Backend models, types and controllers — the source of truth for these shapes

These files already exist. Import from them and match their exports exactly.
Do not restate them unless you are deliberately changing one, in which case
return the complete changed file.

================ BEGIN EXISTING CODE ================


===== EXISTING FILE: backend/src/models/company.model.ts =====
import mongoose, { Document, Schema, Model } from 'mongoose';

export interface ICompany extends Document {
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
  createdAt: Date;
  updatedAt: Date;
}

const companySchema = new Schema<ICompany>(
  {
    name: {
      type: String,
      required: [true, 'Company name is required.'],
      trim: true,
      minlength: [1, 'Company name is required.'],
      maxlength: [100, 'Company name cannot exceed 100 characters.'],
    },
    headquartersAddress: {
      type: String,
      required: [true, 'Headquarters address is required.'],
      trim: true,
      minlength: [1, 'Headquarters address is required.'],
      maxlength: [200, 'Headquarters address cannot exceed 200 characters.'],
    },
    companyNumber: {
      type: String,
      required: [true, 'Company number is required.'],
      unique: true,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^\d{8}$/.test(v);
        },
        message: 'Company number must be exactly 8 digits.',
      },
    },
    taxId: {
      type: String,
      required: [true, 'Tax ID is required.'],
      unique: true,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^[1-9]\d{8}$/.test(v);
        },
        message: 'Tax ID must be exactly 9 digits and must not begin with zero.',
      },
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
  }
);

companySchema.index({ companyNumber: 1 }, { unique: true });
companySchema.index({ taxId: 1 }, { unique: true });
companySchema.index({ name: 1 });

export const Company: Model<ICompany> = mongoose.model<ICompany>('Company', companySchema);


===== EXISTING FILE: backend/src/models/index.ts =====
export { User, IUser } from './user.model';
export { Company, ICompany } from './company.model';
export { RegistrationRequest, IRegistrationRequest } from './registration-request.model';
export { PasswordResetToken, IPasswordResetToken } from './password-reset-token.model';
export { Space, ISpace } from './space.model';
export { Reservation, IReservation, ReservationStatus } from './reservation.model';


===== EXISTING FILE: backend/src/models/password-reset-token.model.ts =====
import mongoose, { Document, Schema, Model } from 'mongoose';

export interface IPasswordResetToken extends Document {
  user: mongoose.Types.ObjectId;
  token: string;
  expiresAt: Date;
  usedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

const passwordResetTokenSchema = new Schema<IPasswordResetToken>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: [true, 'User is required.'],
    },
    token: {
      type: String,
      required: [true, 'Token is required.'],
      unique: true,
      select: false,
    },
    expiresAt: {
      type: Date,
      required: [true, 'Expiration date is required.'],
    },
    usedAt: {
      type: Date,
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.token;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.token;
        return ret;
      },
    },
  }
);

passwordResetTokenSchema.index({ token: 1 }, { unique: true });
passwordResetTokenSchema.index({ user: 1, expiresAt: 1 });
passwordResetTokenSchema.index({ expiresAt: 1 }, { expireAfterSeconds: 0 });

export const PasswordResetToken: Model<IPasswordResetToken> = mongoose.model<IPasswordResetToken>(
  'PasswordResetToken',
  passwordResetTokenSchema
);


===== EXISTING FILE: backend/src/models/registration-request.model.ts =====
import mongoose, { Document, Schema, Model } from 'mongoose';
import { UserRole, RegistrationStatus } from '../types';

export interface IRegistrationRequest extends Document {
  username: string;
  passwordHash: string;
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
  submittedAt: Date;
  decidedAt?: Date;
  decidedBy?: mongoose.Types.ObjectId;
  profileImage: string;
  createdAt: Date;
  updatedAt: Date;
}

const registrationRequestSchema = new Schema<IRegistrationRequest>(
  {
    username: {
      type: String,
      required: [true, 'Username is required.'],
      unique: true,
      trim: true,
      minlength: [1, 'Username is required.'],
      maxlength: [50, 'Username cannot exceed 50 characters.'],
    },
    passwordHash: {
      type: String,
      required: [true, 'Password is required.'],
      select: false,
    },
    firstName: {
      type: String,
      required: [true, 'First name is required.'],
      trim: true,
      minlength: [1, 'First name is required.'],
      maxlength: [50, 'First name cannot exceed 50 characters.'],
    },
    lastName: {
      type: String,
      required: [true, 'Last name is required.'],
      trim: true,
      minlength: [1, 'Last name is required.'],
      maxlength: [50, 'Last name cannot exceed 50 characters.'],
    },
    phone: {
      type: String,
      required: [true, 'Contact phone is required.'],
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^\+?[0-9\s\-()]{7,20}$/.test(v);
        },
        message: 'Enter a valid contact phone number.',
      },
    },
    email: {
      type: String,
      required: [true, 'Email address is required.'],
      unique: true,
      trim: true,
      lowercase: true,
      validate: {
        validator: function (v: string): boolean {
          return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
        },
        message: 'Enter a valid email address.',
      },
    },
    role: {
      type: String,
      enum: {
        values: Object.values(UserRole),
        message: 'Invalid role.',
      },
      required: [true, 'Role is required.'],
      default: UserRole.MEMBER,
    },
    companyName: {
      type: String,
      trim: true,
      maxlength: [100, 'Company name cannot exceed 100 characters.'],
    },
    headquartersAddress: {
      type: String,
      trim: true,
      maxlength: [200, 'Headquarters address cannot exceed 200 characters.'],
    },
    companyNumber: {
      type: String,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return !v || /^\d{8}$/.test(v);
        },
        message: 'Company number must be exactly 8 digits.',
      },
    },
    taxId: {
      type: String,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return !v || /^[1-9]\d{8}$/.test(v);
        },
        message: 'Tax ID must be exactly 9 digits and must not begin with zero.',
      },
    },
    status: {
      type: String,
      enum: {
        values: Object.values(RegistrationStatus),
        message: 'Invalid registration status.',
      },
      required: [true, 'Status is required.'],
      default: RegistrationStatus.PENDING,
    },
    submittedAt: {
      type: Date,
      required: true,
      default: Date.now,
    },
    decidedAt: {
      type: Date,
    },
    decidedBy: {
      type: Schema.Types.ObjectId,
      ref: 'User',
    },
    profileImage: {
      type: String,
      required: true,
      default: 'default-avatar.png',
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
  }
);

registrationRequestSchema.index({ username: 1 }, { unique: true });
registrationRequestSchema.index({ email: 1 }, { unique: true });
registrationRequestSchema.index({ status: 1, submittedAt: 1 });
registrationRequestSchema.index({ role: 1, status: 1 });

export const RegistrationRequest: Model<IRegistrationRequest> = mongoose.model<IRegistrationRequest>(
  'RegistrationRequest',
  registrationRequestSchema
);


===== EXISTING FILE: backend/src/models/reservation.model.ts =====
import mongoose, { Document, Schema, Model } from 'mongoose';

export enum ReservationStatus {
  PENDING = 'PENDING',
  CONFIRMED = 'CONFIRMED',
  CANCELLED = 'CANCELLED',
  COMPLETED = 'COMPLETED',
}

export interface IReservation extends Document {
  user: mongoose.Types.ObjectId;
  space: mongoose.Types.ObjectId;
  startTime: Date;
  endTime: Date;
  status: ReservationStatus;
  totalPrice: number;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

const reservationSchema = new Schema<IReservation>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: [true, 'User is required.'],
    },
    space: {
      type: Schema.Types.ObjectId,
      ref: 'Space',
      required: [true, 'Space is required.'],
    },
    startTime: {
      type: Date,
      required: [true, 'Start time is required.'],
    },
    endTime: {
      type: Date,
      required: [true, 'End time is required.'],
    },
    status: {
      type: String,
      enum: {
        values: Object.values(ReservationStatus),
        message: 'Invalid reservation status.',
      },
      required: [true, 'Status is required.'],
      default: ReservationStatus.PENDING,
    },
    totalPrice: {
      type: Number,
      required: [true, 'Total price is required.'],
      min: [0, 'Total price cannot be negative.'],
    },
    notes: {
      type: String,
      trim: true,
      maxlength: [1000, 'Notes cannot exceed 1000 characters.'],
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
  }
);

reservationSchema.index({ user: 1, startTime: -1 });
reservationSchema.index({ space: 1, startTime: 1, endTime: 1 });
reservationSchema.index({ status: 1 });
reservationSchema.index({ startTime: 1, endTime: 1 });

reservationSchema.pre('validate', function (next): void {
  if (this.startTime && this.endTime && this.startTime >= this.endTime) {
    this.invalidate('endTime', 'End time must be after start time.');
  }
  next();
});

export const Reservation: Model<IReservation> = mongoose.model<IReservation>('Reservation', reservationSchema);


===== EXISTING FILE: backend/src/models/space.model.ts =====
import mongoose, { Document, Schema, Model } from 'mongoose';

export interface ISpace extends Document {
  name: string;
  description: string;
  address: string;
  city: string;
  capacity: number;
  amenities: string[];
  images: string[];
  company: mongoose.Types.ObjectId;
  pricePerHour: number;
  pricePerDay: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

const spaceSchema = new Schema<ISpace>(
  {
    name: {
      type: String,
      required: [true, 'Space name is required.'],
      trim: true,
      minlength: [1, 'Space name is required.'],
      maxlength: [100, 'Space name cannot exceed 100 characters.'],
    },
    description: {
      type: String,
      required: [true, 'Description is required.'],
      trim: true,
      minlength: [1, 'Description is required.'],
      maxlength: [2000, 'Description cannot exceed 2000 characters.'],
    },
    address: {
      type: String,
      required: [true, 'Address is required.'],
      trim: true,
      minlength: [1, 'Address is required.'],
      maxlength: [200, 'Address cannot exceed 200 characters.'],
    },
    city: {
      type: String,
      required: [true, 'City is required.'],
      trim: true,
      minlength: [1, 'City is required.'],
      maxlength: [100, 'City cannot exceed 100 characters.'],
    },
    capacity: {
      type: Number,
      required: [true, 'Capacity is required.'],
      min: [1, 'Capacity must be at least 1.'],
      max: [1000, 'Capacity cannot exceed 1000.'],
    },
    amenities: {
      type: [String],
      default: [],
      validate: {
        validator: function (v: string[]): boolean {
          return v.length <= 50;
        },
        message: 'Cannot have more than 50 amenities.',
      },
    },
    images: {
      type: [String],
      default: [],
      validate: {
        validator: function (v: string[]): boolean {
          return v.length <= 20;
        },
        message: 'Cannot have more than 20 images.',
      },
    },
    company: {
      type: Schema.Types.ObjectId,
      ref: 'Company',
      required: [true, 'Company is required.'],
    },
    pricePerHour: {
      type: Number,
      required: [true, 'Hourly price is required.'],
      min: [0, 'Price cannot be negative.'],
      max: [100000, 'Price cannot exceed 100000.'],
    },
    pricePerDay: {
      type: Number,
      required: [true, 'Daily price is required.'],
      min: [0, 'Price cannot be negative.'],
      max: [1000000, 'Price cannot exceed 1000000.'],
    },
    isActive: {
      type: Boolean,
      default: true,
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
  }
);

spaceSchema.index({ company: 1, isActive: 1 });
spaceSchema.index({ city: 1, isActive: 1 });
spaceSchema.index({ name: 'text', description: 'text', address: 'text' });
spaceSchema.index({ pricePerHour: 1 });
spaceSchema.index({ capacity: 1 });

export const Space: Model<ISpace> = mongoose.model<ISpace>('Space', spaceSchema);


===== EXISTING FILE: backend/src/models/user.model.ts =====
import mongoose, { Document, Schema, Model } from 'mongoose';
import { UserRole, UserStatus } from '../types';

export interface IUser extends Document {
  username: string;
  passwordHash: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  company?: mongoose.Types.ObjectId;
  createdAt: Date;
  updatedAt: Date;
}

const userSchema = new Schema<IUser>(
  {
    username: {
      type: String,
      required: [true, 'Username is required.'],
      unique: true,
      trim: true,
      minlength: [1, 'Username is required.'],
      maxlength: [50, 'Username cannot exceed 50 characters.'],
    },
    passwordHash: {
      type: String,
      required: [true, 'Password is required.'],
      select: false,
    },
    firstName: {
      type: String,
      required: [true, 'First name is required.'],
      trim: true,
      minlength: [1, 'First name is required.'],
      maxlength: [50, 'First name cannot exceed 50 characters.'],
    },
    lastName: {
      type: String,
      required: [true, 'Last name is required.'],
      trim: true,
      minlength: [1, 'Last name is required.'],
      maxlength: [50, 'Last name cannot exceed 50 characters.'],
    },
    phone: {
      type: String,
      required: [true, 'Contact phone is required.'],
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^\+?[0-9\s\-()]{7,20}$/.test(v);
        },
        message: 'Enter a valid contact phone number.',
      },
    },
    email: {
      type: String,
      required: [true, 'Email address is required.'],
      unique: true,
      trim: true,
      lowercase: true,
      validate: {
        validator: function (v: string): boolean {
          return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
        },
        message: 'Enter a valid email address.',
      },
    },
    role: {
      type: String,
      enum: {
        values: Object.values(UserRole),
        message: 'Invalid role.',
      },
      required: [true, 'Role is required.'],
      default: UserRole.MEMBER,
    },
    status: {
      type: String,
      enum: {
        values: Object.values(UserStatus),
        message: 'Invalid status.',
      },
      required: [true, 'Status is required.'],
      default: UserStatus.PENDING,
    },
    profileImage: {
      type: String,
      required: true,
      default: 'default-avatar.png',
    },
    company: {
      type: Schema.Types.ObjectId,
      ref: 'Company',
      default: null,
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
  }
);

userSchema.index({ username: 1 }, { unique: true });
userSchema.index({ email: 1 }, { unique: true });
userSchema.index({ role: 1, status: 1 });
userSchema.index({ company: 1 });

export const User: Model<IUser> = mongoose.model<IUser>('User', userSchema);


===== EXISTING FILE: backend/src/types/express.d.ts =====
import { Role } from '@prisma/client';

declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        username: string;
        email: string;
        role: Role;
        companyId?: string;
      };
    }
  }
}


===== EXISTING FILE: backend/src/types/index.ts =====
export enum UserRole {
  MEMBER = 'MEMBER',
  MANAGER = 'MANAGER',
  ADMIN = 'ADMIN',
}

export enum UserStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}

export enum RegistrationStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
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

export interface AuthenticatedRequest extends Express.Request {
  user?: JwtPayload;
}

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


===== EXISTING FILE: backend/src/controllers/admin.controller.ts =====
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { adminService, AdminStatistics } from '../services/admin.service';
import { registrationService, PendingRegistrationRequest } from '../services/registration.service';
import { userService, UserProfile } from '../services/user.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole, UserStatus, RegistrationStatus } from '../types';

export class AdminController {
  getStatistics = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view statistics.');
    }
    const statistics: AdminStatistics = await adminService.getStatistics();
    res.status(200).json(statistics);
  });

  getPendingRegistrations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view pending registrations.');
    }
    const requests: PendingRegistrationRequest[] = await registrationService.getPendingRequests();
    res.status(200).json({ data: requests });
  });

  approveRegistration = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can approve registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.approveRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  rejectRegistration = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can reject registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.rejectRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  getUsers = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list users.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const role = req.query.role as UserRole | undefined;
    const status = req.query.status as UserStatus | undefined;

    const result = await adminService.getAllUsers(page, limit, sortBy, sortOrder, role, status);
    res.status(200).json(result);
  });

  getUserById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view user details.');
    }
    const { userId } = req.params as { userId: string };
    const profile: UserProfile = await userService.getUserById(userId);
    res.status(200).json(profile);
  });

  updateUserStatus = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user status.');
    }
    const { userId } = req.params as { userId: string };
    const { status } = req.body as { status: UserStatus };
    const result = await adminService.updateUserStatus(userId, status, req.user.sub);
    res.status(200).json(result);
  });

  updateUserRole = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user role.');
    }
    const { userId } = req.params as { userId: string };
    const { role } = req.body as { role: UserRole };
    const result = await adminService.updateUserRole(userId, role, req.user.sub);
    res.status(200).json(result);
  });

  deleteUser = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can delete users.');
    }
    const { userId } = req.params as { userId: string };
    const result = await adminService.deleteUser(userId, req.user.sub);
    res.status(200).json(result);
  });

  getCompanies = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list companies.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';

    const result = await adminService.getAllCompanies(page, limit, sortBy, sortOrder);
    res.status(200).json(result);
  });

  getSpaces = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list all spaces.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const isActive = req.query.isActive !== undefined ? req.query.isActive === 'true' : undefined;

    const result = await adminService.getAllSpaces(page, limit, sortBy, sortOrder, isActive);
    res.status(200).json(result);
  });

  getReservations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list all reservations.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const status = req.query.status as string | undefined;

    const result = await adminService.getAllReservations(page, limit, sortBy, sortOrder, status as any);
    res.status(200).json(result);
  });
}

export const adminController = new AdminController();


===== EXISTING FILE: backend/src/controllers/adminController.ts =====
import { Request, Response, NextFunction } from 'express';
import { PrismaClient } from '@prisma/client';
import { authenticate, requireAdmin } from '@/middleware/auth';
import { AppError } from '@/utils/errors';

const prisma = new PrismaClient();

export async function getAllUsers(req: Request, res: Response, next: NextFunction) {
  try {
    const users = await prisma.user.findMany({
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        username: true,
        email: true,
        firstName: true,
        lastName: true,
        phone: true,
        role: true,
        status: true,
        profileImage: true,
        companyId: true,
        createdAt: true,
        updatedAt: true,
      },
    });
    res.json(users);
  } catch (err) {
    next(err);
  }
}

export async function getAdminStats(req: Request, res: Response, next: NextFunction) {
  try {
    const [totalUsers, pendingRegistrations, totalCompanies, totalSpaces] = await Promise.all([
      prisma.user.count({ where: { status: 'APPROVED' } }),
      prisma.registrationRequest.count({ where: { status: 'PENDING' } }),
      prisma.company.count(),
      prisma.space.count(),
    ]);

    const usersByRole = await prisma.user.groupBy({
      by: ['role'],
      where: { status: 'APPROVED' },
      _count: true,
    });

    res.json({
      totalUsers,
      pendingRegistrations,
      totalCompanies,
      totalSpaces,
      usersByRole: usersByRole.reduce((acc, curr) => {
        acc[curr.role] = curr._count;
        return acc;
      }, {} as Record<string, number>),
    });
  } catch (err) {
    next(err);
  }
}

export async function getPendingSpaces(req: Request, res: Response, next: NextFunction) {
  try {
    // This would be for space approval if we had that feature
    res.json([]);
  } catch (err) {
    next(err);
  }
}


===== EXISTING FILE: backend/src/controllers/auth.controller.ts =====
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { authService, LoginResult } from '../services/auth.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';

export class AuthController {
  login = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { username, password } = req.body as { username: string; password: string };
    const result: LoginResult = await authService.login(username, password, false);
    res.status(200).json(result);
  });

  adminLogin = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { username, password } = req.body as { username: string; password: string };
    const result: LoginResult = await authService.login(username, password, true);
    res.status(200).json(result);
  });

  requestPasswordReset = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { identifier } = req.body as { identifier: string };
    const result = await authService.requestPasswordReset(identifier);
    res.status(200).json(result);
  });

  verifyPasswordResetToken = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { token } = req.params as { token: string };
    const result = await authService.verifyPasswordResetToken(token);
    res.status(200).json({ valid: result.valid });
  });

  confirmPasswordReset = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { token } = req.params as { token: string };
    const { newPassword, confirmPassword } = req.body as { newPassword: string; confirmPassword: string };
    const result = await authService.confirmPasswordReset(token, newPassword, confirmPassword);
    res.status(200).json(result);
  });

  refreshAccessToken = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { refreshToken } = req.body as { refreshToken: string };
    if (!refreshToken) {
      throw AppError.badRequest('Refresh token is required.');
    }
    const result = await authService.refreshAccessToken(refreshToken);
    res.status(200).json(result);
  });

  logout = asyncHandler(async (_req: Request, res: Response, _next: NextFunction): Promise<void> => {
    res.status(200).json({ message: 'Signed out successfully.' });
  });

  getMe = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    res.status(200).json({
      id: req.user.sub,
      username: req.user.username,
      role: req.user.role,
    });
  });
}

export const authController = new AuthController();


===== EXISTING FILE: backend/src/controllers/authController.ts =====
import { Request, Response, NextFunction } from 'express';
import { body } from 'express-validator';
import { login, createRegistrationRequest, getPendingRegistrations, approveRegistrationRequest, rejectRegistrationRequest } from '@/services/userService';
import { requestPasswordReset, validateResetToken, resetPassword } from '@/services/passwordResetService';
import { validate } from '@/middleware/validation';
import { authenticate, requireAdmin } from '@/middleware/auth';
import { AppError } from '@/utils/errors';

export const loginValidation = validate([
  body('username').isString().notEmpty(),
  body('password').isString().notEmpty(),
]);

export async function publicLogin(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password } = req.body;
    const { token, user } = await login(username, password, false);
    res.json({ token, user: { username: user.username, role: user.role } });
  } catch (err) {
    next(err);
  }
}

export async function adminLogin(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password } = req.body;
    const { token, user } = await login(username, password, true);
    res.json({ token, user: { username: user.username, role: user.role } });
  } catch (err) {
    next(err);
  }
}

export const registerMemberValidation = validate([
  body('username').isString().isLength({ min: 3, max: 50 }),
  body('password').isString().isLength({ min: 8, max: 12 }),
  body('firstName').isString().notEmpty(),
  body('lastName').isString().notEmpty(),
  body('phone').isString().notEmpty(),
  body('email').isEmail(),
]);

export async function registerMember(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password, firstName, lastName, phone, email } = req.body;
    const profileImage = req.file ? req.file.filename : undefined;
    const result = await createRegistrationRequest({
      username,
      email,
      password,
      firstName,
      lastName,
      phone,
      role: 'MEMBER',
      profileImage,
    });
    res.status(201).json(result);
  } catch (err) {
    next(err);
  }
}

export const registerManagerValidation = validate([
  body('username').isString().isLength({ min: 3, max: 50 }),
  body('password').isString().isLength({ min: 8, max: 12 }),
  body('firstName').isString().notEmpty(),
  body('lastName').isString().notEmpty(),
  body('phone').isString().notEmpty(),
  body('email').isEmail(),
  body('companyName').isString().notEmpty(),
  body('headquartersAddress').isString().notEmpty(),
  body('companyNumber').matches(/^\d{8}$/),
  body('taxId').matches(/^[1-9]\d{8}$/),
]);

export async function registerManager(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password, firstName, lastName, phone, email, companyName, headquartersAddress, companyNumber, taxId } = req.body;
    const profileImage = req.file ? req.file.filename : undefined;
    const result = await createRegistrationRequest({
      username,
      email,
      password,
      firstName,
      lastName,
      phone,
      role: 'MANAGER',
      companyName,
      headquartersAddress,
      companyNumber,
      taxId,
      profileImage,
    });
    res.status(201).json(result);
  } catch (err) {
    next(err);
  }
}

export const forgotPasswordValidation = validate([
  body('identifier').isString().notEmpty(),
]);

export async function forgotPassword(req: Request, res: Response, next: NextFunction) {
  try {
    const { identifier } = req.body;
    const result = await requestPasswordReset(identifier);
    res.json(result);
  } catch (err) {
    next(err);
  }
}

export async function getResetTokenStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const { token } = req.params;
    await validateResetToken(token);
    res.json({ valid: true });
  } catch (err) {
    next(err);
  }
}

export const resetPasswordValidation = validate([
  body('token').isUUID(),
  body('password').isString().isLength({ min: 8, max: 12 }),
  body('confirmPassword').isString().isLength({ min: 8, max: 12 }),
]);

export async function resetPasswordHandler(req: Request, res: Response, next: NextFunction) {
  try {
    const { token, password } = req.body;
    const result = await resetPassword(token, password);
    res.json(result);
  } catch (err) {
    next(err);
  }
}

export async function getPendingRegistrationsHandler(req: Request, res: Response, next: NextFunction) {
  try {
    const requests = await getPendingRegistrations();
    res.json(requests);
  } catch (err) {
    next(err);
  }
}

export const approveValidation = validate([
  body('username').isString().notEmpty(),
]);

export async function approveRegistration(req: Request, res: Response, next: NextFunction) {
  try {
    const { username } = req.body;
    await approveRegistrationRequest(username, req.user!.id);
    res.json({ message: 'Registration approved' });
  } catch (err) {
    next(err);
  }
}

export async function rejectRegistration(req: Request, res: Response, next: NextFunction) {
  try {
    const { username } = req.body;
    await rejectRegistrationRequest(username, req.user!.id);
    res.json({ message: 'Registration rejected' });
  } catch (err) {
    next(err);
  }
}

export async function getCurrentUser(req: Request, res: Response, next: NextFunction) {
  try {
    res.json({ user: req.user });
  } catch (err) {
    next(err);
  }
}

export async function logout(req: Response) {
  // Client-side token removal, but we can also blacklist tokens here if needed
  res.json({ message: 'Logged out successfully' });
}


===== EXISTING FILE: backend/src/controllers/company.controller.ts =====
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { companyService, CompanyData } from '../services/company.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class CompanyController {
  createCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'ADMIN' && req.user.role !== 'MANAGER')) {
      throw AppError.forbidden('Only administrators and space managers can create companies.');
    }
    const data = req.body as CompanyData;
    const company = await companyService.createCompany(data);
    res.status(201).json(company);
  });

  getCompanyById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const { companyId } = req.params as { companyId: string };
    const company = await companyService.getCompanyById(companyId);
    res.status(200).json(company);
  });

  getCompanies = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list all companies.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';

    const result = await companyService.getCompanies(page, limit, sortBy, sortOrder);
    res.status(200).json(result);
  });

  updateCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update companies.');
    }
    const { companyId } = req.params as { companyId: string };
    const data = req.body as Partial<CompanyData>;
    const company = await companyService.updateCompany(companyId, data);
    res.status(200).json(company);
  });

  deleteCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can delete companies.');
    }
    const { companyId } = req.params as { companyId: string };
    const result = await companyService.deleteCompany(companyId);
    res.status(200).json(result);
  });

  getCompanyManagersCount = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'ADMIN' && req.user.role !== 'MANAGER')) {
      throw AppError.forbidden('Insufficient permissions.');
    }
    const { companyId } = req.params as { companyId: string };
    const count = await companyService.getCompanyManagersCount(companyId);
    res.status(200).json({ count });
  });

  getCompanyPendingManagersCount = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view pending manager counts.');
    }
    const { companyNumber } = req.params as { companyNumber: string };
    const count = await companyService.getCompanyPendingManagersCount(companyNumber);
    res.status(200).json({ count });
  });
}

export const companyController = new CompanyController();


===== EXISTING FILE: backend/src/controllers/imageController.ts =====
import { Request, Response, NextFunction } from 'express';
import multer from 'multer';
import { validateAndProcessImage, getImagePath, getDefaultImagePath } from '@/services/imageService';
import { authenticate } from '@/middleware/auth';
import { AppError } from '@/utils/errors';
import fs from 'fs/promises';
import path from 'path';

// Configure multer for memory storage (we process with sharp)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
  fileFilter: (_req, file, cb) => {
    if (file.mimetype === 'image/jpeg' || file.mimetype === 'image/png') {
      cb(null, true);
    } else {
      cb(new AppError(415, 'Only JPG and PNG images are accepted.', 'UNSUPPORTED_MEDIA_TYPE'));
    }
  },
});

export const uploadProfileImage = upload.single('profileImage');

export async function handleProfileImageUpload(req: Request, res: Response, next: NextFunction) {
  try {
    if (!req.file) {
      throw new AppError(400, 'No file uploaded');
    }
    if (!req.user) {
      throw new AppError(401, 'Authentication required');
    }
    const filename = await validateAndProcessImage(req.file, req.user.id);
    res.json({ filename, message: 'Profile image uploaded successfully' });
  } catch (err) {
    next(err);
  }
}

export async function serveProfileImage(req: Request, res: Response, next: NextFunction) {
  try {
    const { filename } = req.params;
    const filepath = await getImagePath(filename);
    
    // Check if file exists
    try {
      await fs.access(filepath);
    } catch {
      // Serve default image
      const defaultPath = getDefaultImagePath();
      return res.sendFile(defaultPath);
    }
    
    res.sendFile(filepath);
  } catch (err) {
    next(err);
  }
}

export async function serveDefaultImage(_req: Request, res: Response, next: NextFunction) {
  try {
    const defaultPath = getDefaultImagePath();
    res.sendFile(defaultPath);
  } catch (err) {
    next(err);
  }
}


===== EXISTING FILE: backend/src/controllers/index.ts =====
export { authController, AuthController } from './auth.controller';
export { registrationController, RegistrationController } from './registration.controller';
export { userController, UserController } from './user.controller';
export { companyController, CompanyController } from './company.controller';
export { adminController, AdminController } from './admin.controller';
export { spaceController, SpaceController } from './space.controller';
export { reservationController, ReservationController } from './reservation.controller';


===== EXISTING FILE: backend/src/controllers/registration.controller.ts =====
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { authService, RegisterMemberData, RegisterManagerData } from '../services/auth.service';
import { registrationService, PendingRegistrationRequest } from '../services/registration.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class RegistrationController {
  registerMember = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const data = req.body as RegisterMemberData;
    data.profileImage = req.file ? req.file.filename : undefined;
    const request = await authService.registerMember(data);
    res.status(201).json({
      message: 'Your registration request has been submitted and is awaiting approval.',
      request: {
        id: request._id.toString(),
        username: request.username,
        role: request.role,
        status: request.status,
      },
    });
  });

  registerManager = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const data = req.body as RegisterManagerData;
    data.profileImage = req.file ? req.file.filename : undefined;
    const request = await authService.registerManager(data);
    res.status(201).json({
      message: 'Your registration request has been submitted and is awaiting approval.',
      request: {
        id: request._id.toString(),
        username: request.username,
        role: request.role,
        status: request.status,
      },
    });
  });

  getPendingRequests = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view pending registrations.');
    }
    const requests: PendingRegistrationRequest[] = await registrationService.getPendingRequests();
    res.status(200).json({ data: requests });
  });

  approveRequest = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can approve registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.approveRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  rejectRequest = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can reject registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.rejectRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  checkUsernameAvailability = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { username } = req.query as { username: string };
    if (!username) {
      throw AppError.badRequest('Username query parameter is required.');
    }
    const available = await registrationService.isUsernameAvailable(username);
    res.status(200).json({ available });
  });

  checkEmailAvailability = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { email } = req.query as { email: string };
    if (!email) {
      throw AppError.badRequest('Email query parameter is required.');
    }
    const available = await registrationService.isEmailAvailable(email);
    res.status(200).json({ available });
  });
}

export const registrationController = new RegistrationController();


===== EXISTING FILE: backend/src/controllers/reservation.controller.ts =====
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { reservationService, CreateReservationData, ReservationWithDetails } from '../services/reservation.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole, ReservationStatus } from '../types';

export class ReservationController {
  createReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const data = req.body as CreateReservationData;
    const reservation: ReservationWithDetails = await reservationService.createReservation(req.user.sub, data);
    res.status(201).json(reservation);
  });

  getReservationById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const { reservationId } = req.params as { reservationId: string };
    const reservation: ReservationWithDetails = await reservationService.getReservationById(reservationId, req.user.sub, req.user.role);
    res.status(200).json(reservation);
  });

  getUserReservations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'startTime';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const status = req.query.status as ReservationStatus | undefined;

    const result = await reservationService.getUserReservations(req.user.sub, page, limit, sortBy, sortOrder, status);
    res.status(200).json(result);
  });

  getCompanyReservations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can view company reservations.');
    }
    const companyId = req.user.role === 'ADMIN' 
      ? (req.query.companyId as string) 
      : req.user.sub;
    
    if (!companyId) {
      throw AppError.badRequest('Company ID is required.');
    }

    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'startTime';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const status = req.query.status as ReservationStatus | undefined;

    const result = await reservationService.getCompanyReservations(companyId, page, limit, sortBy, sortOrder, status);
    res.status(200).json(result);
  });

  cancelReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const { reservationId } = req.params as { reservationId: string };
    const result = await reservationService.cancelReservation(reservationId, req.user.sub, req.user.role);
    res.status(200).json(result);
  });

  confirmReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can confirm reservations.');
    }
    const { reservationId } = req.params as { reservationId: string };
    const result = await reservationService.confirmReservation(reservationId, req.user.sub);
    res.status(200).json(result);
  });

  completeReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can complete reservations.');
    }
    const { reservationId } = req.params as { reservationId: string };
    const result = await reservationService.completeReservation(reservationId, req.user.sub);
    res.status(200).json(result);
  });

  checkAvailability = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { spaceId } = req.params as { spaceId: string };
    const { startTime, endTime } = req.query as { startTime: string; endTime: string };
    
    if (!startTime || !endTime) {
      throw AppError.badRequest('startTime and endTime query parameters are required.');
    }

    const result = await reservationService.checkAvailability(spaceId, new Date(startTime), new Date(endTime));
    res.status(200).json(result);
  });
}

export const reservationController = new ReservationController();


===== EXISTING FILE: backend/src/controllers/space.controller.ts =====
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { spaceService, CreateSpaceData, UpdateSpaceData } from '../services/space.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class SpaceController {
  createSpace = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can create spaces.');
    }
    const data = req.body as CreateSpaceData;
    data.companyId = req.user.role === 'ADMIN' ? data.companyId : req.user.sub;
    const space = await spaceService.createSpace(data, req.user.sub);
    res.status(201).json(space);
  });

  getSpaceById = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { spaceId } = req.params as { spaceId: string };
    const space = await spaceService.getSpaceById(spaceId);
    res.status(200).json(space);
  });

  getSpacesByCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can list company spaces.');
    }
    const companyId = req.user.role === 'ADMIN' 
      ? (req.query.companyId as string) 
      : req.user.sub;
    
    if (!companyId) {
      throw AppError.badRequest('Company ID is required.');
    }

    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const isActive = req.query.isActive !== undefined ? req.query.isActive === 'true' : undefined;

    const result = await spaceService.getSpacesByCompany(companyId, page, limit, sortBy, sortOrder, isActive);
    res.status(200).json(result);
  });

  getPublicSpaces = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const city = req.query.city as string | undefined;
    const minCapacity = req.query.minCapacity ? parseInt(req.query.minCapacity as string) : undefined;
    const maxPricePerHour = req.query.maxPricePerHour ? parseFloat(req.query.maxPricePerHour as string) : undefined;
    const amenities = req.query.amenities ? (req.query.amenities as string).split(',') : undefined;

    const result = await spaceService.getPublicSpaces(page, limit, sortBy, sortOrder, city, minCapacity, maxPricePerHour, amenities);
    res.status(200).json(result);
  });

  updateSpace = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can update spaces.');
    }
    const { spaceId } = req.params as { spaceId: string };
    const data = req.body as UpdateSpaceData;
    const space = await spaceService.updateSpace(spaceId, data, req.user.sub);
    res.status(200).json(space);
  });

  deleteSpace = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can delete spaces.');
    }
    const { spaceId } = req.params as { spaceId: string };
    const result = await spaceService.deleteSpace(spaceId, req.user.sub);
    res.status(200).json(result);
  });

  toggleSpaceActive = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can toggle space status.');
    }
    const { spaceId } = req.params as { spaceId: string };
    const space = await spaceService.toggleSpaceActive(spaceId, req.user.sub);
    res.status(200).json(space);
  });
}

export const spaceController = new SpaceController();


===== EXISTING FILE: backend/src/controllers/user.controller.ts =====
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { userService, UpdateProfileData, ChangePasswordData, UserProfile } from '../services/user.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class UserController {
  getProfile = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const profile: UserProfile = await userService.getProfile(req.user.sub);
    res.status(200).json(profile);
  });

  updateProfile = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const data = req.body as UpdateProfileData;
    if (req.file) {
      data.profileImage = req.file.filename;
    }
    const profile: UserProfile = await userService.updateProfile(req.user.sub, data);
    res.status(200).json(profile);
  });

  changePassword = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const data = req.body as ChangePasswordData;
    const result = await userService.changePassword(req.user.sub, data);
    res.status(200).json(result);
  });

  deleteProfileImage = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const result = await userService.deleteProfileImage(req.user.sub);
    res.status(200).json(result);
  });

  uploadProfileImage = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    if (!req.file) {
      throw AppError.badRequest('No image file provided.');
    }
    const profile: UserProfile = await userService.updateProfile(req.user.sub, { profileImage: req.file.filename });
    res.status(200).json({ profileImage: profile.profileImage });
  });

  getUsers = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list users.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const role = req.query.role as UserRole | undefined;
    const status = req.query.status as string | undefined;

    const result = await userService.getUsers(page, limit, sortBy, sortOrder, role, status as any);
    res.status(200).json(result);
  });

  getUserById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view user details.');
    }
    const { userId } = req.params as { userId: string };
    const profile: UserProfile = await userService.getUserById(userId);
    res.status(200).json(profile);
  });

  updateUserStatus = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user status.');
    }
    const { userId } = req.params as { userId: string };
    const { status } = req.body as { status: string };
    const profile: UserProfile = await userService.updateUserStatus(userId, status as any, req.user.sub);
    res.status(200).json(profile);
  });

  updateUserRole = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user role.');
    }
    const { userId } = req.params as { userId: string };
    const { role } = req.body as { role: UserRole };
    const profile: UserProfile = await userService.updateUserRole(userId, role, req.user.sub);
    res.status(200).json(profile);
  });

  deleteUser = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can delete users.');
    }
    const { userId } = req.params as { userId: string };
    const result = await userService.deleteUser(userId, req.user.sub);
    res.status(200).json(result);
  });
}

export const userController = new UserController();

================= END EXISTING CODE =================

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
