"""
profile.py — work out what kind of application this specification describes.

The problem this solves. The backend prompts used to demand, of every
specification, an authentication middleware, an authorization middleware, a JWT
utility, a password hasher and an initial-administrator bootstrap. The front-end
prompts demanded an auth guard, a role guard, a guest guard and a bearer-token
interceptor. That is correct for a booking system with members and
administrators, and wrong for a public timetable, a calculator, a catalogue
browser, a survey, or any of the other things a specification might describe.

Asking a model for files the domain does not need is not harmless. It will
produce them — models comply — and you end up with a login system bolted to an
application nobody logs into, plus a stage that "failed" because it returned two
files where the manifest listed five. The measurement is then of the prompt's
assumptions rather than of the model.

So: read the specification, and let it say what the application needs. Every
flag here turns prompt sections on and off, and each one is reported at the top
of the run so you can see what was inferred and correct it if it is wrong.

## How detection works, and its limits

This is keyword matching over the step text, plus a little structure. It is not
natural-language understanding and does not pretend to be. Two consequences
shape the design:

  * **Errors are made in the safe direction.** A false positive costs a file
    nobody uses. A false negative costs an application with no access control on
    a specification that required it. So every signal is generous: one clear
    mention is enough, and related concerns are pulled in together
    (authorization implies authentication; roles imply authorization).

  * **It is always overridable.** `--profile` and `--no-profile` on the pipeline
    set the flags by hand. When you report results, report the profile: two
    models given different profiles were given different tasks.

The vocabularies are English because the prompts and the brief are English. For
a Serbian specification, add the terms to the tuples below — that is the whole
change, and the tests will tell you if a term is ambiguous.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field

import gherkin

# Each concern maps to the words that, appearing anywhere in a step, a scenario
# name or a feature name, mean the specification is talking about it.
#
# Terms are matched on word boundaries, so "rate" does not fire on "generate"
# and "pay" does not fire on "page". Multi-word terms are matched as phrases.
SIGNALS: dict[str, tuple[str, ...]] = {
    "authentication": (
        "sign in", "signs in", "signed in", "sign out", "signs out", "log in",
        "logs in", "logged in", "log out", "login", "logout", "password",
        "credential", "credentials", "authenticate", "authenticated",
        "authentication", "session", "token", "account", "register",
        "registration", "registers", "sign up", "signs up",
    ),
    "authorization": (
        "permission", "permitted", "not allowed", "forbidden", "denied",
        "unauthorised", "unauthorized", "authorise", "authorize", "may not",
        "cannot see", "belongs to another", "someone else", "another user",
        "their own", "his own", "her own", "owner", "owns",
    ),
    # Only PRIVILEGED actors count as roles.
    #
    # This list used to include "visitor", "guest", "member", "customer" and
    # "user". Those are not roles, they are the words every specification uses
    # for "a person" — "Given a visitor is on the reporting page" appears in
    # specifications for entirely public applications. Because roles imply
    # authorization and authorization implies authentication, one such phrase
    # gave a public issue-reporting system a full login system, role middleware
    # and three route guards.
    #
    # A role, for this purpose, is an actor the specification distinguishes
    # *because they may do more than everyone else*. If a domain's only actors
    # are "visitor" and "member", roles stays off and the application gets
    # authentication without a role factory, which is the right shape.
    "roles": (
        "role", "roles", "administrator", "administrators", "admin", "admins",
        "moderator", "staff", "manager", "managers", "supervisor", "editor",
        "librarian", "curator", "operator", "owner of the", "privileged",
    ),
    "uploads": (
        "upload", "uploads", "uploaded", "photograph", "photo", "image",
        "picture", "attachment", "attach", "file", "avatar", "thumbnail",
        "document", "scan", "pdf",
    ),
    "search": (
        "search", "searches", "filter", "filters", "filtered", "sort",
        "sorted", "order by", "ordered by", "results", "query", "browse",
        "find", "look up", "listing", "listings",
    ),
    # NOT bare "page": "the member is on the login page" is a web page, not
    # pagination, and it appears in almost every specification ever written.
    # Because pagination implies search, that one phrase used to switch on two
    # concerns and a page of prompt guidance for a two-screen application.
    "pagination": (
        "per page", "next page", "previous page", "paginate", "pagination",
        "first page", "load more", "to a page", "page size", "page of results",
        "pages of results",
    ),
    # NOT bare "available": "the administrator form is not available through the
    # public page" is about visibility, not scheduling. Availability in the
    # booking sense always travels with a date, an hour or a reservation, all of
    # which are listed here anyway.
    "scheduling": (
        "date", "time", "hour", "hours", "minute", "day", "days", "week",
        "month", "schedule", "scheduled", "booking", "reserve", "reserves",
        "reservation", "appointment", "slot", "period", "duration", "overlap",
        "overlaps", "calendar", "deadline", "expires", "expiry", "expired",
        "opening hours", "due date", "overdue", "renew",
    ),
    "money": (
        "price", "priced", "cost", "costs", "fee", "charge", "charged",
        "payment", "pay", "paid", "invoice", "euro", "euros", "dollar",
        "dollars", "amount", "total", "discount", "refund", "currency",
    ),
    # This concern means the application SENDS messages, which pulls in an SMTP
    # dependency and a section of guidance about side effects at the edge of a
    # rule. A stored email address is not that: "enters a unique email address"
    # is a registration field, and used to switch the whole thing on.
    "email": (
        "by email", "an email is sent", "is sent an email", "receives an email",
        "receive an email", "emailed", "sends an email", "notification",
        "notifications", "notify", "notified", "message is sent",
        "sends a message", "inbox", "reset link", "confirmation link",
        "verification link",
    ),
    "import_export": (
        "import", "imports", "imported", "export", "exports", "exported",
        "json file", "csv", "csv file", "spreadsheet", "bulk", "in bulk",
        "upload a file of", "download the list",
    ),
    "ratings": (
        "rate", "rates", "rating", "ratings", "review", "reviews", "comment",
        "comments", "star", "stars", "score", "feedback", "vote", "votes",
    ),
    "state_machine": (
        "status", "state", "pending", "approved", "approve", "rejected",
        "reject", "cancelled", "canceled", "cancel", "confirmed", "confirm",
        "draft", "published", "publish", "archived", "archive", "withdrawn",
        "withdraw", "completed", "in progress",
    ),
}

# Concerns that drag others in with them. A specification that talks about
# permissions but never about signing in is almost certainly one where signing
# in was left implicit, not one where anyone may do anything.
IMPLIES: dict[str, tuple[str, ...]] = {
    "authorization": ("authentication",),
    "roles": ("authentication", "authorization"),
    "import_export": ("uploads",),
    "pagination": ("search",),
}

ALL_CONCERNS = tuple(SIGNALS)


@dataclass
class Profile:
    """What this specification needs. Every field drives a prompt section."""

    authentication: bool = False
    authorization: bool = False
    roles: bool = False
    uploads: bool = False
    search: bool = False
    pagination: bool = False
    scheduling: bool = False
    money: bool = False
    email: bool = False
    import_export: bool = False
    ratings: bool = False
    state_machine: bool = False

    # Not detected from vocabulary: read off the structure of the spec.
    areas: int = 0
    scenarios: int = 0
    entities_hint: int = 0

    evidence: dict[str, str] = field(default_factory=dict)
    source: str = "detected"          # "detected", "manual", or "detected+manual"

    def enabled(self) -> list[str]:
        return [name for name in ALL_CONCERNS if getattr(self, name)]

    def to_dict(self) -> dict:
        return asdict(self)

    def describe(self) -> str:
        on = self.enabled()
        if not on:
            return "  (no cross-cutting concerns detected — a plain CRUD application)"
        lines = []
        for name in on:
            why = self.evidence.get(name, "")
            lines.append(f"    {name:<16}{'  ← ' + why if why else ''}")
        return "\n".join(lines)


# ---------------------------------------------------------------- detect ---
def _compile(terms: tuple[str, ...]) -> re.Pattern:
    parts = [r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"\b" for term in terms]
    return re.compile("|".join(parts), re.IGNORECASE)


_PATTERNS = {name: _compile(terms) for name, terms in SIGNALS.items()}


def _corpus(features: list[gherkin.Feature]) -> list[str]:
    """Every piece of natural language in the specification, as separate lines."""
    lines: list[str] = []
    for feature in features:
        lines.append(feature.name)
        lines.extend(f"@{t}" for t in feature.tags)
        lines.extend(step.text for step in feature.background)
        for scenario in feature.scenarios:
            lines.append(scenario.name)
            lines.extend(f"@{t}" for t in scenario.tags)
            lines.extend(step.text for step in scenario.steps)
            for block in scenario.examples:
                lines.extend(block.header)
                for row in block.rows:
                    lines.extend(row)
    return [line for line in lines if line]


def detect(features: list[gherkin.Feature]) -> Profile:
    """
    Infer the profile from a parsed specification.

    Each concern records the line that triggered it, so a surprising flag can be
    traced to the sentence responsible rather than argued about.
    """
    profile = Profile()
    lines = _corpus(features)

    for name, pattern in _PATTERNS.items():
        for line in lines:
            match = pattern.search(line)
            if match:
                setattr(profile, name, True)
                snippet = line.strip()
                if len(snippet) > 70:
                    snippet = snippet[:67] + "..."
                profile.evidence[name] = f'"{match.group(0)}" in {snippet!r}'
                break

    # Closure over implications, iterated because implications chain.
    changed = True
    while changed:
        changed = False
        for concern, implied in IMPLIES.items():
            if not getattr(profile, concern):
                continue
            for other in implied:
                if not getattr(profile, other):
                    setattr(profile, other, True)
                    profile.evidence.setdefault(
                        other, f"implied by {concern}")
                    changed = True

    profile.areas = len({f.path.split("/")[0] for f in features if "/" in f.path}) \
        or len(features)
    profile.scenarios = sum(len(f.scenarios) for f in features)
    profile.entities_hint = _estimate_entities(features)
    return profile


def _estimate_entities(features: list[gherkin.Feature]) -> int:
    """
    A rough count of the things this application stores.

    Used only to set a floor on how many model files to expect, so that a
    twelve-entity domain is not judged against the same minimum as a
    two-entity one. Deliberately crude: it counts distinct capitalised or
    quoted nouns appearing in Given steps, which is where a specification
    establishes what exists. Being wrong here costs a slightly loose or
    slightly tight expectation, nothing more.
    """
    nouns: set[str] = set()
    for feature in features:
        steps = list(feature.background)
        for scenario in feature.scenarios:
            steps.extend(s for s in scenario.steps if s.keyword in ("Given", "And"))
        for step in steps:
            for word in re.findall(r'"([^"]{3,40})"', step.text):
                nouns.add(word.strip().lower())
            for word in re.findall(r"\b(?:a|an|the)\s+([a-z]{4,})\b", step.text.lower()):
                if word not in _STOPWORDS:
                    nouns.add(word)
    return max(1, min(len(nouns) // 3, 15))


_STOPWORDS = {
    "system", "page", "form", "screen", "user", "correct", "incorrect", "valid",
    "invalid", "following", "same", "other", "first", "last", "next", "with",
    "that", "this", "their", "there", "where", "which", "when", "then", "given",
    "already", "exists", "does", "have", "been", "were", "will", "shall",
    "message", "error", "value", "field", "list", "item", "items", "data",
    "empty", "full", "part", "time", "date", "name", "text", "line", "case",
}


# ------------------------------------------------------------- overrides ---
def apply_overrides(profile: Profile, enable: list[str] | None = None,
                    disable: list[str] | None = None) -> Profile:
    """Force concerns on or off. Unknown names raise rather than being ignored."""
    touched = False
    for name in enable or []:
        if name not in ALL_CONCERNS:
            raise ValueError(f"unknown concern {name!r}; known: {', '.join(ALL_CONCERNS)}")
        setattr(profile, name, True)
        profile.evidence[name] = "forced on from the command line"
        touched = True
    for name in disable or []:
        if name not in ALL_CONCERNS:
            raise ValueError(f"unknown concern {name!r}; known: {', '.join(ALL_CONCERNS)}")
        setattr(profile, name, False)
        profile.evidence.pop(name, None)
        touched = True
    if touched:
        profile.source = "manual" if profile.source == "manual" else "detected+manual"
    return profile


def from_names(names: list[str]) -> Profile:
    """Build a profile entirely by hand, skipping detection."""
    profile = Profile(source="manual")
    for name in names:
        if name not in ALL_CONCERNS:
            raise ValueError(f"unknown concern {name!r}; known: {', '.join(ALL_CONCERNS)}")
        setattr(profile, name, True)
        profile.evidence[name] = "set from the command line"
    return profile
