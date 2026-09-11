Feature: Public Coworking Space Search

Scenario: Display total number of active coworking spaces
Given an unregistered user is on the home page
When the page is loaded
Then the total number of registered coworking spaces is displayed

Scenario: Display the five highest-rated coworking spaces
Given there are at least five active coworking spaces
When an unregistered user opens the home page
Then the five highest-rated coworking spaces by number of likes are displayed

Scenario: Search by space name
Given there are active coworking spaces
When an unregistered user enters the name of a space
And starts the search
Then the spaces matching the name are displayed

Scenario: Search across multiple cities
Given active coworking spaces exist in multiple cities
When the user selects multiple cities
And starts the search
Then the spaces located in the selected cities are displayed

Scenario: Search with no results
Given there is no active coworking space matching the search criteria
When the user starts the search
Then an empty result list is displayed
