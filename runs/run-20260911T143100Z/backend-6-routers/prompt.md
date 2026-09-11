# Task: generate the routers

You are a senior backend engineer. You answer with code and nothing else.

## Technology, fixed — do not substitute

- Node.js 22.21.0
- Express 4.x
- TypeScript 5.x, compiled with `tsc`
- Mongoose 8.x
- Database MongoDB
- Module system: **commonjs**

Because the project is CommonJS, relative imports carry **no file extension**:
write `import { User } from '../models/user.model'`, never `'../models/user.model.js'`.

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

- Every file in this stage belongs under `backend/src/routers/`.

## The specification

What follows is every `.feature` file for this application. Each `===== name =====`
header begins a separate Gherkin file; they all describe the same system. They
are the complete and authoritative requirements.

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

## Existing code — middlewares and controllers

These files already exist. Import from them, match their exports exactly, and
do not restate them in your answer unless you are deliberately changing one —
in which case return the complete changed file.

================ BEGIN EXISTING CODE ================


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


===== EXISTING FILE: backend/src/middlewares/auth.middleware.ts =====
import { Request, Response, NextFunction } from 'express';
import { verifyAccessToken, decodeToken } from '../utils/token';
import { AppError, isAppError } from '../utils/AppError';
import { User } from '../models/user.model';
import { JwtPayload, AuthenticatedRequest } from '../types';

export async function authenticate(
  req: Request,
  _res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw AppError.unauthorized('Missing or invalid Authorization header');
    }

    const token = authHeader.slice(7).trim();

    if (!token) {
      throw AppError.unauthorized('Missing token');
    }

    let payload: JwtPayload;

    try {
      payload = verifyAccessToken(token);
    } catch (err) {
      if (err instanceof jwt.TokenExpiredError) {
        throw AppError.unauthorized('Token has expired');
      }
      if (err instanceof jwt.JsonWebTokenError) {
        throw AppError.unauthorized('Invalid token');
      }
      throw AppError.unauthorized('Invalid token');
    }

    const user = await User.findById(payload.sub).select('+passwordHash').lean();

    if (!user) {
      throw AppError.unauthorized('User no longer exists');
    }

    if (user.status !== 'APPROVED') {
      throw AppError.unauthorized('Account is not active');
    }

    const authenticatedReq = req as AuthenticatedRequest;
    authenticatedReq.user = {
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
      iat: payload.iat,
      exp: payload.exp,
    };

    next();
  } catch (error) {
    if (isAppError(error)) {
      next(error);
    } else {
      next(AppError.unauthorized('Authentication failed'));
    }
  }
}

import jwt from 'jsonwebtoken';


===== EXISTING FILE: backend/src/middlewares/authorize.middleware.ts =====
import { Request, Response, NextFunction } from 'express';
import { AppError, isAppError } from '../utils/AppError';
import { UserRole } from '../types';
import { AuthenticatedRequest } from '../types';

export function authorize(...allowedRoles: UserRole[]) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    try {
      const authReq = req as AuthenticatedRequest;

      if (!authReq.user) {
        throw AppError.unauthorized('Authentication required');
      }

      if (!allowedRoles.includes(authReq.user.role)) {
        throw AppError.forbidden('Insufficient permissions');
      }

      next();
    } catch (error) {
      if (isAppError(error)) {
        next(error);
      } else {
        next(AppError.forbidden('Authorization failed'));
      }
    }
  };
}

export function authorizeOwner(
  getResourceUserId: (req: Request) => Promise<string | null> | string | null
) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    try {
      const authReq = req as AuthenticatedRequest;

      if (!authReq.user) {
        throw AppError.unauthorized('Authentication required');
      }

      const resourceUserId = await getResourceUserId(req);

      if (!resourceUserId) {
        throw AppError.notFound('Resource not found');
      }

      if (authReq.user.sub !== resourceUserId && authReq.user.role !== UserRole.ADMIN) {
        throw AppError.forbidden('You can only access your own resources');
      }

      next();
    } catch (error) {
      if (isAppError(error)) {
        next(error);
      } else {
        next(AppError.forbidden('Ownership verification failed'));
      }
    }
  };
}

export function authorizeCompany(
  getResourceCompanyId: (req: Request) => Promise<string | null> | string | null
) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    try {
      const authReq = req as AuthenticatedRequest;

      if (!authReq.user) {
        throw AppError.unauthorized('Authentication required');
      }

      const resourceCompanyId = await getResourceCompanyId(req);

      if (!resourceCompanyId) {
        throw AppError.notFound('Resource not found');
      }

      const user = await import('../models/user.model').then(m => m.User.findById(authReq.user!.sub).lean());

      if (!user) {
        throw AppError.unauthorized('User not found');
      }

      const userCompanyId = user.company?.toString();

      if (authReq.user.role !== UserRole.ADMIN && userCompanyId !== resourceCompanyId) {
        throw AppError.forbidden('You can only access resources from your own company');
      }

      next();
    } catch (error) {
      if (isAppError(error)) {
        next(error);
      } else {
        next(AppError.forbidden('Company authorization failed'));
      }
    }
  };
}


===== EXISTING FILE: backend/src/middlewares/error.middleware.ts =====
import { Request, Response, NextFunction } from 'express';
import mongoose from 'mongoose';
import { AppError, isAppError } from '../utils/AppError';
import { ErrorResponse } from '../types';

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  console.error('Error:', {
    message: err.message,
    stack: err.stack,
    name: err.name,
  });

  if (isAppError(err)) {
    const response: ErrorResponse = err.toResponse();
    res.status(err.status).json(response);
    return;
  }

  if (err instanceof mongoose.Error.ValidationError) {
    const fieldErrors = Object.values(err.errors).map(e => ({
      field: e.path,
      message: e.message,
    }));
    const response: ErrorResponse = {
      status: 400,
      message: 'Validation failed',
      fieldErrors,
    };
    res.status(400).json(response);
    return;
  }

  if (err instanceof mongoose.mongo.MongoServerError && err.code === 11000) {
    const field = Object.keys(err.keyPattern || {})[0] || 'field';
    const response: ErrorResponse = {
      status: 409,
      message: `A record with this ${field} already exists`,
      fieldErrors: [{ field, message: `${field} must be unique` }],
    };
    res.status(409).json(response);
    return;
  }

  if (err instanceof SyntaxError && 'status' in err && err.status === 400 && 'body' in err) {
    const response: ErrorResponse = {
      status: 400,
      message: 'Invalid JSON payload',
    };
    res.status(400).json(response);
    return;
  }

  const response: ErrorResponse = {
    status: 500,
    message: 'An unexpected error occurred',
  };
  res.status(500).json(response);
}

export function notFoundHandler(_req: Request, res: Response): void {
  const response: ErrorResponse = {
    status: 404,
    message: 'Route not found',
  };
  res.status(404).json(response);
}


===== EXISTING FILE: backend/src/middlewares/upload.middleware.ts =====
import multer, { FileFilterCallback, Multer } from 'multer';
import { Request } from 'express';
import { AppError } from '../utils/AppError';
import { env } from '../config/env';
import * as path from 'path';
import * as fs from 'fs';
import { fileTypeFromBuffer } from 'file-type';

const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png'];
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png'];
const MIN_DIMENSION = 100;
const MAX_DIMENSION = 300;

function ensureUploadDir(): void {
  if (!fs.existsSync(env.uploadDir)) {
    fs.mkdirSync(env.uploadDir, { recursive: true });
  }
}

function sanitizeFileName(originalName: string): string {
  const ext = path.extname(originalName).toLowerCase();
  const baseName = path.basename(originalName, ext)
    .replace(/[^a-zA-Z0-9._-]/g, '_')
    .substring(0, 100);
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `${baseName}_${timestamp}_${random}${ext}`;
}

const storage = multer.diskStorage({
  destination: (_req: Request, _file: Express.Multer.File, cb: (error: Error | null, destination: string) => void): void => {
    ensureUploadDir();
    cb(null, env.uploadDir);
  },
  filename: (_req: Request, file: Express.Multer.File, cb: (error: Error | null, filename: string) => void): void => {
    cb(null, sanitizeFileName(file.originalname));
  },
});

function fileFilter(
  _req: Request,
  file: Express.Multer.File,
  cb: FileFilterCallback
): void {
  if (!ALLOWED_MIME_TYPES.includes(file.mimetype)) {
    cb(new AppError(415, 'Only JPG and PNG images are accepted'));
    return;
  }

  const ext = path.extname(file.originalname).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    cb(new AppError(415, 'Only JPG and PNG images are accepted'));
    return;
  }

  cb(null, true);
}

export const upload: Multer = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: env.maxFileSize,
    files: 1,
  },
});

export async function validateImageDimensions(
  req: Request,
  _res: Response,
  next: NextFunction
): Promise<void> {
  try {
    if (!req.file) {
      return next();
    }

    const fileBuffer = req.file.buffer || fs.readFileSync(req.file.path);
    const type = await fileTypeFromBuffer(fileBuffer);

    if (!type || !ALLOWED_MIME_TYPES.includes(type.mime)) {
      if (req.file.path && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      throw AppError.unsupportedMediaType('Only JPG and PNG images are accepted');
    }

    const sharp = (await import('sharp')).default;
    const metadata = await sharp(fileBuffer).metadata();

    if (!metadata.width || !metadata.height) {
      if (req.file.path && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      throw AppError.badRequest('Unable to determine image dimensions');
    }

    if (
      metadata.width < MIN_DIMENSION ||
      metadata.height < MIN_DIMENSION ||
      metadata.width > MAX_DIMENSION ||
      metadata.height > MAX_DIMENSION
    ) {
      if (req.file.path && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      throw AppError.badRequest('The image must be between 100x100 and 300x300 pixels.');
    }

    next();
  } catch (error) {
    if (error instanceof AppError) {
      next(error);
    } else {
      next(AppError.badRequest('Image validation failed'));
    }
  }
}

export function handleMulterError(
  err: Error,
  _req: Request,
  _res: Response,
  next: NextFunction
): void {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      next(AppError.payloadTooLarge('The uploaded file is too large'));
      return;
    }
    if (err.code === 'LIMIT_FILE_COUNT') {
      next(AppError.badRequest('Too many files'));
      return;
    }
    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      next(AppError.badRequest('Unexpected file field'));
      return;
    }
    next(AppError.badRequest(err.message));
    return;
  }
  next(err);
}


===== EXISTING FILE: backend/src/middlewares/validate.middleware.ts =====
import { Request, Response, NextFunction } from 'express';
import { validationResult, ValidationChain, ValidationError } from 'express-validator';
import { AppError } from '../utils/AppError';
import { FieldError } from '../types';

export function validate(validations: ValidationChain[]) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    await Promise.all(validations.map(validation => validation.run(req)));

    const errors = validationResult(req);

    if (!errors.isEmpty()) {
      const fieldErrors: FieldError[] = errors.array().map((error: ValidationError) => {
        if ('path' in error) {
          return { field: error.path, message: error.msg };
        }
        return { field: 'unknown', message: error.msg };
      });

      const uniqueFieldErrors = fieldErrors.reduce((acc: FieldError[], current) => {
        if (!acc.some(e => e.field === current.field && e.message === current.message)) {
          acc.push(current);
        }
        return acc;
      }, []);

      throw AppError.badRequest('Validation failed', uniqueFieldErrors);
    }

    next();
  };
}

export function validateQuery(validations: ValidationChain[]) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    const originalQuery = req.query;
    req.query = { ...req.query };

    await Promise.all(validations.map(validation => validation.run(req)));

    const errors = validationResult(req);

    req.query = originalQuery;

    if (!errors.isEmpty()) {
      const fieldErrors: FieldError[] = errors.array().map((error: ValidationError) => {
        if ('path' in error) {
          return { field: error.path, message: error.msg };
        }
        return { field: 'unknown', message: error.msg };
      });

      const uniqueFieldErrors = fieldErrors.reduce((acc: FieldError[], current) => {
        if (!acc.some(e => e.field === current.field && e.message === current.message)) {
          acc.push(current);
        }
        return acc;
      }, []);

      throw AppError.badRequest('Validation failed', uniqueFieldErrors);
    }

    next();
  };
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

1. Does every file I import actually exist, either in the context above or in
   this same answer? No import of a file nobody has written.
2. Do my imports match the exact export style of the file they import from —
   default vs named?
3. Have I written every file completely, with no elision anywhere?
4. Does every function have an explicit return type, and is `any` absent?
5. Does every rule the specification states appear somewhere in the code?
6. Are all reads and writes going through Mongoose?
7. Is every path in a `FILE:` line starting with `backend/`?
