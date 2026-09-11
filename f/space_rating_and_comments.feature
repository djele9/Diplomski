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