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
