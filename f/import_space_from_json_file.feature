Feature: Import Space from JSON File

Scenario: Successfully import JSON configuration
Given the manager is logged in
And has prepared a valid JSON file
When the manager uploads the JSON file
Then the system loads the data
And creates the space configuration

Scenario: Invalid JSON file
Given the manager is logged in
When the manager uploads a JSON file with an invalid structure
Then the configuration is not created
And an error message is displayed