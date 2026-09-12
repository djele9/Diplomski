# Coworking space reservation system — brief

This file is the **only hand-written input to the pipeline**. The model writes
the Gherkin specification from it (zero-shot), and the application is then
generated from that specification.

Two rules for editing it:

1. **Capabilities are numbered `C<n>:`.** Every scenario the model writes must
   be tagged with the capability it exercises, which is what makes coverage
   measurable: "this model covered 14 of 18 capabilities" is a number, not an
   impression. Do not renumber them between runs you intend to compare —
   the identifiers are how two runs are lined up against each other.
2. **Describe behaviour, not implementation.** No endpoints, no collections, no
   screen layouts. If the brief names an HTTP status code, the model will write
   scenarios about HTTP status codes, and the specification stops being
   something a non-programmer can check.

---

## The system

A web application for finding and booking desks and rooms in coworking spaces.
Coworking spaces are listed by the people who run them; members search the
listings and reserve a space for a period of time; the people running a space
manage their listings and see who has booked them.

## The people who use it

- **Visitor** — not signed in. Can browse and search public listings, and can
  apply to become a member or a manager.
- **Member** — a person who books spaces. Has an approved account.
- **Manager** — a person who lists and runs one or more coworking spaces. Has an
  approved account.
- **Administrator** — runs the platform. Approves or rejects account
  applications. There is exactly one kind of administrator account, it is
  created when the system first starts, and there is no public route for anyone
  to apply to become one.

## How accounts work

Applying for a member or manager account creates a **request**, not an account.
A request is `pending` until an administrator approves or rejects it. Until it
is approved the person cannot sign in. A rejected request tells the applicant
that it was rejected, and does not say which administrator did it.

## Capabilities

C1: a visitor can apply for a member account, giving a username, a password, a
first and last name, a contact telephone number, an email address, and
optionally a profile picture; the username and the email address must each be
unused, and if no picture is given a default one is used.

C2: a visitor can apply for a manager account, giving the same details plus the
registered name of the business they run.

C3: an administrator can see the pending account requests, oldest first, and
approve or reject each one, with a rejection carrying a reason of at least ten
characters; an approved applicant can sign in from that moment and a rejected
one cannot.

C4: a member or manager can sign in with their username and password, and is
refused if the password is wrong, the username is unknown, or their request has
not yet been approved.

C5: an administrator signs in through a separate route that is never linked to
or mentioned anywhere in the public interface.

C6: a password must be at least ten characters and contain an upper-case
letter, a lower-case letter, a digit and a punctuation character; a password
that fails any of these is refused at the moment it is chosen, and the applicant
is told every rule it broke rather than only the first.

C7: a person who has forgotten their password can request a reset by email; the
link they receive works once and expires two hours after it is issued, and
requesting a reset for an address nobody uses says the same thing as requesting
one for an address that exists.

C8: a manager can create a coworking space listing with a name, a description, a
street address, a city, a capacity in people, an hourly price, a set of
amenities, and up to eight photographs; the name must be unused among that
manager's own listings but may be shared with another manager's.

C9: a manager can edit and withdraw their own listings, and cannot see, edit or
withdraw a listing belonging to another manager; withdrawing a listing that has
reservations still to come is refused.

C10: a manager can import several listings at once from an uploaded JSON file,
where the whole file is rejected if any entry in it is invalid, and the manager
is told which entry and which field.

C11: anyone, signed in or not, can search public listings by city, by date and
time of availability, by capacity and by price, combining any of these, and the
results can be ordered by price or by average rating.

C12: anyone can open a listing and see its details, its photographs, its
amenities, its average rating and its comments, but only a signed-in member sees
the controls for making a reservation.

C13: a member can reserve an available space for a period on a given day, where
the period is between one and twelve hours, begins on the hour, and lies inside
the space's opening hours.

C14: a reservation is refused if it overlaps a reservation that already exists
for that space; two reservations that merely touch, one ending exactly when the
next begins, do not overlap.

C15: a member may hold at most three reservations that have not yet started, and
a fourth is refused.

C16: a member can cancel their own reservation up to twelve hours before it
starts, and cancelling exactly twelve hours before is still allowed; later than
that it is refused, and a member cannot cancel anyone else's reservation.

C17: a member who has actually used a space — a reservation of theirs for it has
ended — can rate it from one to five and leave a comment of at most five hundred
characters, once per reservation; a member who has not used it cannot.

C18: a manager can see the reservations made for each of their own spaces, for a
chosen day, in order of start time, and can see how much each is worth.

## Things that hold everywhere

- Nobody can read or change anything belonging to another person by asking for
  it directly, whatever the interface shows them.
- Money is in euros, with two decimal places.
- Times are local to the city the space is in.
- A list that has nothing in it says why it is empty.
