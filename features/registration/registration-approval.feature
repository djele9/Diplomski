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
