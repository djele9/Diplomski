Feature: Member Space Search

Scenario: Select an open workspace
Given the member is logged in
When the member selects the "open workspace desk" option
Then the office and conference room options become unavailable

Scenario: Select a private office
Given the member is logged in
When the member selects the "private office" option
Then the open workspace and conference room options become unavailable
And a field for the number of people is displayed

Scenario: Select a conference room
Given the member is logged in
When the member selects the "conference room" option
Then the open workspace and office options become unavailable

Scenario: Display extended space details
Given the member has performed a search
When the member clicks the "DETAILS" button
Then a longer description of the space is displayed
And an image gallery is displayed
And an interactive map is displayed
And the location of the space is marked on the map
