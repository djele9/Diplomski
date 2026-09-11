@registration @upload @vibe-part-1 @zero-shot
Feature: Profile image upload
  As a registering or existing user
  I want to upload my profile picture as a file
  So that my account shows my own image rather than the system default

  Images enter the system exclusively through a file-upload control. Supplying a
  link to an image hosted elsewhere is never an acceptable substitute. Accepted
  formats are JPG and PNG; accepted pixel dimensions are 100x100 through 300x300
  inclusive, in both directions.

  Background:
    Given a Guest is on the route "/register"

  @positive @validation
  Scenario Outline: Images inside the permitted envelope are accepted
    When the Guest attaches the profile image "<file>" of type "<mimeType>" measuring <width>x<height> pixels
    Then the upload is accepted
    And the attached image is shown as a preview beside the form

    Examples: the four corners of the permitted range and a typical case
      | file              | mimeType   | width | height |
      | min.png           | image/png  | 100   | 100    |
      | max.png           | image/png  | 300   | 300    |
      | wide.jpg          | image/jpeg | 300   | 100    |
      | tall.jpg          | image/jpeg | 100   | 300    |
      | avatar-200.jpg    | image/jpeg | 200   | 200    |

  @negative @validation
  Scenario Outline: Images outside the permitted pixel range are rejected
    When the Guest attaches the profile image "<file>" of type "image/png" measuring <width>x<height> pixels
    Then the upload fails with HTTP status 400
    And the message "The image must be between 100x100 and 300x300 pixels." is displayed
    And no file is stored on the server

    Examples: just under, just over, and far outside
      | file        | width | height |
      | tiny.png    | 99    | 100    |
      | tiny2.png   | 100   | 99     |
      | big.png     | 301   | 300    |
      | big2.png    | 300   | 301    |
      | huge.png    | 1920  | 1080   |
      | sliver.png  | 50    | 400    |

  @negative @validation
  Scenario Outline: Only JPG and PNG files are accepted
    When the Guest attaches the profile image "<file>" of type "<mimeType>" measuring 200x200 pixels
    Then the upload fails with HTTP status 415
    And the message "Only JPG and PNG images are accepted." is displayed
    And no file is stored on the server

    Examples:
      | file           | mimeType                 |
      | animation.gif  | image/gif                |
      | vector.svg     | image/svg+xml            |
      | photo.bmp      | image/bmp                |
      | scan.pdf       | application/pdf          |
      | modern.webp    | image/webp               |
      | archive.zip    | application/zip          |

  @negative @security
  Scenario: A file whose extension lies about its content is rejected
    When the Guest attaches a file named "payload.png" whose actual content is a PHP script
    Then the upload fails with HTTP status 415
    And the message "Only JPG and PNG images are accepted." is displayed
    And the decision is based on the file's inspected content, not on its file name

  @negative @security
  Scenario: An image supplied as an external link is not accepted
    When a request is sent directly to "POST /api/users/profile-image" with the body field "imageUrl" set to "https://example.com/avatar.png"
    Then the request fails with HTTP status 400
    And the message "The profile image must be uploaded as a file." is displayed
    And the server makes no outbound request to "example.com"

  @negative @security
  Scenario: The upload endpoint refuses oversized payloads
    When the Guest attaches a PNG file of 25 megabytes measuring 200x200 pixels
    Then the upload fails with HTTP status 413
    And the message "The uploaded file is too large." is displayed

  @negative @security
  Scenario Outline: The stored file name cannot be used to escape the upload directory
    When the Guest attaches a valid 200x200 PNG named "<fileName>"
    Then the stored file is written inside the configured upload directory only
    And the stored file name contains no path separator and no parent-directory segment

    Examples:
      | fileName                   |
      | ../../etc/passwd.png       |
      | ..\\..\\windows\\a.png     |
      | normal name (1).png        |
      | ćirilica-слика.png         |

  @positive
  Scenario: Omitting the image assigns the system default
    When the Guest submits a valid Member registration without attaching any image
    Then the registration succeeds with HTTP status 201
    And the profile image of the created account is the system default image
    And the default image is served from the application's own static assets

  @positive @ui
  Scenario: An existing user replaces their profile image from the profile page
    Given the Member "ana.jovic" is signed in
    And the profile image of "ana.jovic" is "old-avatar.png"
    When the Member opens the profile page
    And the Member attaches the profile image "new-avatar.png" of type "image/png" measuring 250x250 pixels
    And the Member saves the profile
    Then the profile image of "ana.jovic" is "new-avatar.png"
    And the previously stored file "old-avatar.png" is no longer referenced by any account

  @negative @security
  Scenario: A Member cannot replace another user's profile image
    Given the Member "ana.jovic" is signed in
    When a request is sent to "POST /api/users/marko.spc/profile-image" with a valid image
    Then the request fails with HTTP status 403
    And the profile image of "marko.spc" is unchanged
