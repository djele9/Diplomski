Feature: Member Registration

Scenario: Successfully submitting a registration request
Given an unregistered user is on the registration page
When the user enters a unique username
And enters a valid password
And enters their first and last name
And enters a contact phone number
And enters a unique email address
And uploads a valid profile picture
And confirms the registration
Then a registration request is created
And the request has the status "pending"

Scenario: Registration with an existing username
Given the username already exists in the system
When the user attempts to register with the same username
Then the registration is not allowed
And a message indicating that the username is already taken is displayed

Scenario: Registration with an existing email address
Given the email address already belongs to a user account
When the user attempts to register with the same email address
Then the registration is not allowed

Scenario: Registration without a profile picture
Given the user has entered valid registration details
When the user does not upload a profile picture
And submits the registration request
Then the registration request is successfully created
And the user is assigned a default profile picture
