Feature: Reservation

Scenario: Display available and occupied time slots
Given the member has selected a space
And has selected a resource type
When the member opens the calendar
Then the time slots for the current week are displayed
And occupied time slots are marked as occupied

Scenario: Reserve an available time slot
Given the member has selected an available time slot
When the member confirms the reservation
Then the reservation is created
And the time slot is no longer available to other members

Scenario: Attempt to reserve an occupied time slot
Given the time slot is already reserved
When the member attempts to reserve the same time slot
Then the reservation is not allowed

Scenario: Rotate calendars for multiple offices
Given the space has multiple available offices that meet the criteria
When the member clicks the button to move to the next office
Then the calendar for the next office is displayed

Scenario: Rotate calendars for multiple conference rooms
Given the space has multiple conference rooms
When the member clicks the button to move to the next conference room
Then the calendar for the next conference room is displayed
