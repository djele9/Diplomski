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
