"""
gherkin.py — parse, validate and measure .feature files.

The pipeline now generates its own specification (see spec_generation.py), which
means the specification stops being a fixed input and becomes one of the things
under measurement. That only works if "is this a good specification?" has an
answer that does not depend on reading all of it by hand.

So this module does three things:

1. Parses Gherkin well enough to see structure — features, scenarios, outlines,
   tags, steps, Examples tables.
2. Lints it against the contract the generation prompt states. A scenario with
   no Then, an Outline whose placeholders do not match its Examples header, a
   scenario tagged neither positive nor negative: all of these are objectively
   wrong, and all of them are things small models produce.
3. Produces the metrics the thesis needs. "How many scenarios" is a weak
   measure — a model can pad. Capability coverage, negative-path share and step
   reuse say considerably more about whether a specification is worth compiling
   code from.

This is not a full Gherkin implementation and does not try to be. It is
deliberately strict about the subset the prompt asks for, because a strict
parser that reports what it cannot handle is more useful here than a lenient one
that quietly accepts a malformed file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import config

STEP_KEYWORDS = ("Given", "When", "Then", "And", "But", "*")

_TAG_LINE = re.compile(r"^\s*@[\w@\-. ]+$")
_TAG = re.compile(r"@([\w\-.]+)")
_FEATURE = re.compile(r"^\s*Feature:\s*(?P<name>.*)$")
_BACKGROUND = re.compile(r"^\s*Background:\s*(?P<name>.*)$")
_SCENARIO = re.compile(r"^\s*(?P<kind>Scenario Outline|Scenario Template|Scenario):\s*(?P<name>.*)$")
_EXAMPLES = re.compile(r"^\s*(?:Examples|Scenarios):\s*(?P<name>.*)$")
_STEP = re.compile(r"^\s*(?P<keyword>Given|When|Then|And|But|\*)\s+(?P<text>.+?)\s*$")
_TABLE_ROW = re.compile(r"^\s*\|(?P<body>.*)\|\s*$")
_PLACEHOLDER = re.compile(r"<([^<>]+)>")
_COMMENT = re.compile(r"^\s*#")


# ----------------------------------------------------------------- model ---
@dataclass
class Step:
    keyword: str
    text: str
    line: int


@dataclass
class Examples:
    header: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    line: int = 0


@dataclass
class Scenario:
    name: str
    kind: str                       # "Scenario" or "Scenario Outline"
    tags: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    examples: list[Examples] = field(default_factory=list)
    line: int = 0

    @property
    def is_outline(self) -> bool:
        return self.kind != "Scenario"

    def keywords(self) -> set[str]:
        """The effective step keywords, resolving And/But to what they continue."""
        resolved: set[str] = set()
        current = ""
        for step in self.steps:
            if step.keyword in ("Given", "When", "Then"):
                current = step.keyword
            if current:
                resolved.add(current)
        return resolved

    def example_rows(self) -> int:
        return sum(len(block.rows) for block in self.examples)


@dataclass
class Feature:
    path: str
    name: str = ""
    tags: list[str] = field(default_factory=list)
    background: list[Step] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)
    line: int = 0


@dataclass
class Issue:
    path: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


# ---------------------------------------------------------------- parser ---
def _split_row(body: str) -> list[str]:
    return [cell.strip() for cell in body.split("|")]


def parse_feature(text: str, path: str) -> Feature:
    """Parse one .feature file. Never raises; malformed input surfaces in lint()."""
    feature = Feature(path=path)
    pending_tags: list[str] = []
    scenario: Scenario | None = None
    examples: Examples | None = None
    in_background = False
    in_docstring = False

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        if line.strip().startswith(('"""', "```")):
            in_docstring = not in_docstring
            continue
        if in_docstring:
            if scenario and scenario.steps:
                scenario.steps[-1].text += "\n" + line.strip()
            continue

        if not line.strip() or _COMMENT.match(line):
            continue

        if _TAG_LINE.match(line):
            pending_tags.extend(_TAG.findall(line))
            continue

        match = _FEATURE.match(line)
        if match:
            feature.name = match.group("name").strip()
            feature.tags = pending_tags
            feature.line = number
            pending_tags = []
            scenario, examples, in_background = None, None, False
            continue

        if _BACKGROUND.match(line):
            in_background = True
            scenario, examples = None, None
            pending_tags = []
            continue

        match = _SCENARIO.match(line)
        if match:
            kind = "Scenario" if match.group("kind") == "Scenario" else "Scenario Outline"
            scenario = Scenario(name=match.group("name").strip(), kind=kind,
                                tags=pending_tags, line=number)
            feature.scenarios.append(scenario)
            pending_tags = []
            examples = None
            in_background = False
            continue

        match = _EXAMPLES.match(line)
        if match:
            examples = Examples(line=number)
            if scenario is not None:
                scenario.examples.append(examples)
            pending_tags = []
            continue

        match = _TABLE_ROW.match(line)
        if match:
            cells = _split_row(match.group("body"))
            if examples is not None:
                if not examples.header:
                    examples.header = cells
                else:
                    examples.rows.append(cells)
            elif scenario is not None and scenario.steps:
                # A data table attached to a step. Kept as part of the step text
                # so that placeholder checking still sees it.
                scenario.steps[-1].text += "\n| " + " | ".join(cells) + " |"
            continue

        match = _STEP.match(line)
        if match:
            step = Step(match.group("keyword"), match.group("text").strip(), number)
            if in_background:
                feature.background.append(step)
            elif scenario is not None:
                scenario.steps.append(step)
            continue

        # Anything else is free text under Feature: — a description. Ignored.

    return feature


def load_features(directory: Path) -> list[Feature]:
    features: list[Feature] = []
    for path in sorted(directory.rglob("*.feature")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        features.append(parse_feature(text, path.relative_to(directory).as_posix()))
    return features


# ------------------------------------------------------------------ lint ---
def lint_feature(feature: Feature, capabilities: set[str] | None = None) -> list[Issue]:
    """
    Check one feature against the contract the generation prompt states.

    Every rule here corresponds to a sentence in prompts_spec.py. If you relax
    one, relax the prompt too — a linter that enforces something the model was
    never told is a linter that manufactures failures.
    """
    issues: list[Issue] = []
    path = feature.path

    def add(line: int, rule: str, message: str) -> None:
        issues.append(Issue(path, line, rule, message))

    if not feature.name:
        add(1, "feature-missing", "no `Feature:` line in this file")
    if not feature.scenarios:
        add(feature.line or 1, "feature-empty", "the feature declares no scenarios")

    seen_names: dict[str, int] = {}
    background_keywords = {s.keyword for s in feature.background}

    for scenario in feature.scenarios:
        line = scenario.line

        if not scenario.name:
            add(line, "scenario-unnamed", "scenario has no name")
        else:
            key = scenario.name.strip().lower()
            if key in seen_names:
                add(line, "scenario-duplicate",
                    f"duplicate scenario name, first seen at line {seen_names[key]}")
            else:
                seen_names[key] = line

        # --- steps ------------------------------------------------------
        if not scenario.steps:
            add(line, "scenario-empty", "scenario has no steps")
        else:
            if scenario.steps[0].keyword in ("And", "But"):
                add(scenario.steps[0].line, "step-continuation-first",
                    "the first step is And/But, which continues nothing")
            keywords = scenario.keywords()
            has_given = "Given" in keywords or "Given" in background_keywords
            if not has_given:
                add(line, "step-no-given",
                    "no Given, and the Background does not supply one")
            if "When" not in keywords:
                add(line, "step-no-when", "no When — nothing is exercised")
            if "Then" not in keywords:
                add(line, "step-no-then", "no Then — nothing is asserted")

        # --- tags -------------------------------------------------------
        polarity = [t for t in scenario.tags if t in ("positive", "negative")]
        if not polarity:
            add(line, "tag-no-polarity",
                "scenario is tagged neither @positive nor @negative")
        elif len(polarity) > 1:
            add(line, "tag-both-polarities",
                f"scenario is tagged both @positive and @negative")

        if capabilities is not None:
            covered = [t for t in scenario.tags if t.upper().startswith("C")
                       and t.upper() in capabilities]
            unknown = [t for t in scenario.tags
                       if re.fullmatch(r"C\d+", t.upper()) and t.upper() not in capabilities]
            if unknown:
                add(line, "tag-unknown-capability",
                    f"references capabilities that are not in the brief: {unknown}")
            if not covered:
                add(line, "tag-no-capability",
                    "scenario carries no @C<n> tag, so it maps to no stated capability")

        # --- outlines ---------------------------------------------------
        placeholders = set()
        for step in scenario.steps:
            placeholders.update(_PLACEHOLDER.findall(step.text))

        if scenario.is_outline:
            if not scenario.examples:
                add(line, "outline-no-examples", "Scenario Outline with no Examples table")
            for block in scenario.examples:
                if not block.header:
                    add(block.line, "examples-no-header", "Examples table has no header row")
                    continue
                if not block.rows:
                    add(block.line, "examples-no-rows",
                        "Examples table has a header but no data rows")
                elif len(block.rows) < 2:
                    # An Outline with one row is a Scenario carrying extra
                    # ceremony, and it is a common way for a model to look like
                    # it covered a boundary without covering it: the whole point
                    # of the shape is the case on each side of the limit.
                    add(block.line, "examples-too-few-rows",
                        f"Examples table has {len(block.rows)} data row; an "
                        f"Outline needs at least 2 to be worth its shape")
                width = len(block.header)
                for index, row in enumerate(block.rows, start=1):
                    if len(row) != width:
                        add(block.line + index, "examples-ragged",
                            f"row has {len(row)} cells, the header has {width}")
                header = set(block.header)
                missing = placeholders - header
                unused = header - placeholders
                if missing:
                    add(block.line, "outline-placeholder-missing",
                        f"steps use <{'>, <'.join(sorted(missing))}> "
                        f"but the Examples header does not declare it")
                if unused:
                    add(block.line, "outline-column-unused",
                        f"Examples declares {sorted(unused)} which no step uses")
        else:
            if placeholders:
                add(line, "placeholder-in-scenario",
                    f"a plain Scenario uses <{'>, <'.join(sorted(placeholders))}>; "
                    f"placeholders only work in a Scenario Outline")
            if scenario.examples:
                add(line, "examples-in-scenario",
                    "a plain Scenario has an Examples table; it should be an Outline")

        # --- stub text --------------------------------------------------
        for step in scenario.steps:
            upper = step.text.upper()
            for marker in config.PLACEHOLDER_MARKERS_STRONG:
                if marker.upper() in upper:
                    add(step.line, "step-placeholder",
                        f"step contains {marker!r}")
                    break

    return issues


def lint(features: list[Feature], capabilities: set[str] | None = None) -> list[Issue]:
    issues: list[Issue] = []
    for feature in features:
        issues.extend(lint_feature(feature, capabilities))

    # Cross-file: a capability nobody covers is the most important finding here,
    # because it is invisible when reading any single file.
    if capabilities:
        covered = {t.upper() for f in features for s in f.scenarios for t in s.tags
                   if re.fullmatch(r"C\d+", t.upper())}
        for missing in sorted(capabilities - covered, key=_capability_order):
            issues.append(Issue("<specification>", 0, "capability-uncovered",
                                f"{missing} from the brief has no scenario"))
    return issues


def _capability_order(tag: str) -> int:
    match = re.fullmatch(r"C(\d+)", tag.upper())
    return int(match.group(1)) if match else 0


# --------------------------------------------------------------- metrics ---
def metrics(features: list[Feature], capabilities: set[str] | None = None) -> dict:
    """
    The numbers that describe a specification.

    Scenario count alone is a weak measure — padding is cheap and a model that
    writes forty shallow scenarios looks better than one that writes twenty
    sharp ones. These are chosen to be harder to pad:

    - `capability_coverage` — of the capabilities the brief stated, how many
      have at least one scenario. Padding does not move it; missing a
      requirement does.
    - `negative_share` — the fraction of scenarios exercising a refusal. A
      specification that only describes the happy path produces an application
      that only handles the happy path, and this is where small models tend to
      fall short.
    - `step_reuse` — total steps divided by distinct step texts. A specification
      that says "the member is logged in" fifteen different ways is one that
      cannot be automated, and it is the single most common flaw in
      machine-written Gherkin.
    - `examples_rows` — concrete cases, which is what an Outline is worth. An
      Outline with one row is a Scenario with extra ceremony.
    """
    scenarios = [s for f in features for s in f.scenarios]
    steps = [step for s in scenarios for step in s.steps]
    steps += [step for f in features for step in f.background]

    negative = [s for s in scenarios if "negative" in s.tags]
    positive = [s for s in scenarios if "positive" in s.tags]
    normalised = [_normalise_step(s.text) for s in steps]
    distinct = len(set(normalised))

    covered: set[str] = set()
    for scenario in scenarios:
        for tag in scenario.tags:
            if re.fullmatch(r"C\d+", tag.upper()):
                covered.add(tag.upper())

    result = {
        "files": len(features),
        "areas": len({Path(f.path).parent.as_posix() for f in features}),
        "features": len([f for f in features if f.name]),
        "scenarios": len([s for s in scenarios if not s.is_outline]),
        "scenario_outlines": len([s for s in scenarios if s.is_outline]),
        "scenarios_total": len(scenarios),
        "examples_rows": sum(s.example_rows() for s in scenarios),
        "steps": len(steps),
        "distinct_steps": distinct,
        "step_reuse": round(len(steps) / distinct, 2) if distinct else 0.0,
        "steps_per_scenario": round(len(steps) / len(scenarios), 1) if scenarios else 0.0,
        "positive": len(positive),
        "negative": len(negative),
        "untagged_polarity": len(scenarios) - len(positive) - len(negative),
        "negative_share": round(len(negative) / len(scenarios), 2) if scenarios else 0.0,
        "ui_tagged": len([s for s in scenarios if "ui" in s.tags]),
    }
    if capabilities:
        result["capabilities_total"] = len(capabilities)
        result["capabilities_covered"] = len(covered & capabilities)
        result["capability_coverage"] = round(
            len(covered & capabilities) / len(capabilities), 2)
        result["capabilities_missing"] = sorted(capabilities - covered,
                                                key=_capability_order)
    return result


def _normalise_step(text: str) -> str:
    """
    Compare step texts the way a step-definition file would.

    Quoted values and numbers are arguments, not different steps: `enters "ana"`
    and `enters "marko"` are one step used twice. Without this the reuse metric
    would reward a specification for repeating itself with different data, which
    is the opposite of what it is meant to detect.
    """
    text = text.split("\n")[0].strip().lower()
    text = re.sub(r'"[^"]*"', '"?"', text)
    text = re.sub(r"<[^>]*>", "<?>", text)
    text = re.sub(r"\b\d+(?:[.,]\d+)?\b", "?", text)
    return re.sub(r"\s+", " ", text)


# ------------------------------------------------------------ the brief ----
_CAPABILITY = re.compile(r"^\s*-?\s*\*{0,2}(C\d+)\*{0,2}\s*[.:—-]\s*(?P<text>.+?)\s*$",
                         re.IGNORECASE)


def parse_brief(text: str) -> tuple[str, dict[str, str]]:
    """
    Read the brief and pull out its numbered capabilities.

    A capability line looks like `C3: a member may cancel a reservation`. The
    identifiers are what make coverage measurable: the prompt requires every
    scenario to carry the tag of the capability it exercises, so "did the model
    address requirement C7" stops being a judgement call.
    """
    capabilities: dict[str, str] = {}
    for line in text.splitlines():
        match = _CAPABILITY.match(line)
        if match:
            capabilities[match.group(1).upper()] = match.group("text").strip()
    return text, capabilities


def format_issues(issues: list[Issue], limit: int = 60) -> str:
    if not issues:
        return "  (none)"
    shown = issues[:limit]
    body = "\n".join(f"  {issue}" for issue in shown)
    if len(issues) > limit:
        body += f"\n  ... and {len(issues) - limit} more"
    return body
