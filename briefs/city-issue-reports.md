# City issue reporting — brief

A second domain, kept deliberately unlike the first. Its purpose in this project
is to demonstrate that the pipeline is not built around one application: it has
**no accounts and nothing to sign in to**, so a run against it should produce no
authentication middleware, no route guards and no token interceptor, and should
still produce a complete application.

If a run against this brief generates a login screen, the profile detection in
`profile.py` has gone wrong — check what `pipeline.py` printed under DOMAIN
PROFILE.

## The system

A public web application where anyone can report a problem in a city — a broken
street light, a pothole, fly-tipping, a blocked drain — and where anyone can
browse and follow what has been reported. It is deliberately open: reporting
requires no account, and every report is public from the moment it is made.

## The people who use it

Anyone. There are no accounts, no sign-in, no roles and no permissions. A
reporter is identified only by the reference number they are given and by the
email address they chose to leave, if any.

Council staff do change the status of a report, but they do so through a
separate internal system that is outside the scope of this application. This
application never changes a status itself.

## What a report is

A report describes one problem at one place. It has a category, a description, a
location, a status, and a reference number that the reporter is given so they can
find it again. Its status moves through `reported`, `acknowledged`, `in progress`
and `resolved`, and never moves backwards.

## Capabilities

C1: anyone can submit a report giving a category chosen from the published list,
a description of between twenty and two thousand characters, and a location as a
street address or a pair of coordinates; the report is created with the status
"reported" and the reporter is given a reference number.

C2: a report may carry up to four photographs, each a JPEG or PNG of at most five
megabytes, and a report with no photograph is accepted just as readily.

C3: a submission is refused, with every broken rule named at once rather than
only the first, if the category is not on the list, the description is outside
its length limits, or the location is missing.

C4: a reporter may leave an email address, in which case they are sent the
reference number, and if they leave none the submission still succeeds.

C5: anyone can look up a single report by its reference number and see its
category, description, location, photographs, status and the date each status
change happened.

C6: a reference number that belongs to no report is reported as not found, in the
same way and with the same wording whether the number is malformed or merely
unused.

C7: anyone can browse all reports, twenty to a page, newest first, with the total
number of matches shown.

C8: anyone can filter the list by category, by status, and by a date range on the
date the report was made, combining any of these.

C9: anyone can search the list by free text against the description, where a
search matching nothing returns an empty list that says so rather than an error.

C10: the list can be ordered by date reported or by date last updated, in either
direction, and an attempt to order by any other field is refused.

C11: anyone can see how many reports there are in each status and in each
category, for the whole city or for a single category.

C12: anyone can add a comment of at most five hundred characters to an existing
report, and comments are shown oldest first beneath the report.

C13: a comment on a report that has been resolved for more than thirty days is
refused, because the matter is closed.

C14: anyone can confirm that they are affected by an existing report rather than
filing a duplicate, and the number of confirmations is shown on the report.

C15: the same person may confirm a given report only once, judged by the
confirmation already recorded for that browser.

C16: anyone can see the published list of categories, each with its name and a
short description of what belongs in it.

## Things that hold everywhere

- Nothing in this application requires an account, and no part of it may be made
  to require one.
- A report, once made, is never deleted or edited through this application.
- Dates are shown in the city's local time.
- A list that has nothing in it says why it is empty.
- Photographs are served at a size suitable for a web page, not at the size they
  were uploaded.
