# Task: generate the application entry point

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

- Every file in this stage belongs under `backend/`.

### Files to produce in this stage

- `backend/src/app.ts` — the Express application: middleware chain, router
  mounting, 404 handler, error handler
- `backend/src/server.ts` — the entry point: connect to MongoDB, run the
  bootstrap, start listening, handle shutdown signals
- `backend/src/seed/bootstrap.ts` — the initial-administrator bootstrap
  described below, only if the specification has an administrator role
- `backend/.env` — real local values matching `.env.example`

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

## Existing code — middlewares, routers and models

These files already exist. Import from them, match their exports exactly, and
do not restate them in your answer unless you are deliberately changing one —
in which case return the complete changed file.

================ BEGIN EXISTING CODE ================


===== EXISTING FILE: backend/src/config/database.ts =====
import mongoose from 'mongoose';
import { env } from './env';

let isConnected = false;

export async function connectDatabase(): Promise<void> {
  if (isConnected) {
    return;
  }

  try {
    await mongoose.connect(env.mongodbUri, {
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    });

    isConnected = true;
    console.log('MongoDB connected successfully');

    mongoose.connection.on('error', (err) => {
      console.error('MongoDB connection error:', err);
      isConnected = false;
    });

    mongoose.connection.on('disconnected', () => {
      console.warn('MongoDB disconnected');
      isConnected = false;
    });

    process.on('SIGINT', async () => {
      await mongoose.connection.close();
      console.log('MongoDB connection closed due to app termination');
      process.exit(0);
    });
  } catch (error) {
    console.error('Failed to connect to MongoDB:', error);
    throw error;
  }
}

export function getConnectionStatus(): boolean {
  return isConnected && mongoose.connection.readyState === 1;
}


===== EXISTING FILE: backend/src/config/env.ts =====
import dotenv from 'dotenv';

dotenv.config();

interface EnvConfig {
  port: number;
  nodeEnv: string;
  mongodbUri: string;
  jwtSecret: string;
  jwtAccessTokenTtl: string;
  jwtRefreshTokenTtl: string;
  passwordResetTokenTtl: string;
  uploadDir: string;
  maxFileSize: number;
  corsOrigin: string;
}

function getEnv(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

function getEnvNumber(key: string): number {
  const value = getEnv(key);
  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    throw new Error(`Environment variable ${key} must be a number, got: ${value}`);
  }
  return parsed;
}

export const env: EnvConfig = {
  port: getEnvNumber('PORT'),
  nodeEnv: getEnv('NODE_ENV'),
  mongodbUri: getEnv('MONGODB_URI'),
  jwtSecret: getEnv('JWT_SECRET'),
  jwtAccessTokenTtl: getEnv('JWT_ACCESS_TOKEN_TTL'),
  jwtRefreshTokenTtl: getEnv('JWT_REFRESH_TOKEN_TTL'),
  passwordResetTokenTtl: getEnv('PASSWORD_RESET_TOKEN_TTL'),
  uploadDir: getEnv('UPLOAD_DIR'),
  maxFileSize: getEnvNumber('MAX_FILE_SIZE'),
  corsOrigin: getEnv('CORS_ORIGIN'),
};


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


===== EXISTING FILE: backend/src/utils/asyncHandler.ts =====
import { Request, Response, NextFunction } from 'express';

export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<void>
): (req: Request, res: Response, next: NextFunction) => void {
  return (req: Request, res: Response, next: NextFunction): void => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
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


===== EXISTING FILE: backend/src/routers/admin.routes.ts =====
/**
 * Routes declared in this file:
 * GET    /api/admin/statistics
 * GET    /api/admin/registration-requests
 * POST   /api/admin/registration-requests/:requestId/approve
 * POST   /api/admin/registration-requests/:requestId/reject
 * GET    /api/admin/users
 * GET    /api/admin/users/:userId
 * PUT    /api/admin/users/:userId/status
 * PUT    /api/admin/users/:userId/role
 * DELETE /api/admin/users/:userId
 * GET    /api/admin/companies
 * GET    /api/admin/spaces
 * GET    /api/admin/reservations
 */

import { Router } from 'express';
import { adminController } from '../controllers/admin.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { param, query } from 'express-validator';
import { UserRole, UserStatus } from '../types';

const router = Router();

/**
 * Get system statistics (admin only)
 */
router.get(
  '/statistics',
  authenticate,
  authorize(UserRole.ADMIN),
  adminController.getStatistics
);

/**
 * List pending registration requests (admin only)
 */
router.get(
  '/registration-requests',
  authenticate,
  authorize(UserRole.ADMIN),
  adminController.getPendingRegistrations
);

/**
 * Approve a registration request (admin only)
 */
router.post(
  '/registration-requests/:requestId/approve',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  adminController.approveRegistration
);

/**
 * Reject a registration request (admin only)
 */
router.post(
  '/registration-requests/:requestId/reject',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  adminController.rejectRegistration
);

/**
 * List all users (admin only)
 */
router.get(
  '/users',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('role').optional().isIn(Object.values(UserRole)).withMessage('Invalid role.'),
    query('status').optional().isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  adminController.getUsers
);

/**
 * Get user by ID (admin only)
 */
router.get(
  '/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  adminController.getUserById
);

/**
 * Update user status (admin only)
 */
router.put(
  '/users/:userId/status',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('status').isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  adminController.updateUserStatus
);

/**
 * Update user role (admin only)
 */
router.put(
  '/users/:userId/role',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('role').isIn(Object.values(UserRole)).withMessage('Invalid role.'),
  ]),
  adminController.updateUserRole
);

/**
 * Delete user (admin only)
 */
router.delete(
  '/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  adminController.deleteUser
);

/**
 * List all companies (admin only)
 */
router.get(
  '/companies',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
  ]),
  adminController.getCompanies
);

/**
 * List all spaces (admin only)
 */
router.get(
  '/spaces',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('isActive').optional().isBoolean().withMessage('isActive must be a boolean.'),
  ]),
  adminController.getSpaces
);

/**
 * List all reservations (admin only)
 */
router.get(
  '/reservations',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('status').optional().isString(),
  ]),
  adminController.getReservations
);

export default router;


===== EXISTING FILE: backend/src/routers/auth.routes.ts =====
/**
 * Routes declared in this file:
 * POST   /api/auth/login
 * POST   /api/auth/admin/login
 * POST   /api/auth/forgot-password
 * GET    /api/auth/reset-password/:token
 * POST   /api/auth/reset-password/:token
 * POST   /api/auth/refresh
 * POST   /api/auth/logout
 * GET    /api/auth/me
 */

import { Router } from 'express';
import { authController } from '../controllers/auth.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { body, param } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Public sign-in for Members and Space Managers
 */
router.post(
  '/login',
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
  ]),
  authController.login
);

/**
 * Administrator sign-in through dedicated route
 */
router.post(
  '/admin/login',
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
  ]),
  authController.adminLogin
);

/**
 * Request password reset link
 */
router.post(
  '/forgot-password',
  validate([
    body('identifier').isString().notEmpty().withMessage('Username or email is required.'),
  ]),
  authController.requestPasswordReset
);

/**
 * Verify password reset token (shows new-password form)
 */
router.get(
  '/reset-password/:token',
  validate([
    param('token').isString().notEmpty().withMessage('Reset token is required.'),
  ]),
  authController.verifyPasswordResetToken
);

/**
 * Confirm password reset with new password
 */
router.post(
  '/reset-password/:token',
  validate([
    param('token').isString().notEmpty().withMessage('Reset token is required.'),
    body('newPassword').isString().notEmpty().withMessage('New password is required.'),
    body('confirmPassword').isString().notEmpty().withMessage('Confirm password is required.'),
  ]),
  authController.confirmPasswordReset
);

/**
 * Refresh access token using refresh token
 */
router.post(
  '/refresh',
  validate([
    body('refreshToken').isString().notEmpty().withMessage('Refresh token is required.'),
  ]),
  authController.refreshAccessToken
);

/**
 * Sign out (client discards tokens)
 */
router.post('/logout', authController.logout);

/**
 * Get current authenticated user profile
 */
router.get('/me', authenticate, authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN), authController.getMe);

export default router;


===== EXISTING FILE: backend/src/routers/company.routes.ts =====
/**
 * Routes declared in this file:
 * POST   /api/companies
 * GET    /api/companies/:companyId
 * GET    /api/admin/companies
 * PUT    /api/admin/companies/:companyId
 * DELETE /api/admin/companies/:companyId
 * GET    /api/companies/:companyId/managers/count
 * GET    /api/admin/companies/:companyNumber/pending-managers/count
 */

import { Router } from 'express';
import { companyController } from '../controllers/company.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { body, param, query } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Create a new company (admin or manager)
 */
router.post(
  '/companies',
  authenticate,
  authorize(UserRole.ADMIN, UserRole.MANAGER),
  validate([
    body('name').isString().notEmpty().withMessage('Company name is required.'),
    body('headquartersAddress').isString().notEmpty().withMessage('Headquarters address is required.'),
    body('companyNumber').isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
    body('taxId').isString().matches(/^[1-9]\d{8}$/).withMessage('Tax ID must be exactly 9 digits and must not begin with zero.'),
  ]),
  companyController.createCompany
);

/**
 * Get company by ID (authenticated user)
 */
router.get(
  '/companies/:companyId',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
  ]),
  companyController.getCompanyById
);

/**
 * List all companies (admin only)
 */
router.get(
  '/admin/companies',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
  ]),
  companyController.getCompanies
);

/**
 * Update company (admin only)
 */
router.put(
  '/admin/companies/:companyId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
    body('name').optional().isString().notEmpty().withMessage('Company name cannot be empty.'),
    body('headquartersAddress').optional().isString().notEmpty().withMessage('Headquarters address cannot be empty.'),
    body('companyNumber').optional().isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
    body('taxId').optional().isString().matches(/^[1-9]\d{8}$/).withMessage('Tax ID must be exactly 9 digits and must not begin with zero.'),
  ]),
  companyController.updateCompany
);

/**
 * Delete company (admin only)
 */
router.delete(
  '/admin/companies/:companyId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
  ]),
  companyController.deleteCompany
);

/**
 * Get approved managers count for a company (admin or manager)
 */
router.get(
  '/companies/:companyId/managers/count',
  authenticate,
  authorize(UserRole.ADMIN, UserRole.MANAGER),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
  ]),
  companyController.getCompanyManagersCount
);

/**
 * Get pending managers count for a company by company number (admin only)
 */
router.get(
  '/admin/companies/:companyNumber/pending-managers/count',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('companyNumber').isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
  ]),
  companyController.getCompanyPendingManagersCount
);

export default router;


===== EXISTING FILE: backend/src/routers/registration.routes.ts =====
/**
 * Routes declared in this file:
 * POST   /api/auth/register/member
 * POST   /api/auth/register/manager
 * GET    /api/admin/registration-requests
 * POST   /api/admin/registration-requests/:requestId/approve
 * POST   /api/admin/registration-requests/:requestId/reject
 * GET    /api/auth/check-username
 * GET    /api/auth/check-email
 */

import { Router } from 'express';
import { registrationController } from '../controllers/registration.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { upload, validateImageDimensions, handleMulterError } from '../middlewares/upload.middleware';
import { body, param, query } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Register a new Member (public)
 */
router.post(
  '/register/member',
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
    body('firstName').isString().notEmpty().withMessage('First name is required.'),
    body('lastName').isString().notEmpty().withMessage('Last name is required.'),
    body('phone').isString().notEmpty().withMessage('Contact phone is required.'),
    body('email').isEmail().withMessage('Enter a valid email address.'),
  ]),
  registrationController.registerMember
);

/**
 * Register a new Space Manager (public)
 */
router.post(
  '/register/manager',
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
    body('firstName').isString().notEmpty().withMessage('First name is required.'),
    body('lastName').isString().notEmpty().withMessage('Last name is required.'),
    body('phone').isString().notEmpty().withMessage('Contact phone is required.'),
    body('email').isEmail().withMessage('Enter a valid email address.'),
    body('companyName').isString().notEmpty().withMessage('Company name is required.'),
    body('headquartersAddress').isString().notEmpty().withMessage('Headquarters address is required.'),
    body('companyNumber').isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
    body('taxId').isString().matches(/^[1-9]\d{8}$/).withMessage('Tax ID must be exactly 9 digits and must not begin with zero.'),
  ]),
  registrationController.registerManager
);

/**
 * List pending registration requests (admin only)
 */
router.get(
  '/admin/registration-requests',
  authenticate,
  authorize(UserRole.ADMIN),
  registrationController.getPendingRequests
);

/**
 * Approve a registration request (admin only)
 */
router.post(
  '/admin/registration-requests/:requestId/approve',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  registrationController.approveRequest
);

/**
 * Reject a registration request (admin only)
 */
router.post(
  '/admin/registration-requests/:requestId/reject',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  registrationController.rejectRequest
);

/**
 * Check username availability (public)
 */
router.get(
  '/check-username',
  validateQuery([
    query('username').isString().notEmpty().withMessage('Username query parameter is required.'),
  ]),
  registrationController.checkUsernameAvailability
);

/**
 * Check email availability (public)
 */
router.get(
  '/check-email',
  validateQuery([
    query('email').isEmail().withMessage('Enter a valid email address.'),
  ]),
  registrationController.checkEmailAvailability
);

export default router;


===== EXISTING FILE: backend/src/routers/reservation.routes.ts =====
/**
 * Routes declared in this file:
 * POST   /api/reservations
 * GET    /api/reservations
 * GET    /api/reservations/:reservationId
 * GET    /api/reservations/company
 * POST   /api/reservations/:reservationId/cancel
 * POST   /api/reservations/:reservationId/confirm
 * POST   /api/reservations/:reservationId/complete
 * GET    /api/spaces/:spaceId/availability
 */

import { Router } from 'express';
import { reservationController } from '../controllers/reservation.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { body, param, query } from 'express-validator';
import { UserRole, ReservationStatus } from '../types';

const router = Router();

/**
 * Create a new reservation (authenticated user)
 */
router.post(
  '/reservations',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    body('spaceId').isMongoId().withMessage('Invalid space ID.'),
    body('startTime').isISO8601().withMessage('Start time must be a valid ISO 8601 date.'),
    body('endTime').isISO8601().withMessage('End time must be a valid ISO 8601 date.'),
  ]),
  reservationController.createReservation
);

/**
 * List own reservations (authenticated user)
 */
router.get(
  '/reservations',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('status').optional().isIn(Object.values(ReservationStatus)).withMessage('Invalid status.'),
  ]),
  reservationController.getUserReservations
);

/**
 * Get reservation by ID (authenticated user)
 */
router.get(
  '/reservations/:reservationId',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.getReservationById
);

/**
 * List company reservations (manager or admin)
 */
router.get(
  '/reservations/company',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('status').optional().isIn(Object.values(ReservationStatus)).withMessage('Invalid status.'),
    query('companyId').optional().isMongoId().withMessage('Invalid company ID.'),
  ]),
  reservationController.getCompanyReservations
);

/**
 * Cancel reservation (authenticated user)
 */
router.post(
  '/reservations/:reservationId/cancel',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.cancelReservation
);

/**
 * Confirm reservation (manager or admin)
 */
router.post(
  '/reservations/:reservationId/confirm',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.confirmReservation
);

/**
 * Complete reservation (manager or admin)
 */
router.post(
  '/reservations/:reservationId/complete',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.completeReservation
);

/**
 * Check space availability (public)
 */
router.get(
  '/spaces/:spaceId/availability',
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
    query('startTime').isISO8601().withMessage('Start time must be a valid ISO 8601 date.'),
    query('endTime').isISO8601().withMessage('End time must be a valid ISO 8601 date.'),
  ]),
  reservationController.checkAvailability
);

export default router;


===== EXISTING FILE: backend/src/routers/space.routes.ts =====
/**
 * Routes declared in this file:
 * POST   /api/spaces
 * GET    /api/spaces/public
 * GET    /api/spaces/:spaceId
 * GET    /api/spaces/company
 * PUT    /api/spaces/:spaceId
 * DELETE /api/spaces/:spaceId
 * PATCH  /api/spaces/:spaceId/toggle-active
 */

import { Router } from 'express';
import { spaceController } from '../controllers/space.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { body, param, query } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Create a new space (manager or admin)
 */
router.post(
  '/spaces',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    body('name').isString().notEmpty().withMessage('Space name is required.'),
    body('description').isString().notEmpty().withMessage('Description is required.'),
    body('address').isString().notEmpty().withMessage('Address is required.'),
    body('city').isString().notEmpty().withMessage('City is required.'),
    body('capacity').isInt({ min: 1 }).withMessage('Capacity must be at least 1.'),
    body('pricePerHour').isFloat({ min: 0 }).withMessage('Price per hour must be a positive number.'),
    body('amenities').optional().isArray().withMessage('Amenities must be an array.'),
    body('images').optional().isArray().withMessage('Images must be an array.'),
    body('companyId').optional().isMongoId().withMessage('Invalid company ID.'),
  ]),
  spaceController.createSpace
);

/**
 * List public spaces (public)
 */
router.get(
  '/spaces/public',
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('city').optional().isString(),
    query('minCapacity').optional().isInt({ min: 1 }).withMessage('Minimum capacity must be a positive integer.'),
    query('maxPricePerHour').optional().isFloat({ min: 0 }).withMessage('Maximum price per hour must be a positive number.'),
    query('amenities').optional().isString(),
  ]),
  spaceController.getPublicSpaces
);

/**
 * Get space by ID (public)
 */
router.get(
  '/spaces/:spaceId',
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
  ]),
  spaceController.getSpaceById
);

/**
 * List spaces for authenticated user's company (manager or admin)
 */
router.get(
  '/spaces/company',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('isActive').optional().isBoolean().withMessage('isActive must be a boolean.'),
    query('companyId').optional().isMongoId().withMessage('Invalid company ID.'),
  ]),
  spaceController.getSpacesByCompany
);

/**
 * Update space (manager or admin)
 */
router.put(
  '/spaces/:spaceId',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
    body('name').optional().isString().notEmpty().withMessage('Space name cannot be empty.'),
    body('description').optional().isString().notEmpty().withMessage('Description cannot be empty.'),
    body('address').optional().isString().notEmpty().withMessage('Address cannot be empty.'),
    body('city').optional().isString().notEmpty().withMessage('City cannot be empty.'),
    body('capacity').optional().isInt({ min: 1 }).withMessage('Capacity must be at least 1.'),
    body('pricePerHour').optional().isFloat({ min: 0 }).withMessage('Price per hour must be a positive number.'),
    body('amenities').optional().isArray().withMessage('Amenities must be an array.'),
    body('images').optional().isArray().withMessage('Images must be an array.'),
    body('isActive').optional().isBoolean().withMessage('isActive must be a boolean.'),
  ]),
  spaceController.updateSpace
);

/**
 * Delete space (manager or admin)
 */
router.delete(
  '/spaces/:spaceId',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
  ]),
  spaceController.deleteSpace
);

/**
 * Toggle space active status (manager or admin)
 */
router.patch(
  '/spaces/:spaceId/toggle-active',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
  ]),
  spaceController.toggleSpaceActive
);

export default router;


===== EXISTING FILE: backend/src/routers/user.routes.ts =====
/**
 * Routes declared in this file:
 * GET    /api/users/profile
 * PUT    /api/users/profile
 * POST   /api/users/profile/password
 * DELETE /api/users/profile/image
 * POST   /api/users/profile/image
 * GET    /api/admin/users
 * GET    /api/admin/users/:userId
 * PUT    /api/admin/users/:userId/status
 * PUT    /api/admin/users/:userId/role
 * DELETE /api/admin/users/:userId
 */

import { Router } from 'express';
import { userController } from '../controllers/user.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { upload, validateImageDimensions, handleMulterError } from '../middlewares/upload.middleware';
import { body, param, query } from 'express-validator';
import { UserRole, UserStatus } from '../types';

const router = Router();

/**
 * Get own profile (authenticated user)
 */
router.get(
  '/profile',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  userController.getProfile
);

/**
 * Update own profile (authenticated user)
 */
router.put(
  '/profile',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  validate([
    body('firstName').optional().isString().notEmpty().withMessage('First name cannot be empty.'),
    body('lastName').optional().isString().notEmpty().withMessage('Last name cannot be empty.'),
    body('phone').optional().isString().notEmpty().withMessage('Contact phone cannot be empty.'),
    body('email').optional().isEmail().withMessage('Enter a valid email address.'),
  ]),
  userController.updateProfile
);

/**
 * Change own password (authenticated user)
 */
router.post(
  '/profile/password',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    body('currentPassword').isString().notEmpty().withMessage('Current password is required.'),
    body('newPassword').isString().notEmpty().withMessage('New password is required.'),
    body('confirmPassword').isString().notEmpty().withMessage('Confirm password is required.'),
  ]),
  userController.changePassword
);

/**
 * Delete own profile image (authenticated user)
 */
router.delete(
  '/profile/image',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  userController.deleteProfileImage
);

/**
 * Upload/replace own profile image (authenticated user)
 */
router.post(
  '/profile/image',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  userController.uploadProfileImage
);

/**
 * List all users (admin only)
 */
router.get(
  '/admin/users',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('role').optional().isIn(Object.values(UserRole)).withMessage('Invalid role.'),
    query('status').optional().isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  userController.getUsers
);

/**
 * Get user by ID (admin only)
 */
router.get(
  '/admin/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  userController.getUserById
);

/**
 * Update user status (admin only)
 */
router.put(
  '/admin/users/:userId/status',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('status').isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  userController.updateUserStatus
);

/**
 * Update user role (admin only)
 */
router.put(
  '/admin/users/:userId/role',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('role').isIn(Object.values(UserRole)).withMessage('Invalid role.'),
  ]),
  userController.updateUserRole
);

/**
 * Delete user (admin only)
 */
router.delete(
  '/admin/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  userController.deleteUser
);

export default router;

================= END EXISTING CODE =================

## Files already on disk

```
  backend/.env.example
  backend/.gitignore
  backend/package.json
  backend/src/config/database.ts
  backend/src/config/env.ts
  backend/src/controllers/admin.controller.ts
  backend/src/controllers/auth.controller.ts
  backend/src/controllers/company.controller.ts
  backend/src/controllers/index.ts
  backend/src/controllers/registration.controller.ts
  backend/src/controllers/reservation.controller.ts
  backend/src/controllers/space.controller.ts
  backend/src/controllers/user.controller.ts
  backend/src/middlewares/auth.middleware.ts
  backend/src/middlewares/authorize.middleware.ts
  backend/src/middlewares/error.middleware.ts
  backend/src/middlewares/upload.middleware.ts
  backend/src/middlewares/validate.middleware.ts
  backend/src/models/company.model.ts
  backend/src/models/index.ts
  backend/src/models/password-reset-token.model.ts
  backend/src/models/registration-request.model.ts
  backend/src/models/reservation.model.ts
  backend/src/models/space.model.ts
  backend/src/models/user.model.ts
  backend/src/routers/admin.routes.ts
  backend/src/routers/auth.routes.ts
  backend/src/routers/company.routes.ts
  backend/src/routers/registration.routes.ts
  backend/src/routers/reservation.routes.ts
  backend/src/routers/space.routes.ts
  backend/src/routers/user.routes.ts
  backend/src/services/admin.service.ts
  backend/src/services/auth.service.ts
  backend/src/services/company.service.ts
  backend/src/services/index.ts
  backend/src/services/registration.service.ts
  backend/src/services/reservation.service.ts
  backend/src/services/space.service.ts
  backend/src/services/user.service.ts
  backend/src/types/index.ts
  backend/src/utils/AppError.ts
  backend/src/utils/asyncHandler.ts
  backend/src/utils/password.ts
  backend/src/utils/token.ts
  backend/tsconfig.json
```

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
