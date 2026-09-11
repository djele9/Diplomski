@registration @vibe-part-1 @zero-shot
Feature: Space Manager registration and company constraints
  As a visitor who operates coworking premises
  I want to register as a Space Manager on behalf of my company
  So that after approval I can publish and manage that company's Spaces

  A Space Manager submits everything a Member submits plus four company fields.
  Company identity is enforced by two national identifiers with strict formats,
  and a company may never have more than two Space Managers at the same time.

  Background:
    Given the following company exists:
      | name          | headquartersAddress   | companyNumber | taxId     |
      | SPC Radionica | Bulevar Kralja 12, BG | 12345678      | 101234567 |
    And the following approved Space Managers represent "SPC Radionica":
      | username  |
      | marko.spc |
    And a Guest is on the route "/register"
    And the Guest has selected the account type "Space Manager"

  @positive @api
  Scenario: A visitor registers as the manager of a brand-new company
    When the Guest submits the registration form with:
      | field               | value                  |
      | username            | jelena.hub             |
      | password            | Jelena#26x             |
      | firstName           | Jelena                 |
      | lastName            | Ilic                   |
      | phone               | +381631112223          |
      | email               | jelena@nova-firma.rs   |
      | companyName         | Nova Firma             |
      | headquartersAddress | Nemanjina 4, Beograd   |
      | companyNumber       | 87654321               |
      | taxId               | 987654321              |
    And the Guest attaches the profile image "avatar-150x150.jpg"
    Then the registration succeeds with HTTP status 201
    And a registration request for "jelena.hub" is created with status "PENDING"
    And the role of the created account is "MANAGER"
    And a company "Nova Firma" with companyNumber "87654321" and taxId "987654321" exists

  @positive @api
  Scenario: A second manager may join an existing company
    When the Guest submits a valid Space Manager registration for "nikola.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration succeeds with HTTP status 201
    And "nikola.spc" is associated with the existing company "SPC Radionica"
    And no duplicate company record is created

  @negative @api
  Scenario: A third manager for the same company is refused
    Given the approved Space Manager "nikola.spc" also represents "SPC Radionica"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration fails with HTTP status 409
    And the message "This company already has the maximum of two space managers." is displayed
    And no registration request is created

  @negative @api
  Scenario: A pending manager still counts towards the company limit
    Given a registration request for "nikola.spc" representing "SPC Radionica" exists with status "PENDING"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration fails with HTTP status 409
    And the message "This company already has the maximum of two space managers." is displayed

  @positive @api
  Scenario: A rejected manager does not count towards the company limit
    Given a registration request for "nikola.spc" representing "SPC Radionica" exists with status "REJECTED"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration succeeds with HTTP status 201

  @positive @api
  Scenario: Removing a manager frees a slot
    Given the approved Space Manager "nikola.spc" also represents "SPC Radionica"
    And the Administrator deletes the account "nikola.spc"
    When the Guest submits a valid Space Manager registration for "treci.spc" with the companyNumber "12345678" and the taxId "101234567"
    Then the registration succeeds with HTTP status 201

  @negative @validation
  Scenario Outline: The company number must be exactly eight digits
    When the Guest submits a valid Space Manager registration with the companyNumber "<companyNumber>"
    Then the registration fails with HTTP status 400
    And the field "companyNumber" is marked with the message "Company number must be exactly 8 digits."

    Examples: too short, too long, non-numeric, spaced
      | companyNumber |
      | 1234567       |
      | 123456789     |
      | 1234567a      |
      | 1234 5678     |
      |               |
      | -1234567      |

  @positive @validation
  Scenario: A company number beginning with zero is valid
    When the Guest submits a valid Space Manager registration with the companyNumber "01234567"
    Then the registration succeeds with HTTP status 201

  @negative @validation
  Scenario Outline: The tax identification number must be exactly nine digits and must not begin with zero
    When the Guest submits a valid Space Manager registration with the taxId "<taxId>"
    Then the registration fails with HTTP status 400
    And the field "taxId" is marked with the message "<message>"

    Examples:
      | taxId      | message                                       |
      | 12345678   | Tax ID must be exactly 9 digits.              |
      | 1234567890 | Tax ID must be exactly 9 digits.              |
      | 12345678a  | Tax ID must be exactly 9 digits.              |
      |            | Tax ID is required.                           |
      | 012345678  | Tax ID must not begin with zero.              |
      | 000000000  | Tax ID must not begin with zero.              |

  @positive @validation
  Scenario Outline: Tax identification numbers at the edge of the rule are accepted
    When the Guest submits a valid Space Manager registration with the taxId "<taxId>"
    Then the registration succeeds with HTTP status 201

    Examples:
      | taxId     |
      | 100000000 |
      | 999999999 |

  @negative @api
  Scenario: The company number is unique across companies
    When the Guest submits a valid Space Manager registration with the companyName "Druga Firma", the companyNumber "12345678" and the taxId "222333444"
    Then the registration fails with HTTP status 409
    And the message "A different company is already registered with that company number." is displayed

  @negative @api
  Scenario: The tax identification number is unique across companies
    When the Guest submits a valid Space Manager registration with the companyName "Druga Firma", the companyNumber "55556666" and the taxId "101234567"
    Then the registration fails with HTTP status 409
    And the message "A different company is already registered with that tax ID." is displayed

  @negative @validation
  Scenario Outline: The remaining company fields are mandatory
    When the Guest submits a valid Space Manager registration but leaves "<field>" empty
    Then the registration fails with HTTP status 400
    And the field "<field>" is marked with the message "<message>"

    Examples:
      | field               | message                          |
      | companyName         | Company name is required.        |
      | headquartersAddress | Headquarters address is required.|

  @security @api
  Scenario: Company constraints are enforced on the server, not only in the browser
    When a request is sent directly to "POST /api/auth/register" with role "MANAGER", companyNumber "999" and taxId "0"
    Then the registration fails with HTTP status 400
    And the response body reports violations for both "companyNumber" and "taxId"
