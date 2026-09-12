Feature: Sign in to the library system

  @positive @C6 @ui
  Scenario Outline: Signing in with various credentials
    Given a user exists with card number "<card>" and password "<password>" and status "<status>"
    When they sign in with card number "<card>" and password "<password>"
    Then they should see the "<result>" page

    Examples:
      | card   | password | status     | result   |
      | "123"  | "pass1"   | "active"   | "home"   |
      | "123"  | "wrong"   | "active"   | "login"  |
      | "999"  | "pass1"   | "active"   | "login"  |
      | "123"  | "pass1"   | "suspended"| "login"  |

  @positive @C7 @ui
  Scenario: Librarian signs in
    Given a user exists with card number "L01" and password "admin" and status "active" and role "librarian"
    When they sign in with card number "L01" and password "admin"
    Then they should see the "librarian dashboard" page
