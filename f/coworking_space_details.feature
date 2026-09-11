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
Then the selection is stored in the web browser cookie
