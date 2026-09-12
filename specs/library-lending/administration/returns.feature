Feature: Process returns and fines

  Background:
    Given I am signed in as a librarian

  @positive @C14
  Scenario: Recording a return
    Given a member has a loan for copy "S1"
    When I record the return of copy "S1"
    Then the loan for "S1" should be ended
    And copy "S1" should be available on the shelf

  @positive @C14
  Scenario: Recording a return for a reserved book
    Given a member has a loan for copy "S1"
    And a member is in the queue for the title of "S1"
    When I record the return of copy "S1"
    Then the loan for "S1" should be ended
    And copy "S1" should be held for the reservation

  @positive @C15
  Scenario Outline: Calculating fines for late returns
    Given a member has a loan for "S1" that was due "<days_ago>" days ago
    When I record the return of copy "S1"
    Then the member should be charged a fine of "<fine>"

    Examples:
      | days_ago | fine     |
      | "1"      | "0.20 €"  |
      | "10"     | "2.00 €"  |
      | "61"     | "12.00 €" |

  @positive @C18
  Scenario: Recording a payment
    Given a member has a balance of "25.00 €"
    When I record a payment of "25.00 €" for the member
    Then the member's balance should be "0.00 €"
