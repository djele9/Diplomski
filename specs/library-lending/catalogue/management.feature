Feature: Manage the catalogue

  Background:
    Given I am signed in as a librarian

  @positive @C1
  Scenario: Adding a new title
    When I add a title with author "Herbert", name "Dune", year "1965", and ISBN "4444444444444"
    Then the title "Dune" should be in the catalogue

  @negative @C1 @ui
  Scenario: Adding a title with a duplicate ISBN
    Given a title exists with ISBN "1111111111111"
    When I add a title with author "X", name "Y", year "2000", and ISBN "1111111111111"
    Then I should see an error "ISBN must be unused"

  @positive @C2
  Scenario: Adding copies to a title
    Given a title "1984" exists
    When I add a copy to "1984" with shelf mark "S1"
    Then the title "1984" should have 1 copy

  @negative @C2 @ui
  Scenario: Adding a copy with a duplicate shelf mark
    Given a copy exists with shelf mark "S1"
    When I add a copy to "1984" with shelf mark "S1"
    Then I should see an error "Shelf mark must be unique"

  @positive @C2
  Scenario: Withdrawing a copy not on loan
    Given a copy "S1" exists and is not on loan
    When I withdraw copy "S1"
    Then copy "S1" should be removed from the catalogue

  @negative @C2 @ui
  Scenario: Withdrawing a copy that is on loan
    Given a copy "S1" exists and is on loan
    When I withdraw copy "S1"
    Then I should see an error "Cannot withdraw a copy on loan"

  @positive @C3
  Scenario: Editing a title
    Given a title "1984" exists with ISBN "1111111111111"
    When I edit title "1984" to have name "Nineteen Eighty-Four"
    Then the title should be named "Nineteen Eighty-Four"

  @negative @C3 @ui
  Scenario: Editing a title to a used ISBN
    Given a title "1984" exists with ISBN "1111111111111"
    And a title "Animal Farm" exists with ISBN "2222222222222"
    When I edit title "1984" to have ISBN "2222222222222"
    Then I should see an error "ISBN already in use"
