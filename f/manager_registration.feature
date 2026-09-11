Feature: Manager Registration

Scenario: Successful manager registration
Given an unregistered user is on the registration page
When the user enters valid personal information
And enters the company name
And enters the headquarters address
And enters an 8-digit company registration number
And enters a valid 9-digit tax identification number
And submits the registration request
Then a manager registration request is created
And the request is pending administrator approval

Scenario: Company registration number does not contain 8 digits
Given the user is registering as a manager
When the user enters a company registration number that does not contain exactly 8 digits
Then the registration is not allowed

Scenario: Tax identification number does not contain 9 digits
Given the user is registering as a manager
When the user enters a tax identification number that does not contain exactly 9 digits
Then the registration is not allowed

Scenario: Tax identification number starts with zero
Given the user is registering as a manager
When the user enters a tax identification number that starts with the digit 0
Then the registration is not allowed

Scenario: Third manager attempts to register for the same company
Given the company already has two active managers
When a third user attempts to register as a manager of the same company
Then the registration is not allowed
