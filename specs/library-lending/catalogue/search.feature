Feature: Search the catalogue

  Background:
    Given the following titles exist:
      | author   | title        | year | ISBN           |
      | "Orwell" | "1984"       | 1949 | "1111111111111" |
      | "Orwell" | "Animal Farm"| 1945 | "2222222222222" |
      | "Tolkien"| "The Hobbit" | 1937 | "3333333333333" |

  @positive @C4 @ui
  Scenario Outline: Searching by criteria
    Given I am a visitor
    When I search for author "<author>", title "<title>", and year "<year>"
    Then I should see "<expected_count>" results

    Examples:
      | author   | title        | year | expected_count |
      | "Orwell" | ""           | ""   | "2"            |
      | ""       | "1984"       | ""   | "1"            |
      | ""       | ""           | "1937"| "1"            |
      | "Orwell" | "1984"       | "1949"| "1"            |
      | "None"   | "None"       | "0"  | "0"            |

  @positive @C4 @ui
  Scenario: Results are paginated and orderable
    Given I am a visitor
    And 25 titles exist in the catalogue
    When I search for author "", title "", and year "" ordered by "year"
    Then I should see 20 results on the first page
    And the results should be ordered by "year"

  @positive @C5 @ui
  Scenario: Viewing title details
    Given a title "1984" exists with 5 copies total and 2 on loan
    When I open the title "1984"
    Then I should see "3" copies on the shelf
    And I should see "2" copies on loan
