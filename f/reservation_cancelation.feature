Feature: Reservation Cancellation

Scenario: Cancel a reservation more than 12 hours in advance
Given the member has a future reservation
And there are at least 12 hours until the reservation starts
When the member clicks the "Cancel" button
Then the reservation is cancelled

Scenario: Cancellation is not possible less than 12 hours in advance
Given the member has a reservation
And there are less than 12 hours until the reservation starts
Then the "Cancel" button is unavailable

