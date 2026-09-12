Feature: Borrow and renew books

  Background:
    Given I am signed in as a member

  @positive @C8
  Scenario: Borrowing an available copy
    Given a title "1984" exists with a copy "S1" on the shelf
    When I borrow copy "S1"
    Then I should have a loan for "S1" due in 21 days

  @negative @C8 @ui
  Scenario: Borrowing when no copies are available
    Given a title "1984" exists with no copies on the shelf
    When I attempt to borrow "1984"
    Then I should see an error "No copy available"

  @positive @C9
  Scenario: Borrowing the eighth book
    Given I have 7 current loans
    And a title "1984" exists with a copy "S1" on the shelf
    When I borrow copy "S1"
    Then I should have 8 current loans

  @negative @C9 @ui
  Scenario: Borrowing a ninth book
    Given I have 8 current loans
    And a title "1984" exists with a copy "S1" on the shelf
    When I attempt to borrow copy "S1"
    Then I should see an error "Maximum loan limit reached"

  @negative @C10 @ui
  Scenario: Borrowing with a severely overdue loan
    Given I have a loan that is 31 days overdue
    And a title "1984" exists with a copy "S1" on the shelf
    When I attempt to borrow copy "S1"
    Then I should see an error "Overdue loan must be returned"

  @positive @C11
  Scenario: Renewing a loan once
    Given I have a loan for "S1"
    And nobody has reserved the title of "S1"
    When I renew the loan for "S1"
    Then the loan for "S1" should be extended by 21 days

  @negative @C11 @ui
  Scenario: Renewing a loan a second time
    Given I have a loan for "S1" that has been renewed once
    When I attempt to renew the loan for "S1"
    Then I should see an error "Only one renewal permitted"

  @negative @C11 @ui
  Scenario: Renewing a reserved title
    Given I have a loan for "S1"
    And another member has reserved the title of "S1"
    When I attempt to renew the loan for "S1"
    Then I should see an error "Title is reserved"
