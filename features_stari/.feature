# Coworking Hub Manager — Gherkin Specification

Feature: Authentication

  Scenario: Successful member login
    Given a registered member exists in the system
    And the member is on the public login page
    When the member enters the correct username
    And enters the correct password
    And confirms the login
    Then the member is successfully logged in
    And the member menu is displayed

  Scenario: Login with an incorrect password
    Given a registered member exists in the system
    When the member enters the correct username
    And enters an incorrect password
    And confirms the login
    Then the login is unsuccessful
    And an appropriate error message is displayed

  Scenario: Login with a non-existent user
    Given the user does not exist in the system
    When the user enters a non-existent username
    And enters a password
    And confirms the login
    Then the login is unsuccessful
    And an error message is displayed

  Scenario: Administrator login through a separate route
    Given the administrator has an active administrator account
    When the administrator accesses the dedicated login route
    And enters the correct credentials
    And confirms the login
    Then the administrator is successfully logged in
    And the administrator interface is displayed

  Scenario: Administrator login form is not available through the public form
    Given an unregistered user is on the home page
    When the user views the public login form
    Then there is no publicly displayed option for administrator login


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
    Then registration is not allowed
    And a message indicating that the username is already taken is displayed

  Scenario: Registration with an existing email address
    Given the email address already belongs to a user account
    When the user attempts to register with the same email address
    Then registration is not allowed

  Scenario: Registration without a profile picture
    Given the user has entered valid registration details
    When the user does not upload a profile picture
    And submits the registration request
    Then the registration request is successfully created
    And the user is assigned a default profile picture


Feature: Password Validation

  Scenario: Password shorter than 8 characters
    Given the user is registering
    When the user enters a password shorter than 8 characters
    Then registration is not allowed
    And an invalid password message is displayed

  Scenario: Password longer than 12 characters
    Given the user is registering
    When the user enters a password longer than 12 characters
    Then registration is not allowed

  Scenario: Password without an uppercase letter
    Given the user is registering
    When the user enters a password without an uppercase letter
    Then registration is not allowed

  Scenario: Password without a number
    Given the user is registering
    When the user enters a password without a number
    Then registration is not allowed

  Scenario: Password without a special character
    Given the user is registering
    When the user enters a password without a special character
    Then registration is not allowed

  Scenario: Password does not start with a letter
    Given the user is registering
    When the user enters a password that starts with a number or special character
    Then registration is not allowed


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
    Then registration is not allowed

  Scenario: Tax identification number does not contain exactly 9 digits
    Given the user is registering as a manager
    When the user enters a tax identification number that does not contain exactly 9 digits
    Then registration is not allowed

  Scenario: Tax identification number starts with zero
    Given the user is registering as a manager
    When the user enters a tax identification number that starts with the digit 0
    Then registration is not allowed

  Scenario: Third manager of the same company attempts to register
    Given the company already has two active managers
    When a third user attempts to register as a manager of the same company
    Then registration is not allowed


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


Feature: Public Coworking Space Search

  Scenario: Display total number of active coworking spaces
    Given an unregistered user is on the home page
    When the page is loaded
    Then the total number of registered coworking spaces is displayed

  Scenario: Display the five highest-rated coworking spaces
    Given there are at least five active coworking spaces
    When an unregistered user opens the home page
    Then the five highest-rated coworking spaces by number of likes are displayed

  Scenario: Search by space name
    Given there are active coworking spaces
    When an unregistered user enters the name of a space
    And starts the search
    Then the spaces matching the name are displayed

  Scenario: Search across multiple cities
    Given active coworking spaces exist in multiple cities
    When the user selects multiple cities
    And starts the search
    Then the spaces located in the selected cities are displayed

  Scenario: Search with no results
    Given there is no active coworking space matching the search criteria
    When the user starts the search
    Then an empty result list is displayed


Feature: Coworking Space Details

  Scenario: Display coworking space details
    Given the user has received a list of search results
    When the user clicks the "DETAILS" button
    Then the name of the space is displayed
    And the city is displayed
    And the address is displayed
    And the company managing the space is displayed
    And the space manager is displayed
    And the number of likes and dislikes is displayed
    And an image gallery is displayed

  Scenario: Preview a thumbnail image
    Given the space has additional thumbnail images
    When the user selects a thumbnail
    Then the selected image is displayed as the main image

  Scenario: Remember the selected main image
    Given the user has selected an image of the space
    When the image becomes the main image
    Then the selection is stored in a web browser cookie


Feature: Member Profile

  Scenario: View member profile
    Given the member is successfully logged in
    When the member opens their profile
    Then their personal information is displayed
    And their profile picture is displayed
    And their previous and current reservations are displayed

  Scenario: Update personal information
    Given the member is on their profile page
    When the member modifies an allowed personal detail
    And saves the changes
    Then the information is successfully updated

  Scenario: Change username
    Given the member is on their profile page
    When the member attempts to change the username
    Then the change is not allowed

  Scenario: Change profile picture
    Given the member is on their profile page
    When the member selects a new profile picture
    And saves the changes
    Then the new profile picture is displayed on the profile


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


Feature: Space Rating and Comments

  Scenario: Member likes a space after a confirmed reservation
    Given the member has had at least one confirmed reservation at the space
    When the member selects "like"
    Then the like is registered for that member

  Scenario: Member cannot rate a space without a reservation
    Given the member has not had a confirmed reservation at the space
    When the member attempts to leave a like or dislike
    Then the action is not allowed

  Scenario: Member leaves a comment
    Given the member has had at least one confirmed reservation at the space
    When the member enters a comment
    And confirms the comment
    Then the comment is saved
    And the comment contains the username and the date it was posted

  Scenario: Display the last ten comments
    Given the space has more than ten comments
    When the user opens the space details
    Then the last ten comments are displayed

  Scenario: Display the member's own comments
    Given the member has left a comment
    When the member opens the space details page
    Then their comment is visually highlighted with a different border


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


Feature: Create Coworking Space

  Scenario: Create a new space
    Given the manager is logged in
    When the manager enters the space name
    And enters the city and address
    And enters the hourly reservation price
    And enters a number of desks in the open workspace that is at least 5
    And confirms the creation
    Then a new space is created
    And the space has exactly one open workspace
    And the space is pending administrator approval

  Scenario: Create a space with fewer than 5 desks
    Given the manager is creating a new space
    When the manager enters a number of desks fewer than 5
    Then the space cannot be created

  Scenario: Add an office
    Given the manager has created a space
    When the manager adds a new office
    And enters a unique office name
    And enters the number of desks
    Then the office is added to the space

  Scenario: Duplicate office name
    Given the space already has an office with a specific name
    When the manager attempts to add another office with the same name to that space
    Then the office is not added

  Scenario: Add a conference room
    Given the manager has created a space
    When the manager adds a conference room
    And enters a unique room name
    And enters a description of the additional equipment
    Then the conference room is added to the space


Feature: Import Space from JSON File

  Scenario: Successfully import JSON configuration
    Given the manager is logged in
    And has prepared a valid JSON file
    When the manager uploads the JSON file
    Then the system loads the data
    And creates the space configuration

  Scenario: Invalid JSON file
    Given the manager is logged in
    When the manager uploads a JSON file with an invalid structure
    Then the configuration is not created
    And an error message is displayed


Feature: Manager Reservation Management

  Scenario: View reservations
    Given the manager is logged in
    And their space has reservations
    When the manager opens the reservation view
    Then the reservations of members in their spaces are displayed

  Scenario: Confirm member arrival
    Given there is a member reservation
    And the reserved time slot has started
    And no more than 10 minutes have passed since the start of the time slot
    When the manager clicks "Confirm"
    Then the reservation is marked as confirmed

  Scenario: Mark member as a no-show
    Given there is a member reservation
    And no more than 10 minutes have passed since the start of the time slot
    And the member has not shown up
    When the manager clicks "Mark as No-Show"
    Then the reservation is marked as a no-show

  Scenario: Automatically prevent booking after exceeding the no-show limit
    Given the member has reached the allowed number of no-shows for the space
    When the member attempts to reserve that space
    Then the reservation is not allowed


Feature: Manager Calendar

  Scenario: View the calendar of a specific resource
    Given the manager is logged in
    When the manager selects a space
    And selects a resource of the space
    Then an interactive calendar for that resource is displayed

  Scenario: Move a time slot using drag-and-drop
    Given the manager is viewing the calendar of an office or conference room
    And there is an existing time slot
    When the manager drags the time slot to another allowed time slot
    Then the time slot is moved to the new time slot


Feature: Reporting

  Scenario: Generate a monthly PDF report
    Given the manager is logged in
    And there is reservation data for a specific month
    When the manager selects a month
    And requests the report to be generated
    Then the system generates a PDF report
    And the report contains capacity utilization percentages


Feature: Administrator User Management

  Scenario: View all users
    Given the administrator is logged in
    When the administrator opens user management
    Then the user accounts in the system are displayed

  Scenario: Update a user account
    Given the administrator is logged in
    And a user account exists
    When the administrator modifies the allowed data
    And saves the changes
    Then the user's data is updated

  Scenario: Delete a user account
    Given the administrator is logged in
    And a user account exists
    When the administrator selects delete
    And confirms the action
    Then the user account is deleted


Feature: Coworking Space Approval

  Scenario: Administrator approves a new space
    Given the manager has created a new space
    And the space is pending approval
    When the administrator opens the list of spaces pending approval
    And approves the space
    Then the space becomes active
    And the space becomes visible to other users

  Scenario: Reject a new space
    Given there is a space pending approval
    When the administrator rejects the space
    Then the space is not activated
    And it is not visible to other users


Feature: Administrator Statistics

  Scenario: Display space popularity
    Given the administrator is logged in
    And there are active coworking spaces
    When the administrator opens statistics
    Then a space popularity chart is displayed

  Scenario: Display space revenue
    Given there is reservation data
    When the administrator opens revenue statistics
    Then revenue for each space is displayed separately


Feature: Logout

  Scenario: Successful logout
    Given the user is logged in
    When the user selects the "Log out" option
    Then the user is logged out
    And no longer has access to functionality intended for logged-in users


Feature: Input Validation

  Scenario: Server rejects invalid data
    Given the user sends data to the server
    When one or more fields contain invalid values
    Then the server rejects the request
    And the data is not stored in the system

  Scenario: Responsive layout for different screen sizes
    Given the user accesses the application from a small screen
    When the user opens any page
    Then the content is adapted to the screen size
    And the basic functionality is available to the user