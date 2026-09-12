"""
prompts_spec.py — the ZERO-SHOT prompt that writes the specification.

This is stage zero of the thesis: the model is given a plain-language brief of
an application and must produce the Gherkin specification for it — user stories
as features, and scenarios covering both the paths that succeed and the paths
that must be refused. Everything downstream then compiles code from whatever it
wrote.

## What "zero-shot" means here, precisely

Zero-shot means the prompt contains **no worked example of the task**. There is
no sample feature file, no sample scenario, not one line of Gherkin showing the
model what a good answer looks like. It is told the notation by name — Feature,
Scenario, Scenario Outline, Given/When/Then, Examples — and told the rules its
answer must satisfy, and that is all. Whether it has internalised the notation
from pre-training is exactly the thing being measured.

Two things in this prompt are worth being honest about in the write-up, because
a reader will ask:

  * **The output contract shows a skeleton** — a `FILE:` line and a fenced
    block. That is packaging, not task content: it tells the model how to
    deliver an answer, not what a scenario looks like. No Gherkin appears in it.
  * **The rules are detailed.** Tag vocabulary, one feature per area, every
    scenario mapped to a capability. These are instructions, which zero-shot
    permits, but they do constrain the output and they make the task easier than
    a bare "write Gherkin for this" would be. Say so. What is being measured is
    "can the model produce a usable specification from instructions alone",
    which is the realistic question, not "does the model know what Gherkin is".

The natural comparison condition — and the obvious extension of this module — is
a few-shot variant carrying two or three hand-written exemplar scenarios, run
against the same models and the same brief. The difference between the two is a
result in itself, and a more interesting one than either number alone.

## What the model is NOT told

It is not told how many features or scenarios to write, which entities exist, or
what the screens are. Those are the decisions under test. It is told the brief
and the contract, and it must derive the rest.
"""

from __future__ import annotations

import config


# ============================================================ shared =======
def _notation() -> str:
    """
    The notation, described rather than demonstrated.

    Every sentence here is a rule. There is deliberately not a single line of
    Gherkin: the moment one appears, this stops being zero-shot and the
    comparison against a few-shot condition loses its meaning.
    """
    return """\
## The notation

Write Gherkin, the notation used by Cucumber and SpecFlow. Use only these
constructs, spelled exactly as named:

- `Feature:` followed by the name of one coherent area of behaviour. One per
  file, as the first line after the file's tags.
- `Background:` for steps that every scenario in that file needs before it
  starts. Optional, and only worth using when it genuinely applies to all of
  them.
- `Scenario:` followed by a name, for a single concrete case.
- `Scenario Outline:` followed by a name, for one case shape exercised with
  several sets of data, together with an `Examples:` table supplying the data.
- Steps, each beginning with `Given`, `When`, `Then`, `And` or `But`.
  `Given` establishes the starting state. `When` performs the single action
  under test. `Then` asserts the observable outcome. `And` and `But` continue
  whichever of the three came before them, so neither may be the first step.
- Tags, written on the line above a `Feature:` or a `Scenario:`, each beginning
  with `@`.
- `Examples:` tables and step data tables are pipe-delimited, one row per line,
  with a header row first and every row holding the same number of cells.

## How to write the steps themselves

- A step describes **observable behaviour from the user's point of view**. It
  says what the person does and what they see. It does not mention HTTP status
  codes, database collections, tables, endpoints, CSS selectors, button
  coordinates or field identifiers.
- **Reuse step wording.** If two scenarios need a signed-in member, both say it
  with the same words. Every distinct phrasing becomes a separate step
  definition for whoever automates this, so a specification that says the same
  thing five different ways costs five times as much to automate. This is the
  most common flaw in machine-written Gherkin; avoid it deliberately.
- Put concrete values in double quotes so they are visibly arguments rather
  than part of the sentence.
- One `When` per scenario. If a scenario needs two actions to be interesting,
  it is two scenarios, or the first action belongs in `Given`.
- A `Then` asserts one thing. Use `And` for each additional assertion.
"""


def _tagging(capabilities: dict[str, str]) -> str:
    listing = "\n".join(f"- `@{key}` — {text}" for key, text in sorted(capabilities.items()))
    return f"""\
## Required tags

Every `Scenario:` and `Scenario Outline:` carries tags on the line above it:

1. **Exactly one of `@positive` or `@negative`.** `@positive` is a path that
   succeeds. `@negative` is a path the system must refuse — bad input, a missing
   permission, a duplicate, a violated limit, an expired or absent credential, a
   state that forbids the action. Tag by what the system does, not by whether
   the user is happy: a refusal that is working correctly is `@negative`.
2. **At least one `@C<n>` capability tag**, naming the capability from the brief
   that the scenario exercises. The capabilities are:

{listing}

3. **`@ui` as well**, on any scenario whose assertions are about what is on
   screen — what is visible, enabled, disabled, ordered, or which message is
   shown. A scenario may be both `@negative` and `@ui`.

Tags are the only thing that makes this specification measurable, so they are
not optional decoration. A scenario without a polarity tag or without a
capability tag will be rejected.
"""


def _coverage() -> str:
    return """\
## What the specification must cover

- **Every capability in the brief has at least one scenario.** A capability with
  no scenario is a requirement the generated application will not have.
- **Every capability that can fail has at least one `@negative` scenario.**
  Across the whole specification, well under half the scenarios being negative
  means the failure paths have not been thought about. Most real requirements
  are about what the system refuses.
- **Boundaries are stated as concrete cases.** Wherever the brief names a number
  — a limit, a length, a count, a duration — write scenarios at the boundary
  itself and on each side of it, with the exact values. A `Scenario Outline`
  with an `Examples:` table is the right shape for this. Do not write a scenario
  that says a value is "invalid" without saying which value.
- **Permissions are stated per role.** For anything a role may do, there is a
  scenario showing another role being refused it.
- Do not invent capabilities the brief does not mention. If the brief is silent
  on something you need, choose the simplest behaviour consistent with what it
  does say, and do not add a whole feature around it.
"""


def _file_layout(areas_hint: int) -> str:
    return f"""\
## Files

Organise the specification into **subdirectories, one per functional area**, and
one `.feature` file per area within it. The directory name is the area name, in
lowercase with hyphens. The pipeline generates one screen group per area, so the
areas you choose become the structure of the application.

- A path looks like `<area>/<name>.feature` — a directory, then the file.
- Around {areas_hint} areas is the right scale for a brief of this size. Group by
  what the user is trying to do, not by which entity is stored.
- Give each file a `Feature:` whose name is a capability of the system, not a
  noun. The reader should be able to tell what the area is for from that line
  alone.
"""


def _output_contract() -> str:
    """
    Packaging only. Deliberately contains no Gherkin — see the module docstring.
    """
    return """\
## Output contract

Return **only** files, each in exactly this form:

FILE: relative/path/to/file.feature

```gherkin
COMPLETE FILE CONTENT
```

Rules:

- Every path ends in `.feature` and contains exactly one directory level.
- Do not prefix a path with `features/`, `./`, or an absolute path.
- The fenced block holds the entire file, ready to be read by a Gherkin parser.
- **Exactly one fenced block per `FILE:` line.** The block closes with a single
  ``` and the next thing in your answer is either the next `FILE:` line or the
  end of the answer. Do not add commentary, a summary, or an explanation after a
  file.
- No prose before the first `FILE:` line and none after the last closing fence.
"""


def _self_check() -> str:
    return """\
## Before you answer, check each of these

1. Does every capability in the brief have at least one scenario?
2. Does every capability that can fail have at least one `@negative` scenario?
3. Does every scenario have exactly one of `@positive` / `@negative`, and at
   least one `@C<n>` tag?
4. Does every scenario have a `Given`, exactly one `When`, and a `Then` — with
   `Given` possibly coming from the `Background:`?
5. Does every `Scenario Outline:` have an `Examples:` table whose header names
   exactly the placeholders its steps use, no more and no less, and at least two
   data rows?
6. Have I used the same wording for the same precondition everywhere, rather
   than rephrasing it each time?
7. Does every scenario that names a limit state the exact value at the boundary?
8. Is every path a `<area>/<name>.feature`?
"""


def _assemble(*sections: str) -> str:
    return "\n\n".join(s.strip() for s in sections if s and s.strip()) + "\n"


# =================================================== 1. generate the spec ===
def specification(brief: str, capabilities: dict[str, str],
                  areas_hint: int | None = None) -> str:
    """The zero-shot prompt. `brief` is the plain-language description."""
    hint = areas_hint or max(3, min(8, round(len(capabilities) / 2.5)))
    return _assemble(
        "# Task: write the Gherkin specification for the application described below",
        "You are a business analyst who writes specifications that developers "
        "implement from and testers automate directly. You answer with "
        "specification files and nothing else.",
        f"""\
## The brief

This is the whole of what you have been told about the application. Everything
in the specification must follow from it.

================ BEGIN BRIEF ================
{brief}
================= END BRIEF =================
""",
        _notation(),
        _tagging(capabilities),
        _coverage(),
        _file_layout(hint),
        _output_contract(),
        _self_check(),
    )


# ================================================= 2. repair what it wrote ==
def repair(brief: str, capabilities: dict[str, str],
           issues: str, current: str) -> str:
    """
    Feed the linter's findings back.

    Note for the write-up: a repaired specification is a different condition
    from a first-attempt one, and the two should be reported separately.
    "Produced a valid specification unaided" and "produced one after three
    rounds of being told what was wrong" are different claims about a model, and
    collapsing them into a single pass/fail hides the result.

    This is still zero-shot in the sense that matters: the model is shown its
    own output and a list of faults, never an exemplar of the task.
    """
    return _assemble(
        "# Task: fix the faults in this specification",
        "You are a business analyst. You answer with specification files and "
        "nothing else.",
        f"""\
## What is wrong

A validator checked the specification you wrote against the rules it was given.
Each line below is `file:line: [rule] what is wrong`.

```
{issues}
```
""",
        f"""\
## The specification as it stands

================ BEGIN CURRENT SPECIFICATION ================
{current}
================= END CURRENT SPECIFICATION =================
""",
        """\
## How to fix them

- Fix the **cause**. A scenario missing a `Then` needs the assertion it was
  always supposed to have, not a `Then` that restates the `When`.
- A scenario tagged with no capability is usually a scenario that does not
  belong to one. Decide which capability it serves and tag it, or remove it.
- An uncovered capability needs a new scenario, positive and negative.
- Do not delete a scenario to silence a complaint about it, and do not weaken an
  assertion to make a scenario simpler.
- Return every file you changed, complete. Files you did not change must not
  appear in your answer.
""",
        f"""\
## The brief, unchanged

================ BEGIN BRIEF ================
{brief}
================= END BRIEF =================
""",
        _notation(),
        _tagging(capabilities),
        _output_contract(),
        _self_check(),
    )
