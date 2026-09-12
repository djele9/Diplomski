# Library lending — brief

A third domain, of a shape between the other two: it has accounts and roles like
the coworking system, but no uploads, no ratings and no bulk import. Useful for
checking that the profile narrows as well as widens — a run against this brief
should generate authentication and authorization, and should **not** generate
upload middleware.

## The system

A lending system for a public library. Members borrow physical copies of titles;
librarians manage the catalogue and the loans. Everything a member may do with a
book, and everything the library refuses, is described below.

## The people who use it

- **Visitor** — not signed in. Can search the catalogue and see what is available.
- **Member** — has a library account. Borrows, reserves, renews and returns.
- **Librarian** — manages the catalogue, the copies, and the loans of others.

## Titles, copies and loans

A **title** is a work — an author, a title, a year, an ISBN. A **copy** is one
physical book on a shelf, belonging to a title; a title may have many copies. A
**loan** is one copy in the hands of one member between two dates. A member
borrows a copy, not a title.

## Capabilities

C1: a librarian can add a title with an author, a name, a year of publication and
a thirteen-digit ISBN, where the ISBN must be unused in the catalogue.

C2: a librarian can add copies to a title, each with a shelf mark unique within
the library, and can withdraw a copy that is not currently on loan.

C3: a librarian can edit a title, and an attempt to change its ISBN to one
another title already uses is refused.

C4: a visitor or member can search the catalogue by author, by title and by year,
combining any of these, with results twenty to a page and orderable by author or
by year.

C5: anyone can open a title and see its details together with how many of its
copies are on the shelf and how many are on loan.

C6: a member signs in with a library card number and a password, and is refused
if the password is wrong, the card number is unknown, or the account is
suspended.

C7: a librarian signs in through the same form as a member, and what they may do
follows from their role and not from anything the browser sends.

C8: a member can borrow an available copy for twenty-one days, and the loan is
refused if no copy of that title is on the shelf.

C9: a member may hold at most eight loans at once, and a ninth is refused.

C10: a member with any loan more than thirty days overdue may not borrow anything
further until it is returned.

C11: a member can renew a loan once, for a further twenty-one days, provided
nobody has reserved the title; a second renewal is refused.

C12: a member can reserve a title all of whose copies are on loan, joining a
queue, and is refused if they already have a copy of that title on loan.

C13: when a copy is returned, the first member in the queue for its title is
notified by email and the copy is held for them for three days.

C14: a librarian records the return of a copy, which ends the loan and makes the
copy available unless it is being held for a reservation.

C15: a loan returned after its due date incurs a fine of twenty cents for each
day late, counted from the day after the due date, capped at twelve euros per
loan.

C16: a member can see their own current loans, their due dates, their
reservations and the total they owe, and cannot see any of this for another
member.

C17: a librarian can see the loans of any member, and can see every loan that is
overdue, ordered by how overdue it is.

C18: a member whose fines exceed twenty euros is suspended from borrowing until
the balance is cleared, and a librarian can record that a member has paid.

## Things that hold everywhere

- Nobody can read or change anything belonging to another member by asking for it
  directly, whatever the interface shows them.
- Money is in euros, with two decimal places.
- Dates are whole days in the library's local time; a loan due "on" a day is not
  overdue until the day after.
- A list that has nothing in it says why it is empty.
- There are no photographs, cover images or file uploads anywhere in this system.
