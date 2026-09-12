Feature: View account details

  @positive @C16 @ui
  Scenario: Member views own account
    Given I am signed in as a member
    And I have a loan for "S1" due "2023-12-01"
    And I have a reservation for "1984"
    And I owe "5.00 €"
    When I view my account
    Then I should see the loan for "S1" and due date "2023-12-01"
    And I should see the reservation for "1984"
    And I should see a total balance of "5.00 €"

  @negative @C16 @ui
  Scenario: Member cannot view another member's account
    Given I am signed in as a member
    And another member "M2" exists with loans
    When I attempt to view the account of "M2"
    Then I should see an error "Access denied"

  @positive @C17 @ui
  Scenario: Librarian views member loans
    Given I am signed in as a librarian
    And member "M1" has a loan for "S1"
    When I view the loans of member "M1"
    Then I should see the loan for "S1"

  @positive @C17 @ui
  Scenario: Librarian views overdue loans
    Given I am signed in as a librarian
    And member "M1" has a loan overdue by 5 days
    And member "M2" has a loan overdue by 10 days
    When I view all overdue loans
    Then I should see the loan for "M2" before the loan for "M1"

  @negative @C18 @ui
  Scenario: Suspended member cannot borrow
    Given I am signed in as a member
    And I owe "20.01 €"
    And a title "1984" exists with a copy "S1" on the shelf
    When I attempt to borrow copy "S1"
    Then I should see an error "Account suspended due to fines"
