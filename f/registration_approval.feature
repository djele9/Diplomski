Feature: Registration Approval

Scenario: Administrator approves a member registration request
Given there is a member registration request pending approval
And the administrator is logged in
When the administrator opens the list of registration requests
And selects a registration request
And approves the registration
Then the member becomes an active user
And the member can log in to the system

Scenario: Administrator rejects a member registration request
Given there is a member registration request pending approval
And the administrator is logged in
When the administrator rejects the registration request
Then the member registration is not approved
And the member cannot use the system