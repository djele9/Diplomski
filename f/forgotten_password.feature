Feature: Forgotten Password

Scenario: Password reset request using username
Given the user has an account in the system
When the user selects the forgot password option
And enters their username
And submits the request
Then the system generates a temporary password reset link

Scenario: Password reset request using email address
Given the user has an account in the system
When the user enters their email address
And submits the request
Then the system generates a temporary password reset link

Scenario: Password reset within 30 minutes
Given the user has received a password reset link
And no more than 30 minutes have passed
When the user opens the link
And enters a valid new password
Then the password is successfully changed

Scenario: Expired password reset link
Given the user has received a password reset link
And more than 30 minutes have passed
When the user opens the link
Then the link is no longer valid
And the password is not changed
