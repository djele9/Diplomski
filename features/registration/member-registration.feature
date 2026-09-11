@registration @vibe-part-1 @zero-shot
Feature: Member registration
  As a visitor
  I want to register as a Member of the coworking network
  So that after an Administrator approves me I can search for and reserve workspaces

  Registration never creates an active account directly: it creates a
  registration request with status PENDING that an Administrator must decide on.

  Background:
    Given the following users already exist:
      | username  | email               |
      | ana.jovic | ana.jovic@primer.rs |
    And a Guest is on the route "/register"
    And the Guest has selected the account type "Member"

  @positive @api
  Scenario: A visitor registers with complete, valid data
    When the Guest submits the registration form with:
      | field         | value                 |
      | username      | pera.peric            |
      | password      | Pera#2026ab           |
      | firstName     | Petar                 |
      | lastName      | Peric                 |
      | phone         | +381641234567         |
      | email         | pera.peric@primer.rs  |
    And the Guest attaches the profile image "avatar-200x200.png"
    Then the registration succeeds with HTTP status 201
    And a registration request for "pera.peric" is created with status "PENDING"
    And the role of the created account is "MEMBER"
    And the message "Your registration request has been submitted and is awaiting approval." is displayed
    And signing in as "pera.peric" with "Pera#2026ab" fails with HTTP status 403

  @positive
  Scenario: A visitor who uploads no image receives the system default image
    When the Guest submits a valid Member registration for "pera.peric" without attaching an image
    Then the registration succeeds with HTTP status 201
    And the profile image of "pera.peric" is the system default image

  @negative @validation @api
  Scenario: The username must be unique across all users
    When the Guest submits a valid Member registration using the username "ana.jovic"
    Then the registration fails with HTTP status 409
    And the message "That username is already taken." is displayed
    And no registration request is created

  @negative @validation @api
  Scenario: The email address must be unique across all users
    When the Guest submits a valid Member registration using the email "ana.jovic@primer.rs"
    Then the registration fails with HTTP status 409
    And the message "An account with that email address already exists." is displayed
    And no registration request is created

  @negative @validation
  Scenario Outline: Mandatory fields are rejected when empty
    When the Guest submits a valid Member registration but leaves "<field>" empty
    Then the registration fails with HTTP status 400
    And the field "<field>" is marked with the message "<message>"
    And no registration request is created

    Examples:
      | field     | message                    |
      | username  | Username is required.      |
      | password  | Password is required.      |
      | firstName | First name is required.    |
      | lastName  | Last name is required.     |
      | phone     | Contact phone is required. |
      | email     | Email address is required. |

  @negative @validation
  Scenario Outline: The password must satisfy the password policy
    When the Guest submits a valid Member registration with the password "<password>"
    Then the registration fails with HTTP status 400
    And the field "password" is marked with the message "<message>"

    Examples: too short, too long, missing character class, wrong first character
      | password        | message                                             |
      | Ab#1cde         | Password must be between 8 and 12 characters.       |
      | Abcdefg#1234x   | Password must be between 8 and 12 characters.       |
      | abcdefg#1       | Password must contain at least one uppercase letter.|
      | Abcdefgh#       | Password must contain at least one digit.           |
      | Abcdefgh1       | Password must contain at least one special character.|
      | 1Abcde#f        | Password must begin with a letter.                  |
      | #Abcde1f        | Password must begin with a letter.                  |
      |                 | Password is required.                               |

  @positive @validation
  Scenario Outline: Passwords at the boundaries of the policy are accepted
    When the Guest submits a valid Member registration with the password "<password>"
    Then the registration succeeds with HTTP status 201

    Examples: exactly 8 and exactly 12 characters
      | password      |
      | Abcdef#1      |
      | Abcdefgh#123  |

  @negative @validation
  Scenario Outline: The email address must be well formed
    When the Guest submits a valid Member registration with the email "<email>"
    Then the registration fails with HTTP status 400
    And the field "email" is marked with the message "Enter a valid email address."

    Examples:
      | email             |
      | pera              |
      | pera@             |
      | @primer.rs        |
      | pera@primer       |
      | pera @primer.rs   |
      | pera@@primer.rs   |

  @negative @validation
  Scenario Outline: The contact phone must be a plausible phone number
    When the Guest submits a valid Member registration with the phone "<phone>"
    Then the registration fails with HTTP status 400
    And the field "phone" is marked with the message "Enter a valid contact phone number."

    Examples:
      | phone           |
      | abcdefg         |
      | 12              |
      | +381-64-abc     |
      | 06412345678901234 |

  @security @api
  Scenario: Client-side validation is not the only line of defence
    When a request is sent directly to "POST /api/auth/register" bypassing the browser form, with the password "weak"
    Then the registration fails with HTTP status 400
    And the response body reports a violation of the password policy
    And no registration request is created

  @security @api
  Scenario: A visitor cannot self-assign a privileged role
    When a request is sent directly to "POST /api/auth/register" with the field "role" set to "ADMIN"
    Then no account with role "ADMIN" is created
    And any account that is created has role "MEMBER"

  @security @api
  Scenario: A visitor cannot self-approve a registration
    When a request is sent directly to "POST /api/auth/register" with the field "status" set to "APPROVED"
    Then the created registration request has status "PENDING"
    And signing in with the new account fails with HTTP status 403
