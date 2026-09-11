Feature: Manager Profile

Scenario: View manager profile
Given the manager is successfully logged in
When the manager opens their profile
Then their personal information is displayed
And their profile picture is displayed
And the spaces offered by their company are displayed

Scenario: Manager cannot change username
Given the manager is on the profile page
When the manager attempts to change the username
Then the change is not allowed