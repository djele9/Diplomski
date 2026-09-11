Feature: Password Validation

Scenario: Password shorter than 8 characters
Given the user is registering
When the user enters a password shorter than 8 characters
Then the registration is not allowed
And an invalid password message is displayed

Scenario: Password longer than 12 characters
Given the user is registering
When the user enters a password longer than 12 characters
Then the registration is not allowed

Scenario: Password without an uppercase letter
Given the user is registering
When the user enters a password without an uppercase letter
Then the registration is not allowed

Scenario: Password without a number
Given the user is registering
When the user enters a password without a number
Then the registration is not allowed

Scenario: Password without a special character
Given the user is registering
When the user enters a password without a special character
Then the registration is not allowed

Scenario: Password does not start with a letter
Given the user is registering
When the user enters a password that starts with a number or special character
Then the registration is not allowed
