# <Application name> — brief

A brief is the only hand-written input to the pipeline. The model writes the
Gherkin specification from it; the application is generated from that.

Copy this file to `briefs/<project>.md` and run:

    python3 pipeline.py --project <project> --generate-spec

## Rules for writing one

1. **Capabilities are numbered `C<n>:`.** One capability per line, each a single
   sentence in the form "someone can do something, subject to these conditions".
   Every scenario the model writes must carry the tag of the capability it
   exercises, which is what makes coverage measurable — "this model covered 14
   of 18 capabilities" is a number rather than an impression.

2. **Do not renumber between runs you intend to compare.** The identifiers are
   how two runs are lined up against each other. Add `C19`, never reuse `C7`.

3. **Describe behaviour, not implementation.** No endpoints, no collections, no
   screen layouts, no status codes. If the brief says "returns 409" the model
   will write scenarios about status codes, and the specification stops being
   something a non-programmer can check.

4. **State the numbers.** Every limit, length, count and duration, with its
   exact value and whether the boundary itself is included. "Up to twelve hours
   before, and exactly twelve hours is still allowed" produces a correct
   comparison; "shortly before" produces a guess.

5. **Say what must be refused.** Roughly half of what an application does is
   refuse things. A brief that only describes success produces a specification
   that only describes success, and then an application that only handles it.

6. **Only describe what you want built.** The pipeline infers what the
   application needs — accounts, roles, uploads, search, scheduling, money,
   email, bulk import, ratings, state machines — from the specification the
   model writes. Mentioning a concern in passing that you do not want is how an
   application acquires a login screen nobody needs.

---

## The system

<Two or three sentences. What is it for, and who is it for?>

## The people who use it

- **<Role>** — <what they can do, in one line>
- **<Role>** — <...>

<If the application has no accounts at all, say so explicitly here: "Anyone can
use the application; there are no accounts and nothing to sign in to." The
pipeline reads this and will not generate authentication.>

## <Any concept that needs explaining before the capabilities make sense>

<For example: what a "request" is and what states it moves through. Keep it to
what a reader needs in order to follow the list below.>

## Capabilities

C1: <a person> can <do a thing>, given <conditions>, and <what results>.

C2: ...

C3: ...

<Aim for 10-20. Fewer than about 8 and the generated application is too small to
say anything interesting about a model; more than about 25 and the specification
stage runs past what a small model can hold in one answer.>

## Things that hold everywhere

- <Cross-cutting rules: money format, time zones, what an empty list says, what
  nobody may ever do.>
