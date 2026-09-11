# Task: generate the controllers

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

- Every file in this stage belongs under `backend/src/controllers/`.

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

## Existing code — models, middlewares and services

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


===== EXISTING FILE: backend/src/utils/AppError.ts =====
import { FieldError, ErrorResponse } from '../types';

export class AppError extends Error {
  public readonly status: number;
  public readonly fieldErrors?: FieldError[];
  public readonly isOperational: boolean;

  constructor(status: number, message: string, fieldErrors?: FieldError[]) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
    this.isOperational = true;

    Object.setPrototypeOf(this, AppError.prototype);
    Error.captureStackTrace(this, this.constructor);
  }

  static badRequest(message: string, fieldErrors?: FieldError[]): AppError {
    return new AppError(400, message, fieldErrors);
  }

  static unauthorized(message = 'Invalid or missing credentials'): AppError {
    return new AppError(401, message);
  }

  static forbidden(message = 'You do not have permission to perform this action'): AppError {
    return new AppError(403, message);
  }

  static notFound(message = 'Resource not found'): AppError {
    return new AppError(404, message);
  }

  static conflict(message: string): AppError {
    return new AppError(409, message);
  }

  static payloadTooLarge(message = 'The uploaded file is too large'): AppError {
    return new AppError(413, message);
  }

  static unsupportedMediaType(message = 'Unsupported file type'): AppError {
    return new AppError(415, message);
  }

  static gone(message: string): AppError {
    return new AppError(410, message);
  }

  static internal(message = 'An unexpected error occurred'): AppError {
    const error = new AppError(500, message);
    error.isOperational = false;
    return error;
  }

  toResponse(): ErrorResponse {
    const response: ErrorResponse = {
      status: this.status,
      message: this.message,
    };
    if (this.fieldErrors && this.fieldErrors.length > 0) {
      response.fieldErrors = this.fieldErrors;
    }
    return response;
  }
}

export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}


===== EXISTING FILE: backend/src/utils/password.ts =====
import bcrypt from 'bcryptjs';

const SALT_ROUNDS = 12;

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function validatePasswordPolicy(password: string): { valid: boolean; message?: string } {
  if (password.length < 8 || password.length > 12) {
    return { valid: false, message: 'Password must be between 8 and 12 characters.' };
  }

  if (!/^[A-Za-z]/.test(password)) {
    return { valid: false, message: 'Password must begin with a letter.' };
  }

  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter.' };
  }

  if (!/[0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one digit.' };
  }

  if (!/[^A-Za-z0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one special character.' };
  }

  return { valid: true };
}


===== EXISTING FILE: backend/src/utils/token.ts =====
import jwt, { SignOptions, VerifyOptions } from 'jsonwebtoken';
import { env } from '../config/env';
import { JwtPayload, TokenPair } from '../types';

const ACCESS_TOKEN_OPTIONS: SignOptions = {
  expiresIn: env.jwtAccessTokenTtl as SignOptions['expiresIn'],
};

const REFRESH_TOKEN_OPTIONS: SignOptions = {
  expiresIn: env.jwtRefreshTokenTtl as SignOptions['expiresIn'],
};

const RESET_TOKEN_OPTIONS: SignOptions = {
  expiresIn: env.passwordResetTokenTtl as SignOptions['expiresIn'],
};

const VERIFY_OPTIONS: VerifyOptions = {
  algorithms: ['HS256'],
};

export function signAccessToken(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, env.jwtSecret, ACCESS_TOKEN_OPTIONS);
}

export function signRefreshToken(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, env.jwtSecret, REFRESH_TOKEN_OPTIONS);
}

export function signTokenPair(payload: Omit<JwtPayload, 'iat' | 'exp'>): TokenPair {
  return {
    accessToken: signAccessToken(payload),
    refreshToken: signRefreshToken(payload),
  };
}

export function signPasswordResetToken(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, env.jwtSecret, RESET_TOKEN_OPTIONS);
}

export function verifyAccessToken(token: string): JwtPayload {
  return jwt.verify(token, env.jwtSecret, VERIFY_OPTIONS) as JwtPayload;
}

export function verifyRefreshToken(token: string): JwtPayload {
  return jwt.verify(token, env.jwtSecret, VERIFY_OPTIONS) as JwtPayload;
}

export function verifyPasswordResetToken(token: string): JwtPayload {
  return jwt.verify(token, env.jwtSecret, VERIFY_OPTIONS) as JwtPayload;
}

export function decodeToken(token: string): JwtPayload | null {
  try {
    return jwt.decode(token) as JwtPayload | null;
  } catch {
    return null;
  }
}


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


===== EXISTING FILE: backend/src/services/admin.service.ts =====
import { User, IUser } from '../models/user.model';
import { RegistrationRequest, IRegistrationRequest } from '../models/registration-request.model';
import { Company, ICompany } from '../models/company.model';
import { Space, ISpace } from '../models/space.model';
import { Reservation, IReservation, ReservationStatus } from '../models/reservation.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus, RegistrationStatus } from '../types';
import mongoose from 'mongoose';

export interface AdminStatistics {
  users: {
    total: number;
    members: number;
    managers: number;
    admins: number;
    pending: number;
    approved: number;
    rejected: number;
  };
  companies: {
    total: number;
  };
  spaces: {
    total: number;
    active: number;
    inactive: number;
  };
  reservations: {
    total: number;
    pending: number;
    confirmed: number;
    cancelled: number;
    completed: number;
  };
}

export interface PendingRegistrationRequest {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  submittedAt: Date;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
  profileImage: string;
}

export class AdminService {
  async getStatistics(): Promise<AdminStatistics> {
    const [
      totalUsers,
      members,
      managers,
      admins,
      pendingUsers,
      approvedUsers,
      rejectedUsers,
      totalCompanies,
      totalSpaces,
      activeSpaces,
      inactiveSpaces,
      totalReservations,
      pendingReservations,
      confirmedReservations,
      cancelledReservations,
      completedReservations,
    ] = await Promise.all([
      User.countDocuments(),
      User.countDocuments({ role: UserRole.MEMBER }),
      User.countDocuments({ role: UserRole.MANAGER }),
      User.countDocuments({ role: UserRole.ADMIN }),
      User.countDocuments({ status: UserStatus.PENDING }),
      User.countDocuments({ status: UserStatus.APPROVED }),
      User.countDocuments({ status: UserStatus.REJECTED }),
      Company.countDocuments(),
      Space.countDocuments(),
      Space.countDocuments({ isActive: true }),
      Space.countDocuments({ isActive: false }),
      Reservation.countDocuments(),
      Reservation.countDocuments({ status: ReservationStatus.PENDING }),
      Reservation.countDocuments({ status: ReservationStatus.CONFIRMED }),
      Reservation.countDocuments({ status: ReservationStatus.CANCELLED }),
      Reservation.countDocuments({ status: ReservationStatus.COMPLETED }),
    ]);

    return {
      users: {
        total: totalUsers,
        members,
        managers,
        admins,
        pending: pendingUsers,
        approved: approvedUsers,
        rejected: rejectedUsers,
      },
      companies: {
        total: totalCompanies,
      },
      spaces: {
        total: totalSpaces,
        active: activeSpaces,
        inactive: inactiveSpaces,
      },
      reservations: {
        total: totalReservations,
        pending: pendingReservations,
        confirmed: confirmedReservations,
        cancelled: cancelledReservations,
        completed: completedReservations,
      },
    };
  }

  async getPendingRegistrations(): Promise<PendingRegistrationRequest[]> {
    const requests = await RegistrationRequest.find({ status: RegistrationStatus.PENDING })
      .sort({ submittedAt: 1 })
      .lean();

    return requests.map(req => ({
      id: req._id.toString(),
      username: req.username,
      firstName: req.firstName,
      lastName: req.lastName,
      email: req.email,
      role: req.role,
      submittedAt: req.submittedAt,
      companyName: req.companyName,
      headquartersAddress: req.headquartersAddress,
      companyNumber: req.companyNumber,
      taxId: req.taxId,
      profileImage: req.profileImage,
    }));
  }

  async getAllUsers(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    role?: UserRole,
    status?: UserStatus
  ): Promise<{ data: Array<IUser & { id: string }>; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (role) query.role = role;
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [users, total] = await Promise.all([
      User.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      User.countDocuments(query),
    ]);

    return {
      data: users.map(u => ({ ...u, id: u._id.toString() })),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getAllCompanies(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<{ data: ICompany[]; total: number; page: number; limit: number; totalPages: number }> {
    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [companies, total] = await Promise.all([
      Company.find()
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Company.countDocuments(),
    ]);

    return {
      data: companies,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getAllSpaces(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    isActive?: boolean
  ): Promise<{ data: ISpace[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (isActive !== undefined) query.isActive = isActive;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [spaces, total] = await Promise.all([
      Space.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Space.countDocuments(query),
    ]);

    return {
      data: spaces,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getAllReservations(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    status?: ReservationStatus
  ): Promise<{ data: IReservation[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [reservations, total] = await Promise.all([
      Reservation.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Reservation.countDocuments(query),
    ]);

    return {
      data: reservations,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async deleteUser(userId: string, adminId: string): Promise<{ message: string }> {
    if (userId === adminId) {
      throw AppError.badRequest('You cannot delete your own account.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    await User.findByIdAndDelete(userId);
    return { message: 'User deleted successfully.' };
  }

  async updateUserStatus(userId: string, status: UserStatus, adminId: string): Promise<{ message: string }> {
    if (userId === adminId) {
      throw AppError.badRequest('You cannot change your own status.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    user.status = status;
    await user.save();

    return { message: `User status updated to ${status}.` };
  }

  async updateUserRole(userId: string, role: UserRole, adminId: string): Promise<{ message: string }> {
    if (userId === adminId) {
      throw AppError.badRequest('You cannot change your own role.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    user.role = role;
    await user.save();

    return { message: `User role updated to ${role}.` };
  }
}

export const adminService = new AdminService();


===== EXISTING FILE: backend/src/services/auth.service.ts =====
import { User, IUser } from '../models/user.model';
import { RegistrationRequest, IRegistrationRequest } from '../models/registration-request.model';
import { PasswordResetToken, IPasswordResetToken } from '../models/password-reset-token.model';
import { Company, ICompany } from '../models/company.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus, RegistrationStatus } from '../types';
import { hashPassword, verifyPassword, validatePasswordPolicy } from '../utils/password';
import { signTokenPair, signPasswordResetToken, verifyPasswordResetToken } from '../utils/token';
import mongoose, { ClientSession } from 'mongoose';

export interface LoginResult {
  user: {
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    role: UserRole;
    profileImage: string;
  };
  tokens: {
    accessToken: string;
    refreshToken: string;
  };
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

export interface PasswordResetRequestResult {
  message: string;
}

export interface PasswordResetVerifyResult {
  valid: boolean;
  userId?: string;
  token?: string;
}

export interface PasswordResetConfirmResult {
  message: string;
}

export class AuthService {
  async login(
    username: string,
    password: string,
    isAdminRoute: boolean = false,
    now: Date = new Date()
  ): Promise<LoginResult> {
    const user = await User.findOne({ username }).select('+passwordHash').lean();

    if (!user) {
      throw AppError.unauthorized('Invalid username or password.');
    }

    if (isAdminRoute) {
      if (user.role !== UserRole.ADMIN) {
        throw AppError.unauthorized('Invalid username or password.');
      }
    } else {
      if (user.role === UserRole.ADMIN) {
        throw AppError.unauthorized('Invalid username or password.');
      }
    }

    const isValid = await verifyPassword(password, user.passwordHash);
    if (!isValid) {
      throw AppError.unauthorized('Invalid username or password.');
    }

    if (user.status !== UserStatus.APPROVED) {
      if (user.status === UserStatus.PENDING) {
        throw AppError.forbidden('Your registration is still awaiting administrator approval.');
      }
      if (user.status === UserStatus.REJECTED) {
        throw AppError.forbidden('Your registration request was rejected.');
      }
      throw AppError.forbidden('Account is not active');
    }

    const tokens = signTokenPair({
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
    });

    return {
      user: {
        id: user._id.toString(),
        username: user.username,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        profileImage: user.profileImage,
      },
      tokens,
    };
  }

  async registerMember(data: RegisterMemberData, session?: ClientSession): Promise<IRegistrationRequest> {
    const passwordValidation = validatePasswordPolicy(data.password);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    const existingUser = await User.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingUser) {
      if (existingUser.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    const existingRequest = await RegistrationRequest.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingRequest) {
      if (existingRequest.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    const passwordHash = await hashPassword(data.password);

    const registrationRequest = new RegistrationRequest({
      username: data.username,
      passwordHash,
      firstName: data.firstName,
      lastName: data.lastName,
      phone: data.phone,
      email: data.email.toLowerCase(),
      role: UserRole.MEMBER,
      profileImage: data.profileImage || 'default-avatar.png',
      status: RegistrationStatus.PENDING,
      submittedAt: new Date(),
    });

    await registrationRequest.save({ session: session || null });
    return registrationRequest;
  }

  async registerManager(data: RegisterManagerData, session?: ClientSession): Promise<IRegistrationRequest> {
    const passwordValidation = validatePasswordPolicy(data.password);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    if (!/^\d{8}$/.test(data.companyNumber)) {
      throw AppError.badRequest('Company number must be exactly 8 digits.', [{ field: 'companyNumber', message: 'Company number must be exactly 8 digits.' }]);
    }

    if (!/^[1-9]\d{8}$/.test(data.taxId)) {
      throw AppError.badRequest('Tax ID must be exactly 9 digits and must not begin with zero.', [{ field: 'taxId', message: 'Tax ID must be exactly 9 digits and must not begin with zero.' }]);
    }

    const existingUser = await User.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingUser) {
      if (existingUser.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    const existingRequest = await RegistrationRequest.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingRequest) {
      if (existingRequest.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    let company: ICompany | null = null;
    const existingCompany = await Company.findOne({
      $or: [{ companyNumber: data.companyNumber }, { taxId: data.taxId }],
    }).session(session || null);

    if (existingCompany) {
      if (existingCompany.companyNumber === data.companyNumber && existingCompany.taxId !== data.taxId) {
        throw AppError.conflict('A different company is already registered with that company number.');
      }
      if (existingCompany.taxId === data.taxId && existingCompany.companyNumber !== data.companyNumber) {
        throw AppError.conflict('A different company is already registered with that tax ID.');
      }
      company = existingCompany;
    }

    const managerCount = await this.countCompanyManagers(company?._id || new mongoose.Types.ObjectId(), session);

    if (managerCount >= 2) {
      throw AppError.conflict('This company already has the maximum of two space managers.');
    }

    const passwordHash = await hashPassword(data.password);

    const registrationRequest = new RegistrationRequest({
      username: data.username,
      passwordHash,
      firstName: data.firstName,
      lastName: data.lastName,
      phone: data.phone,
      email: data.email.toLowerCase(),
      role: UserRole.MANAGER,
      companyName: data.companyName,
      headquartersAddress: data.headquartersAddress,
      companyNumber: data.companyNumber,
      taxId: data.taxId,
      profileImage: data.profileImage || 'default-avatar.png',
      status: RegistrationStatus.PENDING,
      submittedAt: new Date(),
    });

    await registrationRequest.save({ session: session || null });
    return registrationRequest;
  }

  private async countCompanyManagers(companyId: mongoose.Types.ObjectId, session?: ClientSession): Promise<number> {
    const approvedManagers = await User.countDocuments({
      company: companyId,
      role: UserRole.MANAGER,
      status: UserStatus.APPROVED,
    }).session(session || null);

    const pendingManagers = await RegistrationRequest.countDocuments({
      companyNumber: (await Company.findById(companyId).session(session || null))?.companyNumber,
      role: UserRole.MANAGER,
      status: RegistrationStatus.PENDING,
    }).session(session || null);

    return approvedManagers + pendingManagers;
  }

  async requestPasswordReset(identifier: string, now: Date = new Date()): Promise<PasswordResetRequestResult> {
    const user = await User.findOne({
      $or: [{ username: identifier }, { email: identifier.toLowerCase() }],
      status: UserStatus.APPROVED,
    }).lean();

    if (!user) {
      return { message: 'If an account exists, a reset link has been sent to your email.' };
    }

    await PasswordResetToken.deleteMany({ user: user._id, usedAt: { $exists: false } });

    const expiresAt = new Date(now.getTime() + 30 * 60 * 1000);
    const tokenPayload = {
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
      type: 'password-reset' as const,
    };
    const token = signPasswordResetToken(tokenPayload);

    await PasswordResetToken.create({
      user: user._id,
      token,
      expiresAt,
    });

    return { message: 'If an account exists, a reset link has been sent to your email.' };
  }

  async verifyPasswordResetToken(token: string, now: Date = new Date()): Promise<PasswordResetVerifyResult> {
    let payload: { sub: string; type: string };
    try {
      payload = verifyPasswordResetToken(token) as { sub: string; type: string };
    } catch {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    if (payload.type !== 'password-reset') {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    const resetToken = await PasswordResetToken.findOne({ token }).lean();

    if (!resetToken) {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    if (resetToken.usedAt) {
      throw AppError.gone('This reset link has already been used.');
    }

    if (resetToken.expiresAt < now) {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    return { valid: true, userId: resetToken.user.toString(), token };
  }

  async confirmPasswordReset(token: string, newPassword: string, confirmPassword: string, now: Date = new Date()): Promise<PasswordResetConfirmResult> {
    if (newPassword !== confirmPassword) {
      throw AppError.badRequest('The two passwords do not match.', [{ field: 'confirmPassword', message: 'The two passwords do not match.' }]);
    }

    const passwordValidation = validatePasswordPolicy(newPassword);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    const verification = await this.verifyPasswordResetToken(token, now);
    if (!verification.valid || !verification.userId || !verification.token) {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const passwordHash = await hashPassword(newPassword);

      await User.findByIdAndUpdate(
        verification.userId,
        { passwordHash },
        { session }
      );

      await PasswordResetToken.findOneAndUpdate(
        { token: verification.token },
        { usedAt: now },
        { session }
      );

      await PasswordResetToken.updateMany(
        { user: verification.userId, usedAt: { $exists: false }, _id: { $ne: (await PasswordResetToken.findOne({ token: verification.token }).lean())?._id } },
        { usedAt: now },
        { session }
      );

      await session.commitTransaction();
      return { message: 'Your password has been changed successfully.' };
    } catch (error) {
      await session.abortTransaction();
      throw error;
    } finally {
      await session.endSession();
    }
  }

  async refreshAccessToken(refreshToken: string): Promise<{ accessToken: string }> {
    let payload: { sub: string; username: string; role: UserRole };
    try {
      payload = verifyPasswordResetToken(refreshToken) as { sub: string; username: string; role: UserRole };
    } catch {
      throw AppError.unauthorized('Invalid or expired refresh token');
    }

    const user = await User.findById(payload.sub).lean();
    if (!user || user.status !== UserStatus.APPROVED) {
      throw AppError.unauthorized('User no longer exists or is not active');
    }

    const accessToken = signTokenPair({
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
    }).accessToken;

    return { accessToken };
  }
}

export const authService = new AuthService();


===== EXISTING FILE: backend/src/services/company.service.ts =====
import { Company, ICompany } from '../models/company.model';
import { User, IUser } from '../models/user.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface CompanyData {
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
}

export interface CompanyWithManagers extends ICompany {
  managers: Array<{
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    email: string;
    status: UserStatus;
  }>;
}

export class CompanyService {
  async createCompany(data: CompanyData, session?: ClientSession): Promise<ICompany> {
    if (!/^\d{8}$/.test(data.companyNumber)) {
      throw AppError.badRequest('Company number must be exactly 8 digits.', [{ field: 'companyNumber', message: 'Company number must be exactly 8 digits.' }]);
    }

    if (!/^[1-9]\d{8}$/.test(data.taxId)) {
      throw AppError.badRequest('Tax ID must be exactly 9 digits and must not begin with zero.', [{ field: 'taxId', message: 'Tax ID must be exactly 9 digits and must not begin with zero.' }]);
    }

    const existingCompany = await Company.findOne({
      $or: [{ companyNumber: data.companyNumber }, { taxId: data.taxId }],
    }).session(session || null);

    if (existingCompany) {
      if (existingCompany.companyNumber === data.companyNumber) {
        throw AppError.conflict('A different company is already registered with that company number.');
      }
      throw AppError.conflict('A different company is already registered with that tax ID.');
    }

    const company = new Company(data);
    await company.save({ session: session || null });
    return company;
  }

  async getCompanyById(companyId: string): Promise<CompanyWithManagers> {
    const company = await Company.findById(companyId).lean();
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    const managers = await User.find({ company: company._id, role: UserRole.MANAGER })
      .select('username firstName lastName email status')
      .lean();

    return {
      ...company,
      managers: managers.map(m => ({
        id: m._id.toString(),
        username: m.username,
        firstName: m.firstName,
        lastName: m.lastName,
        email: m.email,
        status: m.status,
      })),
    } as CompanyWithManagers;
  }

  async getCompanies(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<{ data: ICompany[]; total: number; page: number; limit: number; totalPages: number }> {
    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [companies, total] = await Promise.all([
      Company.find()
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Company.countDocuments(),
    ]);

    return {
      data: companies,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async updateCompany(companyId: string, data: Partial<CompanyData>): Promise<ICompany> {
    if (data.companyNumber && !/^\d{8}$/.test(data.companyNumber)) {
      throw AppError.badRequest('Company number must be exactly 8 digits.', [{ field: 'companyNumber', message: 'Company number must be exactly 8 digits.' }]);
    }

    if (data.taxId && !/^[1-9]\d{8}$/.test(data.taxId)) {
      throw AppError.badRequest('Tax ID must be exactly 9 digits and must not begin with zero.', [{ field: 'taxId', message: 'Tax ID must be exactly 9 digits and must not begin with zero.' }]);
    }

    const company = await Company.findById(companyId);
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    if (data.companyNumber && data.companyNumber !== company.companyNumber) {
      const existing = await Company.findOne({ companyNumber: data.companyNumber }).lean();
      if (existing) {
        throw AppError.conflict('A different company is already registered with that company number.');
      }
      company.companyNumber = data.companyNumber;
    }

    if (data.taxId && data.taxId !== company.taxId) {
      const existing = await Company.findOne({ taxId: data.taxId }).lean();
      if (existing) {
        throw AppError.conflict('A different company is already registered with that tax ID.');
      }
      company.taxId = data.taxId;
    }

    if (data.name) company.name = data.name;
    if (data.headquartersAddress) company.headquartersAddress = data.headquartersAddress;

    await company.save();
    return company;
  }

  async deleteCompany(companyId: string): Promise<{ message: string }> {
    const company = await Company.findById(companyId);
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    const managersCount = await User.countDocuments({ company: company._id, role: UserRole.MANAGER });
    if (managersCount > 0) {
      throw AppError.conflict('Cannot delete company with associated space managers.');
    }

    await Company.findByIdAndDelete(companyId);
    return { message: 'Company deleted successfully.' };
  }

  async getCompanyManagersCount(companyId: string): Promise<number> {
    return User.countDocuments({ company: companyId, role: UserRole.MANAGER, status: UserStatus.APPROVED });
  }

  async getCompanyPendingManagersCount(companyNumber: string): Promise<number> {
    const { RegistrationRequest } = await import('../models/registration-request.model');
    const { RegistrationStatus } = await import('../types');
    return RegistrationRequest.countDocuments({
      companyNumber,
      role: UserRole.MANAGER,
      status: RegistrationStatus.PENDING,
    });
  }
}

export const companyService = new CompanyService();


===== EXISTING FILE: backend/src/services/index.ts =====
export { authService, AuthService } from './auth.service';
export { registrationService, RegistrationService } from './registration.service';
export { userService, UserService } from './user.service';
export { companyService, CompanyService } from './company.service';
export { adminService, AdminService } from './admin.service';
export { spaceService, SpaceService } from './space.service';
export { reservationService, ReservationService } from './reservation.service';


===== EXISTING FILE: backend/src/services/registration.service.ts =====
import { RegistrationRequest, IRegistrationRequest } from '../models/registration-request.model';
import { User, IUser } from '../models/user.model';
import { Company, ICompany } from '../models/company.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus, RegistrationStatus } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface PendingRegistrationRequest {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  submittedAt: Date;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
  profileImage: string;
}

export interface RegistrationDecisionResult {
  message: string;
  user?: {
    id: string;
    username: string;
    role: UserRole;
  };
}

export class RegistrationService {
  async getPendingRequests(): Promise<PendingRegistrationRequest[]> {
    const requests = await RegistrationRequest.find({ status: RegistrationStatus.PENDING })
      .sort({ submittedAt: 1 })
      .lean();

    return requests.map(req => ({
      id: req._id.toString(),
      username: req.username,
      firstName: req.firstName,
      lastName: req.lastName,
      email: req.email,
      role: req.role,
      submittedAt: req.submittedAt,
      companyName: req.companyName,
      headquartersAddress: req.headquartersAddress,
      companyNumber: req.companyNumber,
      taxId: req.taxId,
      profileImage: req.profileImage,
    }));
  }

  async approveRequest(requestId: string, adminId: string, now: Date = new Date()): Promise<RegistrationDecisionResult> {
    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const request = await RegistrationRequest.findById(requestId).session(session);
      if (!request) {
        throw AppError.notFound('Registration request not found');
      }

      if (request.status !== RegistrationStatus.PENDING) {
        throw AppError.conflict('This registration request has already been decided.');
      }

      if (request.role === UserRole.MANAGER) {
        await this.validateCompanyManagerLimit(request, session);
      }

      let companyId: mongoose.Types.ObjectId | undefined;

      if (request.role === UserRole.MANAGER && request.companyNumber && request.taxId) {
        let company = await Company.findOne({
          $or: [{ companyNumber: request.companyNumber }, { taxId: request.taxId }],
        }).session(session);

        if (!company) {
          company = new Company({
            name: request.companyName!,
            headquartersAddress: request.headquartersAddress!,
            companyNumber: request.companyNumber,
            taxId: request.taxId,
          });
          await company.save({ session });
        }
        companyId = company._id;
      }

      const user = new User({
        username: request.username,
        passwordHash: request.passwordHash,
        firstName: request.firstName,
        lastName: request.lastName,
        phone: request.phone,
        email: request.email,
        role: request.role,
        status: UserStatus.APPROVED,
        profileImage: request.profileImage,
        company: companyId,
      });

      await user.save({ session });

      request.status = RegistrationStatus.APPROVED;
      request.decidedAt = now;
      request.decidedBy = new mongoose.Types.ObjectId(adminId);
      await request.save({ session });

      await session.commitTransaction();

      return {
        message: 'Registration request approved successfully.',
        user: {
          id: user._id.toString(),
          username: user.username,
          role: user.role,
        },
      };
    } catch (error) {
      await session.abortTransaction();
      throw error;
    } finally {
      await session.endSession();
    }
  }

  async rejectRequest(requestId: string, adminId: string, now: Date = new Date()): Promise<RegistrationDecisionResult> {
    const request = await RegistrationRequest.findById(requestId);
    if (!request) {
      throw AppError.notFound('Registration request not found');
    }

    if (request.status !== RegistrationStatus.PENDING) {
      throw AppError.conflict('This registration request has already been decided.');
    }

    request.status = RegistrationStatus.REJECTED;
    request.decidedAt = now;
    request.decidedBy = new mongoose.Types.ObjectId(adminId);
    await request.save();

    return { message: 'Registration request rejected.' };
  }

  private async validateCompanyManagerLimit(request: IRegistrationRequest, session: ClientSession): Promise<void> {
    if (!request.companyNumber || !request.taxId) {
      return;
    }

    const company = await Company.findOne({
      $or: [{ companyNumber: request.companyNumber }, { taxId: request.taxId }],
    }).session(session);

    const companyId = company?._id;

    const approvedManagers = await User.countDocuments({
      company: companyId,
      role: UserRole.MANAGER,
      status: UserStatus.APPROVED,
    }).session(session);

    const pendingManagers = await RegistrationRequest.countDocuments({
      companyNumber: request.companyNumber,
      role: UserRole.MANAGER,
      status: RegistrationStatus.PENDING,
      _id: { $ne: request._id },
    }).session(session);

    if (approvedManagers + pendingManagers >= 2) {
      throw AppError.conflict('This company already has the maximum of two space managers.');
    }
  }

  async isUsernameAvailable(username: string, excludeRequestId?: string): Promise<boolean> {
    const user = await User.findOne({ username }).lean();
    if (user) return false;

    const query: Record<string, unknown> = { username };
    if (excludeRequestId) {
      query._id = { $ne: excludeRequestId };
    }
    const request = await RegistrationRequest.findOne(query).lean();
    return !request;
  }

  async isEmailAvailable(email: string, excludeRequestId?: string): Promise<boolean> {
    const user = await User.findOne({ email: email.toLowerCase() }).lean();
    if (user) return false;

    const query: Record<string, unknown> = { email: email.toLowerCase() };
    if (excludeRequestId) {
      query._id = { $ne: excludeRequestId };
    }
    const request = await RegistrationRequest.findOne(query).lean();
    return !request;
  }

  async releaseUsername(username: string): Promise<void> {
    await RegistrationRequest.deleteOne({ username, status: RegistrationStatus.REJECTED });
  }
}

export const registrationService = new RegistrationService();


===== EXISTING FILE: backend/src/services/reservation.service.ts =====
import { Reservation, IReservation, ReservationStatus } from '../models/reservation.model';
import { Space, ISpace } from '../models/space.model';
import { User, IUser } from '../models/user.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface CreateReservationData {
  spaceId: string;
  startTime: Date;
  endTime: Date;
  notes?: string;
}

export interface ReservationWithDetails extends IReservation {
  space: ISpace;
  user: {
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    email: string;
  };
}

export class ReservationService {
  async createReservation(userId: string, data: CreateReservationData, now: Date = new Date()): Promise<ReservationWithDetails> {
    if (data.startTime < now) {
      throw AppError.badRequest('Start time cannot be in the past.');
    }

    if (data.startTime >= data.endTime) {
      throw AppError.badRequest('End time must be after start time.');
    }

    const space = await Space.findById(data.spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    if (!space.isActive) {
      throw AppError.badRequest('This space is not available for reservations.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.status !== UserStatus.APPROVED) {
      throw AppError.forbidden('Your account is not approved.');
    }

    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const overlappingReservation = await Reservation.findOne({
        space: data.spaceId,
        status: { $in: [ReservationStatus.PENDING, ReservationStatus.CONFIRMED] },
        startTime: { $lt: data.endTime },
        endTime: { $gt: data.startTime },
      }).session(session);

      if (overlappingReservation) {
        throw AppError.conflict('The space is already reserved for the selected time period.');
      }

      const durationHours = (data.endTime.getTime() - data.startTime.getTime()) / (1000 * 60 * 60);
      const totalPrice = Math.ceil(durationHours) * space.pricePerHour;

      const reservation = new Reservation({
        user: userId,
        space: data.spaceId,
        startTime: data.startTime,
        endTime: data.endTime,
        status: ReservationStatus.PENDING,
        totalPrice,
        notes: data.notes,
      });

      await reservation.save({ session });

      await session.commitTransaction();

      const populatedReservation = await Reservation.findById(reservation._id)
        .populate('space')
        .populate('user', 'username firstName lastName email')
        .lean();

      return this.mapToReservationWithDetails(populatedReservation!);
    } catch (error) {
      await session.abortTransaction();
      throw error;
    } finally {
      await session.endSession();
    }
  }

  async getReservationById(reservationId: string, userId: string, userRole: UserRole): Promise<ReservationWithDetails> {
    const reservation = await Reservation.findById(reservationId)
      .populate('space')
      .populate('user', 'username firstName lastName email')
      .lean();

    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    if (userRole !== UserRole.ADMIN && reservation.user._id.toString() !== userId) {
      const space = await Space.findById(reservation.space._id).lean();
      if (!space || space.company.toString() !== (await User.findById(userId).lean())?.company?.toString()) {
        throw AppError.forbidden('You can only access your own reservations.');
      }
    }

    return this.mapToReservationWithDetails(reservation);
  }

  async getUserReservations(
    userId: string,
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'startTime',
    sortOrder: 'asc' | 'desc' = 'desc',
    status?: ReservationStatus
  ): Promise<{ data: ReservationWithDetails[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = { user: userId };
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [reservations, total] = await Promise.all([
      Reservation.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .populate('space')
        .populate('user', 'username firstName lastName email')
        .lean(),
      Reservation.countDocuments(query),
    ]);

    return {
      data: reservations.map(r => this.mapToReservationWithDetails(r)),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getCompanyReservations(
    companyId: string,
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'startTime',
    sortOrder: 'asc' | 'desc' = 'desc',
    status?: ReservationStatus
  ): Promise<{ data: ReservationWithDetails[]; total: number; page: number; limit: number; totalPages: number }> {
    const spaces = await Space.find({ company: companyId }).select('_id').lean();
    const spaceIds = spaces.map(s => s._id);

    const query: Record<string, unknown> = { space: { $in: spaceIds } };
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [reservations, total] = await Promise.all([
      Reservation.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .populate('space')
        .populate('user', 'username firstName lastName email')
        .lean(),
      Reservation.countDocuments(query),
    ]);

    return {
      data: reservations.map(r => this.mapToReservationWithDetails(r)),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async cancelReservation(reservationId: string, userId: string, userRole: UserRole): Promise<{ message: string }> {
    const reservation = await Reservation.findById(reservationId);
    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    if (userRole !== UserRole.ADMIN && reservation.user.toString() !== userId) {
      const space = await Space.findById(reservation.space).lean();
      if (!space || space.company.toString() !== (await User.findById(userId).lean())?.company?.toString()) {
        throw AppError.forbidden('You can only cancel your own reservations.');
      }
    }

    if (reservation.status === ReservationStatus.CANCELLED) {
      throw AppError.badRequest('Reservation is already cancelled.');
    }

    if (reservation.status === ReservationStatus.COMPLETED) {
      throw AppError.badRequest('Cannot cancel a completed reservation.');
    }

    reservation.status = ReservationStatus.CANCELLED;
    await reservation.save();

    return { message: 'Reservation cancelled successfully.' };
  }

  async confirmReservation(reservationId: string, managerId: string): Promise<{ message: string }> {
    const reservation = await Reservation.findById(reservationId).populate('space');
    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    const space = reservation.space as ISpace;
    const user = await User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can confirm reservations.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only confirm reservations for your own company spaces.');
    }

    if (reservation.status !== ReservationStatus.PENDING) {
      throw AppError.badRequest('Only pending reservations can be confirmed.');
    }

    reservation.status = ReservationStatus.CONFIRMED;
    await reservation.save();

    return { message: 'Reservation confirmed successfully.' };
  }

  async completeReservation(reservationId: string, managerId: string): Promise<{ message: string }> {
    const reservation = await Reservation.findById(reservationId).populate('space');
    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    const space = reservation.space as ISpace;
    const user = await User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can complete reservations.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only complete reservations for your own company spaces.');
    }

    if (reservation.status !== ReservationStatus.CONFIRMED) {
      throw AppError.badRequest('Only confirmed reservations can be completed.');
    }

    reservation.status = ReservationStatus.COMPLETED;
    await reservation.save();

    return { message: 'Reservation marked as completed.' };
  }

  async checkAvailability(spaceId: string, startTime: Date, endTime: Date): Promise<{ available: boolean; conflictingReservations: IReservation[] }> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const conflictingReservations = await Reservation.find({
      space: spaceId,
      status: { $in: [ReservationStatus.PENDING, ReservationStatus.CONFIRMED] },
      startTime: { $lt: endTime },
      endTime: { $gt: startTime },
    }).lean();

    return {
      available: conflictingReservations.length === 0,
      conflictingReservations,
    };
  }

  private mapToReservationWithDetails(reservation: IReservation & {
    space: ISpace;
    user: { _id: mongoose.Types.ObjectId; username: string; firstName: string; lastName: string; email: string };
  }): ReservationWithDetails {
    return {
      ...reservation,
      space: reservation.space,
      user: {
        id: reservation.user._id.toString(),
        username: reservation.user.username,
        firstName: reservation.user.firstName,
        lastName: reservation.user.lastName,
        email: reservation.user.email,
      },
    };
  }
}

export const reservationService = new ReservationService();


===== EXISTING FILE: backend/src/services/space.service.ts =====
import { Space, ISpace } from '../models/space.model';
import { Company, ICompany } from '../models/company.model';
import { AppError } from '../utils/AppError';
import { UserRole } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface CreateSpaceData {
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

export class SpaceService {
  async createSpace(data: CreateSpaceData, managerId: string, session?: ClientSession): Promise<ISpace> {
    const company = await Company.findById(data.companyId).session(session || null);
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    const user = await require('../models/user.model').User.findById(managerId).session(session || null);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can create spaces.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== data.companyId) {
      throw AppError.forbidden('You can only create spaces for your own company.');
    }

    const space = new Space({
      ...data,
      company: data.companyId,
    });

    await space.save({ session: session || null });
    return space;
  }

  async getSpaceById(spaceId: string): Promise<ISpace> {
    const space = await Space.findById(spaceId).populate('company').lean();
    if (!space) {
      throw AppError.notFound('Space not found');
    }
    return space;
  }

  async getSpacesByCompany(
    companyId: string,
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    isActive?: boolean
  ): Promise<{ data: ISpace[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = { company: companyId };
    if (isActive !== undefined) query.isActive = isActive;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [spaces, total] = await Promise.all([
      Space.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Space.countDocuments(query),
    ]);

    return {
      data: spaces,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getPublicSpaces(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    city?: string,
    minCapacity?: number,
    maxPricePerHour?: number,
    amenities?: string[]
  ): Promise<{ data: ISpace[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = { isActive: true };

    if (city) query.city = new RegExp(city, 'i');
    if (minCapacity) query.capacity = { $gte: minCapacity };
    if (maxPricePerHour) query.pricePerHour = { $lte: maxPricePerHour };
    if (amenities && amenities.length > 0) query.amenities = { $all: amenities };

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [spaces, total] = await Promise.all([
      Space.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Space.countDocuments(query),
    ]);

    return {
      data: spaces,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async updateSpace(spaceId: string, data: UpdateSpaceData, managerId: string): Promise<ISpace> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const user = await require('../models/user.model').User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can update spaces.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only update spaces for your own company.');
    }

    if (data.name) space.name = data.name;
    if (data.description) space.description = data.description;
    if (data.address) space.address = data.address;
    if (data.city) space.city = data.city;
    if (data.capacity !== undefined) space.capacity = data.capacity;
    if (data.amenities) space.amenities = data.amenities;
    if (data.images) space.images = data.images;
    if (data.pricePerHour !== undefined) space.pricePerHour = data.pricePerHour;
    if (data.pricePerDay !== undefined) space.pricePerDay = data.pricePerDay;
    if (data.isActive !== undefined) space.isActive = data.isActive;

    await space.save();
    return space;
  }

  async deleteSpace(spaceId: string, managerId: string): Promise<{ message: string }> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const user = await require('../models/user.model').User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can delete spaces.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only delete spaces for your own company.');
    }

    await Space.findByIdAndDelete(spaceId);
    return { message: 'Space deleted successfully.' };
  }

  async toggleSpaceActive(spaceId: string, managerId: string): Promise<ISpace> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const user = await require('../models/user.model').User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can toggle space status.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only toggle spaces for your own company.');
    }

    space.isActive = !space.isActive;
    await space.save();
    return space;
  }
}

export const spaceService = new SpaceService();


===== EXISTING FILE: backend/src/services/user.service.ts =====
import { User, IUser } from '../models/user.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus } from '../types';
import { hashPassword, validatePasswordPolicy } from '../utils/password';
import mongoose, { ClientSession } from 'mongoose';

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

export interface UserProfile {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  company?: string;
  createdAt: Date;
  updatedAt: Date;
}

export class UserService {
  async getProfile(userId: string): Promise<UserProfile> {
    const user = await User.findById(userId).lean();
    if (!user) {
      throw AppError.notFound('User not found');
    }

    return this.mapToProfile(user);
  }

  async updateProfile(userId: string, data: UpdateProfileData): Promise<UserProfile> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (data.email) {
      const existingUser = await User.findOne({
        email: data.email.toLowerCase(),
        _id: { $ne: userId },
      }).lean();

      if (existingUser) {
        throw AppError.conflict('An account with that email address already exists.');
      }
      user.email = data.email.toLowerCase();
    }

    if (data.firstName) user.firstName = data.firstName;
    if (data.lastName) user.lastName = data.lastName;
    if (data.phone) user.phone = data.phone;
    if (data.profileImage) user.profileImage = data.profileImage;

    await user.save();
    return this.mapToProfile(user);
  }

  async changePassword(userId: string, data: ChangePasswordData): Promise<{ message: string }> {
    if (data.newPassword !== data.confirmPassword) {
      throw AppError.badRequest('The two passwords do not match.', [{ field: 'confirmPassword', message: 'The two passwords do not match.' }]);
    }

    const passwordValidation = validatePasswordPolicy(data.newPassword);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    const user = await User.findById(userId).select('+passwordHash');
    if (!user) {
      throw AppError.notFound('User not found');
    }

    const isValid = await require('../utils/password').verifyPassword(data.currentPassword, user.passwordHash);
    if (!isValid) {
      throw AppError.badRequest('Current password is incorrect.', [{ field: 'currentPassword', message: 'Current password is incorrect.' }]);
    }

    user.passwordHash = await hashPassword(data.newPassword);
    await user.save();

    return { message: 'Password changed successfully.' };
  }

  async deleteProfileImage(userId: string): Promise<{ message: string; profileImage: string }> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    const oldImage = user.profileImage;
    user.profileImage = 'default-avatar.png';
    await user.save();

    return { message: 'Profile image reset to default.', profileImage: user.profileImage };
  }

  async getUsers(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    role?: UserRole,
    status?: UserStatus
  ): Promise<{ data: UserProfile[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (role) query.role = role;
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [users, total] = await Promise.all([
      User.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      User.countDocuments(query),
    ]);

    return {
      data: users.map(u => this.mapToProfile(u)),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getUserById(userId: string): Promise<UserProfile> {
    const user = await User.findById(userId).lean();
    if (!user) {
      throw AppError.notFound('User not found');
    }
    return this.mapToProfile(user);
  }

  async updateUserStatus(userId: string, status: UserStatus, adminId: string): Promise<UserProfile> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user._id.toString() === adminId) {
      throw AppError.badRequest('You cannot change your own status.');
    }

    user.status = status;
    await user.save();

    return this.mapToProfile(user);
  }

  async updateUserRole(userId: string, role: UserRole, adminId: string): Promise<UserProfile> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user._id.toString() === adminId) {
      throw AppError.badRequest('You cannot change your own role.');
    }

    user.role = role;
    await user.save();

    return this.mapToProfile(user);
  }

  async deleteUser(userId: string, adminId: string): Promise<{ message: string }> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user._id.toString() === adminId) {
      throw AppError.badRequest('You cannot delete your own account.');
    }

    await User.findByIdAndDelete(userId);
    return { message: 'User deleted successfully.' };
  }

  private mapToProfile(user: IUser & { _id: mongoose.Types.ObjectId }): UserProfile {
    return {
      id: user._id.toString(),
      username: user.username,
      firstName: user.firstName,
      lastName: user.lastName,
      phone: user.phone,
      email: user.email,
      role: user.role,
      status: user.status,
      profileImage: user.profileImage,
      company: user.company?.toString(),
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
    };
  }
}

export const userService = new UserService();

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
