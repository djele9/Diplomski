#!/usr/bin/env python3
"""
test_pipeline.py — tests for the parts of the pipeline that fail silently.

Run with:  python3 test_pipeline.py

These are not tests of the generated application. They are tests of the
MEASURING INSTRUMENT: the response parser, the path guard, the route extractor
and the compiler-output parser. Every one of them can be wrong in a way that
produces a plausible number rather than an error, and a thesis built on a
plausible number is worse than one built on a missing number.

The committed run runs/run-20260911T143100Z is the cautionary case: `"ok": false`
with `"error_count": 0` on both sides, which measured the parser, not the model.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import config

# Point every path at a scratch directory before importing anything that reads
# them at import time.
_TMP = Path(tempfile.mkdtemp(prefix="pipeline-test-"))
config.OUTPUT_DIR = _TMP / "app"
config.BACKEND_DIR = config.OUTPUT_DIR / "backend"
config.FRONTEND_DIR = config.OUTPUT_DIR / "frontend"
config.RUNS_DIR = _TMP / "runs"
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

import compilers                                              # noqa: E402
import context                                                # noqa: E402
import domain_profile                                         # noqa: E402
import gherkin                                                # noqa: E402
import llm                                                    # noqa: E402
import prompts_backend as pb                                  # noqa: E402
import prompts_frontend as pf                                 # noqa: E402
import prompts_spec                                           # noqa: E402

PASSED = 0
FAILED: list[str] = []


def check(name: str, actual, expected) -> None:
    global PASSED
    if actual == expected:
        PASSED += 1
        print(f"  ok   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name}\n        expected: {expected!r}\n        actual:   {actual!r}")


def check_true(name: str, value) -> None:
    check(name, bool(value), True)


# ====================================================== response parsing ====
def test_parse_plain() -> None:
    print("\nparse_files — the ordinary case")
    text = """FILE: backend/src/a.ts
```ts
export const a = 1;
```

FILE: backend/src/b.ts
```ts
export const b = 2;
```
"""
    files = llm.parse_files(text)
    check("two files found", len(files), 2)
    check("first path", files[0].path, "backend/src/a.ts")
    check("first content", files[0].content, "export const a = 1;")
    check("second content", files[1].content, "export const b = 2;")
    check("both closed", [f.closed for f in files], [True, True])
    check("no chatter", [f.trailing_chatter for f in files], [False, False])


def test_parse_chatty_model() -> None:
    """The regression this rewrite exists for."""
    print("\nparse_files — a chatty model adds an example after the file")
    text = """FILE: backend/src/a.ts
```ts
export const a = 1;
```

You can run it with:

```bash
npm run dev
```
"""
    files = llm.parse_files(text)
    check("one file", len(files), 1)
    check("content stops at the first closing fence",
          files[0].content, "export const a = 1;")
    check_true("trailing chatter recorded", files[0].trailing_chatter)
    # Under the old "last fence wins" rule the content would have been
    # "export const a = 1;\n```\n\nYou can run it with:\n\n```bash\nnpm run dev"
    # — a TypeScript file containing prose and a fence, which does not compile,
    # and which would have been scored against the model's code quality.
    check_true("no shell command leaked into the source",
               "npm run dev" not in files[0].content)


def test_parse_markdown_keeps_nested_fences() -> None:
    print("\nparse_files — a markdown file may legitimately contain fences")
    text = """FILE: backend/README.md
```md
# Setup

```bash
npm install
```

Done.
```
"""
    files = llm.parse_files(text)
    check("one file", len(files), 1)
    check_true("nested fence preserved", "npm install" in files[0].content)
    check_true("closing prose preserved", "Done." in files[0].content)


def test_parse_truncated() -> None:
    print("\nparse_files — a truncated response")
    text = """FILE: backend/src/a.ts
```ts
export const a = 1;
```

FILE: backend/src/b.ts
```ts
export const b = 2;
export function unfinished(
"""
    files = llm.parse_files(text)
    check("two markers seen", len(files), 2)
    check("first is closed", files[0].closed, True)
    check("second is unclosed", files[1].closed, False)


def test_parse_no_markers() -> None:
    print("\nparse_files — the model ignored the contract")
    check("no files", llm.parse_files("Sure! Here is your code:\n\nconst a = 1;"), [])


# =========================================================== path guard ====
def test_path_guard() -> None:
    print("\nsafe_destination — rejections")
    for bad in ("/etc/passwd", "C:/Windows/system32/x.ts", "../../escape.ts",
                "backend/../../escape.ts", "backend/package-lock.json"):
        try:
            llm.safe_destination(bad, "backend/")
            FAILED.append(f"accepted {bad}")
            print(f"  FAIL accepted {bad}")
        except llm.PathRejected:
            globals()["PASSED"] = PASSED + 1
            print(f"  ok   rejected {bad}")

    print("\nsafe_destination — the root contract")
    dest, note = llm.safe_destination("backend/src/models/user.model.ts", "backend/")
    check("correct path untouched",
          dest.relative_to(config.OUTPUT_DIR).as_posix(), "backend/src/models/user.model.ts")
    check("no note for a correct path", note, "")

    dest, note = llm.safe_destination("src/models/user.model.ts", "backend/")
    check("rootless path repaired",
          dest.relative_to(config.OUTPUT_DIR).as_posix(), "backend/src/models/user.model.ts")
    check_true("repair is reported", "prepended" in note)

    dest, note = llm.safe_destination("package.json", "frontend/")
    check("root-level file repaired",
          dest.relative_to(config.OUTPUT_DIR).as_posix(), "frontend/package.json")

    dest, _ = llm.safe_destination("app/backend/src/x.ts", "backend/")
    check("output-root prefix stripped",
          dest.relative_to(config.OUTPUT_DIR).as_posix(), "backend/src/x.ts")

    try:
        llm.safe_destination("frontend/src/x.ts", "backend/")
        FAILED.append("wrong-side path accepted")
        print("  FAIL wrong-side path accepted")
    except llm.PathRejected:
        globals()["PASSED"] = PASSED + 1
        print("  ok   rejected a frontend path from a backend stage")

    # The frontend's own app/ directory must survive the app/ prefix stripping.
    dest, _ = llm.safe_destination("frontend/src/app/app.config.ts", "frontend/")
    check("frontend src/app preserved",
          dest.relative_to(config.OUTPUT_DIR).as_posix(), "frontend/src/app/app.config.ts")


# ====================================================== route extraction ====
ROUTER_CONVENTIONAL = """
import { Router } from 'express';
import { login } from '../controllers/auth.controller';
const router = Router();
router.post('/login', login);
router.get('/me', auth, me);
export default router;
"""

ROUTER_NAMED_VARIABLE = """
import express from 'express';
const authRouter = express.Router();
authRouter.post('/login', login);
authRouter.get('/me', auth, me);
export default authRouter;
"""

ROUTER_CHAINED = """
import { Router } from 'express';
const router = Router();
router.route('/spaces')
  .get(listSpaces)
  .post(auth, createSpace);
router.get('/spaces/:id', getSpace);
export default router;
"""

SERVER = """
import express from 'express';
import authRouter from './routers/auth.routes';
const app = express();
app.use('/api/auth', authRouter);
"""


def test_route_extraction() -> None:
    print("\nroute extraction")
    check("conventional router",
          context._routes_in_text(ROUTER_CONVENTIONAL),
          [("post", "/login"), ("get", "/me")])
    # The old regex required the literal name `router` and found nothing here.
    check("router named after the area",
          context._routes_in_text(ROUTER_NAMED_VARIABLE),
          [("post", "/login"), ("get", "/me")])
    # The old comment claimed this worked; the regex never matched it.
    check("chained .route()",
          context._routes_in_text(ROUTER_CHAINED),
          [("get", "/spaces"), ("post", "/spaces"), ("get", "/spaces/:id")])

    src = config.BACKEND_DIR / "src"
    (src / "routers").mkdir(parents=True, exist_ok=True)
    (src / "routers" / "auth.routes.ts").write_text(ROUTER_CONVENTIONAL, encoding="utf-8")
    (src / "server.ts").write_text(SERVER, encoding="utf-8")

    rows = context.api_surface_routes()
    check("mount prefix applied",
          [(m, p) for _, m, p in rows],
          [("POST", "/api/auth/login"), ("GET", "/api/auth/me")])
    check_true("surface is usable", context.surface_is_usable(context.extract_api_surface()))


def test_module_key() -> None:
    print("\nmodule key — the .routes suffix trap")
    check("import specifier", context._module_key("./routers/space.routes"), "space.routes")
    check("file name", context._module_key("space.routes.ts"), "space.routes")


# ==================================================== compiler output ======
TSC_PLAIN_OUTPUT = """
src/models/user.model.ts(4,17): error TS2304: Cannot find name 'compose'.
src/models/user.model.ts(9,3): error TS2551: Property 'emial' does not exist.
src/app.ts(2,1): warning TS6133: 'x' is declared but never used.
"""

TSC_PRETTY_OUTPUT = """
src/models/user.model.ts:4:17 - error TS2304: Cannot find name 'compose'.
"""

TSC_PRETTY_ANSI = (
    "\x1b[96msrc/models/user.model.ts\x1b[0m:\x1b[93m4\x1b[0m:\x1b[93m17\x1b[0m - "
    "\x1b[91merror\x1b[0m \x1b[90mTS2304: \x1b[0mCannot find name 'compose'.\n"
)

NG_ESBUILD_OUTPUT = """
✘ [ERROR] TS2339: Property 'titel' does not exist on type 'LoginComponent'. [plugin angular-compiler]

    src/app/components/login/login.html:7:20:
      7 │   {{ titel }}
"""


def test_compiler_parsing() -> None:
    print("\ncompiler output parsing")
    errors = compilers.parse_compiler_output(TSC_PLAIN_OUTPUT)
    check("tsc plain: files", sorted(errors), ["src/models/user.model.ts"])
    check("tsc plain: warnings ignored", len(errors["src/models/user.model.ts"]), 2)

    errors = compilers.parse_compiler_output(TSC_PRETTY_OUTPUT)
    check("tsc pretty", len(errors.get("src/models/user.model.ts", [])), 1)

    errors = compilers.parse_compiler_output(TSC_PRETTY_ANSI)
    check("tsc pretty with ANSI", len(errors.get("src/models/user.model.ts", [])), 1)

    errors = compilers.parse_compiler_output(NG_ESBUILD_OUTPUT)
    check("angular esbuild two-line error",
          len(errors.get("src/app/components/login/login.html", [])), 1)

    check("clean output parses to nothing", compilers.parse_compiler_output(""), {})


def test_blocked_detection() -> None:
    print("\nblocked vs failing")
    missing = compilers._result_from(["npx", "tsc"], 127, "command not found: npx")
    check_true("missing tool flagged", missing.tool_missing)
    check_true("missing tool counts as blocked", missing.blocked())
    check("missing tool is not a parse failure", missing.parse_failed, False)

    unparseable = compilers._result_from(["npx", "tsc"], 2, "something unfamiliar")
    check_true("unrecognised format flagged", unparseable.parse_failed)
    check_true("unrecognised format counts as blocked", unparseable.blocked())

    real = compilers._result_from(["npx", "tsc"], 2, TSC_PLAIN_OUTPUT)
    check("real errors counted", real.error_count, 2)
    check("real errors are not blocked", real.blocked(), False)


# ========================================================== placeholders ====
def test_placeholders() -> None:
    print("\nplaceholder scanning")
    check("help text is not a stub",
          llm.scan_placeholders("x.html", '<p>A default image is used if omitted.</p>'), [])
    check_true("a commented TODO is a stub",
               llm.scan_placeholders("x.ts", "// TODO: implement this\nconst a = 1;"))
    check_true("a strong marker anywhere is a stub",
               llm.scan_placeholders("x.ts", 'const s = "REST OF CODE";'))
    check("ngOnInit may legitimately be empty",
          llm.scan_placeholders("x.ts", "  ngOnInit(): void {}"), [])


# ============================================================ spec counts ===
SPEC = """
===== login.feature =====
Feature: Authentication

  Background:
    Given the system is running

  Scenario: Successful login
    Given a member exists
    Then they are logged in

  Scenario Outline: Bad password
    Given a member exists
    Then login fails

    Examples:
      | password |
      | short    |
      | wrong    |
"""


def test_spec_counts() -> None:
    print("\nspecification counting")
    sizes = context.count_scenarios(SPEC)
    check("features", sizes["features"], 1)
    check("scenarios", sizes["scenarios"], 1)
    check("outlines", sizes["scenario_outlines"], 1)
    check("backgrounds", sizes["backgrounds"], 1)
    check("example rows exclude the header", sizes["examples_rows"], 2)
    check("fingerprint is stable",
          context.spec_fingerprint(SPEC), context.spec_fingerprint(SPEC))


# =============================================================== context ====
def test_context_budget() -> None:
    print("\ncode context budget")
    area = config.BACKEND_DIR / "src" / "services"
    area.mkdir(parents=True, exist_ok=True)
    (area / "small.ts").write_text("export const small = 1;\n", encoding="utf-8")
    (area / "huge.ts").write_text("// " + "x" * 5000 + "\n", encoding="utf-8")

    body = context.collect_code(area, budget=2000)
    check_true("small file included", "export const small = 1;" in body)
    check_true("huge file omitted", "OMITTED FROM THIS CONTEXT" in body)
    check_true("omission names the file", "huge.ts" in body.split("OMITTED FROM THIS CONTEXT")[1])
    check_true("budget respected", len(body) < 4000)

    generous = context.collect_code(area, budget=100_000)
    check_true("nothing omitted when it fits",
               "OMITTED FROM THIS CONTEXT" not in generous)


# ========================================================= gherkin parsing ==
GOOD_FEATURE = """\
@auth
Feature: Signing in

  Background:
    Given the system is running

  @positive @C4
  Scenario: A member signs in
    Given an approved member "ana" exists
    When she signs in with the correct password
    Then she is signed in
    And the member menu is shown

  @negative @C4 @ui
  Scenario: A member signs in with the wrong password
    Given an approved member "ana" exists
    When she signs in with an incorrect password
    Then she is not signed in
    And she is told the credentials are wrong

  @negative @C6
  Scenario Outline: A password that breaks a rule is refused
    Given a visitor is choosing a password
    When she submits "<password>"
    Then the password is refused
    And she is told "<reason>"

    Examples:
      | password | reason              |
      | short    | at least ten        |
      | alllower | needs an upper case |
"""

BAD_FEATURE = """\
Feature: Reservations

  Scenario: A member reserves a space
    Given an approved member exists
    Then the reservation exists

  @positive @negative @C99
  Scenario: A member reserves a space
    Given an approved member exists
    When she reserves it
    Then it is reserved

  @positive @C13
  Scenario Outline: Reserving for various durations
    Given an approved member exists
    When she reserves for <hours> hours
    Then it is accepted

    Examples:
      | duration |
      | 1        |
"""


def test_gherkin_parse() -> None:
    print("\ngherkin — parsing a well-formed feature")
    feature = gherkin.parse_feature(GOOD_FEATURE, "auth/login.feature")
    check("feature name", feature.name, "Signing in")
    check("feature tags", feature.tags, ["auth"])
    check("background steps", len(feature.background), 1)
    check("scenarios", len(feature.scenarios), 3)
    check("kinds", [s.kind for s in feature.scenarios],
          ["Scenario", "Scenario", "Scenario Outline"])
    check("tags on the second", sorted(feature.scenarios[1].tags),
          ["C4", "negative", "ui"])
    check("and-steps resolve to their keyword",
          sorted(feature.scenarios[0].keywords()), ["Given", "Then", "When"])
    outline = feature.scenarios[2]
    check("examples header", outline.examples[0].header, ["password", "reason"])
    check("examples rows", outline.example_rows(), 2)


def test_gherkin_lint_clean() -> None:
    print("\ngherkin — a valid feature produces no issues")
    feature = gherkin.parse_feature(GOOD_FEATURE, "auth/login.feature")
    issues = gherkin.lint_feature(feature, {"C4", "C6"})
    check("no issues", [str(i) for i in issues], [])


def test_gherkin_lint_catches() -> None:
    print("\ngherkin — the faults small models actually produce")
    feature = gherkin.parse_feature(BAD_FEATURE, "booking/reserve.feature")
    rules = {i.rule for i in gherkin.lint_feature(feature, {"C13"})}
    for rule in ("step-no-when", "tag-no-polarity", "tag-both-polarities",
                 "tag-unknown-capability", "scenario-duplicate",
                 "outline-placeholder-missing", "outline-column-unused",
                 "examples-too-few-rows"):
        check_true(f"catches {rule}", rule in rules)


def test_gherkin_coverage() -> None:
    print("\ngherkin — an uncovered capability is reported once, globally")
    feature = gherkin.parse_feature(GOOD_FEATURE, "auth/login.feature")
    issues = gherkin.lint([feature], {"C4", "C6", "C17"})
    uncovered = [i for i in issues if i.rule == "capability-uncovered"]
    check("one uncovered capability", len(uncovered), 1)
    check_true("names the right one", "C17" in uncovered[0].message)


def test_gherkin_metrics() -> None:
    print("\ngherkin — metrics")
    feature = gherkin.parse_feature(GOOD_FEATURE, "auth/login.feature")
    m = gherkin.metrics([feature], {"C4", "C6", "C17"})
    check("scenarios total", m["scenarios_total"], 3)
    check("positive", m["positive"], 1)
    check("negative", m["negative"], 2)
    check("negative share", m["negative_share"], 0.67)
    check("ui tagged", m["ui_tagged"], 1)
    check("coverage", m["capability_coverage"], 0.67)
    check("missing", m["capabilities_missing"], ["C17"])
    check("example rows", m["examples_rows"], 2)
    check_true("step reuse above 1 — the Given repeats", m["step_reuse"] > 1.0)


def test_step_normalisation() -> None:
    print("\ngherkin — step reuse ignores arguments, not wording")
    same = gherkin._normalise_step('a member "ana" exists')
    other = gherkin._normalise_step('a member "marko" exists')
    check("quoted values are arguments", same, other)
    check("numbers are arguments",
          gherkin._normalise_step("she reserves for 3 hours"),
          gherkin._normalise_step("she reserves for 12 hours"))
    check_true("different wording stays different",
               gherkin._normalise_step("a member exists")
               != gherkin._normalise_step("there is a member"))


def test_brief_parsing() -> None:
    print("\nbrief — capability extraction")
    text = """
# Brief

## Capabilities

C1: a visitor can apply for a member account
C2: a member can reserve a space

## Things that hold everywhere
- nothing numbered here
"""
    _, capabilities = gherkin.parse_brief(text)
    check("two capabilities", sorted(capabilities), ["C1", "C2"])
    check_true("text captured", "reserve a space" in capabilities["C2"])

    real = (Path(__file__).parent / "brief.md")
    if real.exists():
        _, caps = gherkin.parse_brief(real.read_text(encoding="utf-8"))
        check_true("the bundled brief declares capabilities", len(caps) >= 10)


def test_spec_prompt_is_zero_shot() -> None:
    """
    The methodological guard: no worked example may leak into the prompt.

    This is a test rather than a comment because it is the one property of the
    prompt that cannot be checked by reading the output. A single exemplar
    scenario added later 'to help the model' would silently turn the whole
    condition into one-shot, and every number collected under it would be
    describing a different experiment than the write-up claims.
    """
    print("\nprompts_spec — the zero-shot property")
    capabilities = {"C1": "a visitor can register", "C2": "a member can book"}
    prompt = prompts_spec.specification("A system for booking things.", capabilities)

    check_true("the brief is present", "A system for booking things." in prompt)
    check_true("capabilities are listed", "@C2" in prompt)

    # No Gherkin step may appear anywhere in the prompt. Keywords are named in
    # prose ("steps begin with Given"), so look for the step SHAPE: a line that
    # starts with a step keyword followed by text.
    import re as _re
    offenders = [
        line for line in prompt.splitlines()
        if _re.match(r"^\s*(Given|When|Then|And|But)\s+\w", line)
    ]
    check("no example steps", offenders, [])

    scenario_lines = [
        line for line in prompt.splitlines()
        if _re.match(r"^\s*(Scenario|Scenario Outline|Feature):\s*\S", line)
    ]
    check("no example Feature/Scenario declarations", scenario_lines, [])

    table_lines = [line for line in prompt.splitlines()
                   if _re.match(r"^\s*\|.*\|\s*$", line) and "---" not in line
                   and "Use" not in line and "Not" not in line]
    check("no example Examples table", table_lines, [])


def test_spec_path_guard() -> None:
    print("\nspec stage — paths are confined to the features directory")
    base = _TMP / "features"
    base.mkdir(parents=True, exist_ok=True)

    dest, _ = llm.safe_destination("auth/login.feature", None, base, (".feature",))
    check("area path accepted",
          dest.relative_to(base).as_posix(), "auth/login.feature")

    dest, note = llm.safe_destination("features/auth/login.feature", None, base,
                                      (".feature",))
    check("features/ prefix stripped",
          dest.relative_to(base).as_posix(), "auth/login.feature")
    check_true("strip is reported", "stripped" in note)

    for bad, why in (("auth/README.md", "wrong suffix"),
                     ("../escape.feature", "traversal"),
                     ("/etc/login.feature", "absolute")):
        try:
            llm.safe_destination(bad, None, base, (".feature",))
            FAILED.append(f"spec stage accepted {bad}")
            print(f"  FAIL accepted {bad} ({why})")
        except llm.PathRejected:
            globals()["PASSED"] = PASSED + 1
            print(f"  ok   rejected {bad} ({why})")

    # The backend/frontend guard must be unaffected by the new parameter.
    dest, _ = llm.safe_destination("backend/src/x.ts", "backend/")
    check("code stage still writes under the app directory",
          dest.relative_to(config.OUTPUT_DIR).as_posix(), "backend/src/x.ts")


# ====================================================== domain independence ==
#
# The tests below are the ones that matter for the claim "this works for any
# specification". Everything above checks that the machinery is correct; these
# check that it is not quietly built around one application.

SPEC_WITH_ACCOUNTS = """\
Feature: Borrowing

  @positive @C1
  Scenario: A member borrows a copy
    Given an approved member "ana" is signed in
    And a copy of "Ulysses" is on the shelf
    When she borrows it
    Then the loan is created
    And it is due in 21 days

  @negative @C2
  Scenario: A member may not see another member's loans
    Given a member "ana" is signed in
    When she asks for the loans of "marko"
    Then she is not permitted to see them

  @negative @C3
  Scenario: A librarian is refused a wrong password
    Given a librarian account exists
    When she signs in with an incorrect password
    Then she is not signed in
"""

SPEC_WITHOUT_ACCOUNTS = """\
Feature: Reporting a problem

  @positive @C1
  Scenario: Anyone submits a report
    Given a visitor is on the reporting page
    When they submit a description and a location
    Then the report is created with the status "reported"
    And they are given a reference number

  @negative @C2
  Scenario: A description that is too short is refused
    Given a visitor is on the reporting page
    When they submit a description of 5 characters
    Then the report is refused
    And they are told the description is too short

  @positive @C3
  Scenario: Anyone browses the reports
    Given several reports exist
    When they browse the list
    Then the reports are shown 20 to a page
    And the total number is shown
"""


def _profile_for(text: str) -> domain_profile.Profile:
    return domain_profile.detect([gherkin.parse_feature(text, "a/b.feature")])


def test_profile_detects_accounts() -> None:
    print("\nprofile — a domain with accounts")
    prof = _profile_for(SPEC_WITH_ACCOUNTS)
    check_true("authentication", prof.authentication)
    check_true("authorization", prof.authorization)
    check_true("roles", prof.roles)
    check_true("scheduling — the due date", prof.scheduling)
    check("no uploads", prof.uploads, False)
    check("no ratings", prof.ratings, False)
    check("no money", prof.money, False)
    check_true("every flag has evidence",
               all(name in prof.evidence for name in prof.enabled()))


def test_profile_detects_no_accounts() -> None:
    """The load-bearing test for the whole domain-independence claim."""
    print("\nprofile — a domain with NO accounts")
    prof = _profile_for(SPEC_WITHOUT_ACCOUNTS)
    check("authentication is off", prof.authentication, False)
    check("authorization is off", prof.authorization, False)
    check("roles are off", prof.roles, False)
    check_true("search is on", prof.search)
    check_true("pagination is on", prof.pagination)
    check_true("state machine is on", prof.state_machine)


def test_profile_implications() -> None:
    print("\nprofile — implications close over each other")
    prof = domain_profile.Profile()
    prof.roles = True
    prof = domain_profile.apply_overrides(prof, [], [])
    # roles alone does not imply anything until detect() runs the closure, so
    # exercise the closure the way detect does:
    prof = _profile_for("Feature: F\n\n  @positive @C1\n  Scenario: S\n"
                        "    Given an administrator exists\n"
                        "    When she acts\n    Then it works\n")
    check_true("roles implies authorization", prof.authorization)
    check_true("roles implies authentication", prof.authentication)


FALSE_FRIENDS = """\
Feature: Signing in

  @positive @C1
  Scenario: A member signs in
    Given the member is on the public login page
    And the member enters a unique email address
    When they confirm the login
    Then the member menu is displayed

  @negative @C2
  Scenario: The administrator form is hidden
    Given an unregistered user is on the home page
    When the user views the public login form
    Then the administrator option is not available there
"""


def test_profile_false_friends() -> None:
    """
    Words that look like a concern and are not.

    Each of these was a real false positive found by reading the evidence trail
    on the bundled specification, and each one cost more than a stray flag:
    pagination implies search, so "login page" switched on two concerns and a
    page of filtering guidance for an application with one form on it.
    """
    print("\nprofile — words that look like a concern and are not")
    prof = _profile_for(FALSE_FRIENDS)
    check("'login page' is not pagination", prof.pagination, False)
    check("...and so search stays off too", prof.search, False)
    check("'not available there' is not scheduling", prof.scheduling, False)
    check("an email FIELD is not sending email", prof.email, False)
    # What should still fire, so the tightening did not go too far:
    check_true("signing in is still authentication", prof.authentication)
    check_true("'administrator' is still a role", prof.roles)

    real = _profile_for(
        "Feature: F\n\n  @positive @C1\n  Scenario: S\n"
        "    Given a reservation from 09:00 for 3 hours exists\n"
        "    When a member asks for the next page of results\n"
        "    Then they are notified by email\n")
    check_true("a real reservation is scheduling", real.scheduling)
    check_true("a real next page is pagination", real.pagination)
    check_true("a real notification is email", real.email)


def test_profile_overrides() -> None:
    print("\nprofile — manual override")
    prof = _profile_for(SPEC_WITHOUT_ACCOUNTS)
    prof = domain_profile.apply_overrides(prof, ["authentication"], ["search"])
    check_true("forced on", prof.authentication)
    check("forced off", prof.search, False)
    check("source records the intervention", prof.source, "detected+manual")

    manual = domain_profile.from_names(["uploads", "money"])
    check("only what was named", sorted(manual.enabled()), ["money", "uploads"])
    check("source is manual", manual.source, "manual")

    try:
        domain_profile.apply_overrides(prof, ["nonsense"], [])
        FAILED.append("unknown concern accepted")
        print("  FAIL unknown concern accepted")
    except ValueError:
        globals()["PASSED"] = PASSED + 1
        print("  ok   unknown concern rejected")


def test_manifests_follow_the_profile() -> None:
    print("\nmanifests — they shrink when the domain is simpler")
    with_accounts = _profile_for(SPEC_WITH_ACCOUNTS)
    without = _profile_for(SPEC_WITHOUT_ACCOUNTS)

    mw_with = [e.path for e in pb.middlewares_manifest(with_accounts)]
    mw_without = [e.path for e in pb.middlewares_manifest(without)]
    check_true("auth middleware requested when there are accounts",
               any("auth.middleware" in p for p in mw_with))
    check("NO auth middleware when there are none",
          [p for p in mw_without if "auth" in p], [])
    check_true("validation and errors always requested",
               all(any(name in p for p in mw_without)
                   for name in ("validate.middleware", "error.middleware")))

    g_with = [e.path for e in pf.guards_manifest(with_accounts)]
    g_without = [e.path for e in pf.guards_manifest(without)]
    check_true("guards requested when there are accounts",
               any("auth.guard" in p for p in g_with))
    check_true("role guard requested when there are roles",
               any("role.guard" in p for p in g_with))
    check("NO guards at all when there are no accounts",
          [p for p in g_without if "guard" in p], [])
    check("but the error interceptor survives", len(g_without), 1)

    sc_with = [e.path for e in pb.scaffold_manifest(with_accounts)]
    sc_without = [e.path for e in pb.scaffold_manifest(without)]
    check_true("password and token helpers when there are accounts",
               any("password.ts" in p for p in sc_with)
               and any("token.ts" in p for p in sc_with))
    check("no password or token helper otherwise",
          [p for p in sc_without if "password" in p or "token" in p], [])

    check_true("expected file count follows the manifest",
               pb.minimum(pb.middlewares_manifest(with_accounts))
               > pb.minimum(pb.middlewares_manifest(without)))


AUTH_WORDS = ("Bearer", "authGuard", "CanActivateFn", "JWT", "JSON Web Token",
              "password", "sign-in", "signed in", "401", "403", "role")


def test_no_auth_leaks_into_a_no_account_domain() -> None:
    """
    A prompt for an application with no accounts must not mention any of them.

    This is the test that would have caught the original design: every prompt
    demanded an auth middleware, a JWT helper and three guards of every
    specification, including ones describing a public catalogue. The model
    complies, and you end up measuring how well a model bolts a login system
    onto an application that has no users.
    """
    print("\nprompts — nothing about accounts reaches a domain without them")
    prof = _profile_for(SPEC_WITHOUT_ACCOUNTS)
    spec = SPEC_WITHOUT_ACCOUNTS

    for name, prompt in (
        ("backend scaffold",    pb.scaffold(spec, prof)),
        ("backend middlewares", pb.middlewares(spec, prof)),
        ("backend controllers", pb.controllers(spec, prof)),
        ("backend routers",     pb.routers(spec, prof)),
        ("backend server",      pb.server(spec, prof)),
        ("frontend guards",     pf.guards(spec, prof)),
        ("frontend app shell",  pf.app_shell(spec, prof)),
    ):
        # The specification itself is embedded in every prompt, so search only
        # the instruction half — everything before the specification block.
        instructions = prompt.split("BEGIN GHERKIN SPECIFICATION")[0]
        leaked = [w for w in AUTH_WORDS if w.lower() in instructions.lower()]
        check(f"{name}: no account vocabulary", leaked, [])


def test_auth_still_reaches_a_domain_that_has_it() -> None:
    """The mirror image: narrowing must not have broken the normal case."""
    print("\nprompts — accounts still reach a domain that has them")
    prof = _profile_for(SPEC_WITH_ACCOUNTS)
    spec = SPEC_WITH_ACCOUNTS

    middlewares = pb.middlewares(spec, prof)
    check_true("bearer token described", "Bearer" in middlewares)
    check_true("403 for the wrong role", "403" in middlewares)

    guards = pf.guards(spec, prof)
    check_true("functional guard required", "CanActivateFn" in guards)
    check_true("guards are not a security boundary",
               "not a security boundary" in guards)

    scaffold = pb.scaffold(spec, prof)
    check_true("401 in the error contract", "401" in scaffold)


def test_domain_specific_advice_is_conditional() -> None:
    print("\nprompts — advice appears only where it applies")
    booking = _profile_for(SPEC_WITH_ACCOUNTS)          # has scheduling
    reports = _profile_for(SPEC_WITHOUT_ACCOUNTS)       # has none

    check_true("half-open interval rule where there are dates",
               "half-open" in pb.services(SPEC_WITH_ACCOUNTS, booking))
    check("no interval rule where there are none",
          "half-open" in pb.services(SPEC_WITHOUT_ACCOUNTS, reports), False)

    money = domain_profile.from_names(["money"])
    check_true("minor-unit rule where there is money",
               "minor units" in pb.services("x", money))
    check("no money rule otherwise",
          "minor units" in pb.services("x", domain_profile.Profile()), False)


def test_project_switching() -> None:
    print("\nprojects — set_project moves every path together")
    original = config.PROJECT
    saved = (config.FEATURES_DIR, config.OUTPUT_DIR,
             config.BACKEND_DIR, config.FRONTEND_DIR, config.BRIEF_FILE)
    try:
        config.set_project("alpha")
        first = config.FRONTEND_DIR
        check("brief follows", config.BRIEF_FILE.name, "alpha.md")
        check("spec follows", config.FEATURES_DIR.name, "alpha")
        check("output follows", config.OUTPUT_DIR.name, "alpha")
        check_true("backend under the project",
                   config.BACKEND_DIR.parent == config.OUTPUT_DIR)

        # The import-time binding bug: prompts_frontend used to compute
        # FRONTEND_SRC once at import, so every project after the first wrote
        # into the first one's directory.
        src_alpha = pf._frontend_src()
        config.set_project("beta")
        src_beta = pf._frontend_src()
        check_true("front-end source path follows the project",
                   src_alpha != src_beta)
        check_true("and points inside the new project",
                   src_beta.is_relative_to(config.FRONTEND_DIR))
        check_true("projects really are separate", first != config.FRONTEND_DIR)
    finally:
        config.set_project(original)
        (config.FEATURES_DIR, config.OUTPUT_DIR, config.BACKEND_DIR,
         config.FRONTEND_DIR, config.BRIEF_FILE) = saved


def test_bundled_briefs_are_well_formed() -> None:
    print("\nbriefs — every bundled brief parses")
    briefs_dir = Path(__file__).parent / "briefs"
    if not briefs_dir.exists():
        print("  (no briefs directory; skipped)")
        return
    found = [p for p in sorted(briefs_dir.glob("*.md")) if p.stem != "TEMPLATE"]
    check_true("at least two domains ship", len(found) >= 2)
    for path in found:
        _, capabilities = gherkin.parse_brief(path.read_text(encoding="utf-8"))
        check_true(f"{path.stem}: declares capabilities", len(capabilities) >= 8)
        numbers = sorted(int(k[1:]) for k in capabilities)
        check(f"{path.stem}: numbered from 1 without gaps",
              numbers, list(range(1, len(numbers) + 1)))


# ================================================================== main ====
def main() -> int:
    print("=" * 72)
    print("  pipeline instrument tests")
    print("=" * 72)

    test_parse_plain()
    test_parse_chatty_model()
    test_parse_markdown_keeps_nested_fences()
    test_parse_truncated()
    test_parse_no_markers()
    test_path_guard()
    test_route_extraction()
    test_module_key()
    test_compiler_parsing()
    test_blocked_detection()
    test_placeholders()
    test_spec_counts()
    test_context_budget()
    test_gherkin_parse()
    test_gherkin_lint_clean()
    test_gherkin_lint_catches()
    test_gherkin_coverage()
    test_gherkin_metrics()
    test_step_normalisation()
    test_brief_parsing()
    test_spec_prompt_is_zero_shot()
    test_spec_path_guard()
    test_profile_detects_accounts()
    test_profile_detects_no_accounts()
    test_profile_implications()
    test_profile_false_friends()
    test_profile_overrides()
    test_manifests_follow_the_profile()
    test_no_auth_leaks_into_a_no_account_domain()
    test_auth_still_reaches_a_domain_that_has_it()
    test_domain_specific_advice_is_conditional()
    test_project_switching()
    test_bundled_briefs_are_well_formed()

    print("\n" + "=" * 72)
    if FAILED:
        print(f"  {len(FAILED)} FAILED, {PASSED} passed")
        for name in FAILED:
            print(f"    - {name}")
        return 1
    print(f"  all {PASSED} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
