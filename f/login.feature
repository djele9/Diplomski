Feature: Authentication

Scenario: Successful member login
Given a registered member exists in the system
And the member is on the public login page
When the member enters a valid username
And the member enters a valid password
And the member confirms the login
Then the member is successfully logged in
And the main member menu is displayed

Scenario: Login with an incorrect password
Given a registered member exists in the system
When the member enters a valid username
And the member enters an incorrect password
And the member confirms the login
Then the login is unsuccessful
And an appropriate error message is displayed

Scenario: Login with a non-existent user
Given the user does not exist in the system
When the user enters a non-existent username
And the user enters a password
And the user confirms the login
Then the login is unsuccessful
And an error message is displayed

Scenario: Administrator login through a separate route
Given the administrator has an active administrator account
When the administrator accesses the dedicated login route
And the administrator enters valid credentials
And the administrator confirms the login
Then the administrator is successfully logged in
And the administrator interface is displayed

Scenario: Administrator login form is not accessible through the public login form
Given an unregistered user is on the home page
When the user views the public login form
Then there is no publicly displayed option for administrator login
