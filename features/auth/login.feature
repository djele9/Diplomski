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
