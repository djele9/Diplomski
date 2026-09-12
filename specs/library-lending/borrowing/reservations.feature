Feature: Reserve titles

  Background:
    Given I am signed in as a member

  @positive @C12
  Scenario: Reserving a title with no available copies
    Given a title "1984" exists and all copies are on loan
    When I reserve the title "1984"
    Then I should be in the queue for "1984"

  @negative @C12 @ui
  Scenario: Reserving a title already on loan to the member
    Given I have a loan for a copy of "1984"
    And all other copies of "1984" are on loan
    When I attempt to reserve the title "1984"
    Then I should see an error "You already have a copy of this title"

  @positive @C13
  Scenario: Notification upon return
    Given I am the first member in the queue for "1984"
    When a copy "S1" of "1984" is returned
    Then I should receive an email notification
    And copy "S1" should be held for me for 3 days
