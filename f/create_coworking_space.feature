Feature: Create Coworking Space

Scenario: Create a new space
Given the manager is logged in
When the manager enters the space name
And enters the city and address
And enters the hourly reservation price
And enters a number of desks in the open workspace that is at least 5
And confirms the creation
Then a new space is created
And the space has exactly one open workspace
And the space is pending administrator approval

Scenario: Create a space with fewer than 5 desks
Given the manager is creating a new space
When the manager enters a number of desks fewer than 5
Then the space cannot be created

Scenario: Add an office
Given the manager has created a space
When the manager adds a new office
And enters a unique office name
And enters the number of desks
Then the office is added to the space

Scenario: Duplicate office name
Given the space already has an office with a specific name
When the manager attempts to add another office with the same name to that space
Then the office is not added

Scenario: Add a conference room
Given the manager has created a space
When the manager adds a conference room
And enters a unique room name
And enters a description of the additional equipment
Then the conference room is added to the space