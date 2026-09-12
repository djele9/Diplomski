#!/usr/bin/env python3
"""
spec_generation.py — stage zero: the model writes the specification.

    python3 spec_generation.py                          # generate from brief.md
    python3 spec_generation.py --model llama3.1:8b
    python3 spec_generation.py --brief other-brief.md
    python3 spec_generation.py --out features_llama     # do not overwrite features/
    python3 spec_generation.py --lint-only              # check an existing spec

The mentor's step one, in his words: use zero-shot prompting to design the user
stories and scenarios, positive and negative. Everything the rest of this
pipeline does — generate a backend, generate a front end, compile both — runs on
whatever comes out of here.

That inversion is worth being clear about. Until now the specification was a
hand-written constant and the models were judged on the code they produced from
it. Now the specification is itself model output, so a run measures two things
at once, and they have to be kept apart:

  * **Specification quality** — measured here, before a line of code exists, by
    gherkin.metrics: capability coverage, negative-path share, structural
    validity, step reuse.
  * **Code quality** — measured downstream by compilation and repair rounds.

A model that writes a thin specification will produce a small application that
compiles perfectly, and an end-to-end score would call that a success. It is
not one. Report the two separately, and use `--spec-model` in pipeline.py when
you want every model to write code from the *same* specification, which is the
only way to compare code generation on its own.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
import gherkin
import llm
import prompts_spec


def _banner(text: str) -> None:
    print(f"\n{'=' * 72}\n  {text}\n{'=' * 72}")


def load_brief(path: Path) -> tuple[str, dict[str, str]]:
    if not path.exists():
        raise RuntimeError(
            f"No brief at {path}. The brief is the plain-language description of "
            f"the application, and it is the only input to the zero-shot stage. "
            f"See the bundled brief.md for the shape it needs — in particular the "
            f"numbered `C<n>:` capability lines, which are what make coverage "
            f"measurable."
        )
    text = path.read_text(encoding="utf-8")
    brief, capabilities = gherkin.parse_brief(text)
    if not capabilities:
        raise RuntimeError(
            f"{path} declares no capabilities. Each one is a line like\n"
            f"    C1: a visitor can register as a member\n"
            f"Without them the specification cannot be scored for coverage, and "
            f"the model has nothing to tag its scenarios with."
        )
    return brief, capabilities


def _current_specification(directory: Path) -> str:
    """Every generated .feature file, concatenated, for the repair prompt."""
    parts = []
    for path in sorted(directory.rglob("*.feature")):
        rel = path.relative_to(directory).as_posix()
        parts.append(f"\n\n===== {rel} =====\n{path.read_text(encoding='utf-8')}")
    return "".join(parts)


def generate(
    brief_path: Path | None = None,
    out_dir: Path | None = None,
    model: str | None = None,
    max_rounds: int | None = None,
    wipe: bool = True,
) -> dict:
    """
    Generate the specification and validate it. Returns the report dictionary.

    The repair loop mirrors the compile loop downstream: produce, check, feed the
    faults back, bounded. What it checks is the linter rather than a compiler,
    but the shape and the reason are the same — the first attempt of a small
    model is rarely structurally valid, and "valid after two rounds" is a much
    more informative result than "invalid".
    """
    brief_path = brief_path or config.BRIEF_FILE
    out_dir = out_dir or config.FEATURES_DIR
    max_rounds = max_rounds if max_rounds is not None else config.MAX_SPEC_REPAIR_ROUNDS
    model = model or config.MODEL

    brief, capabilities = load_brief(brief_path)
    capability_ids = set(capabilities)

    _banner(f"SPECIFICATION (zero-shot)  —  {model}")
    print(f"  brief        {brief_path}")
    print(f"  capabilities {len(capabilities)}: {', '.join(sorted(capability_ids, key=lambda c: int(c[1:])))}")
    print(f"  output       {out_dir}")

    if wipe and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "model": model,
        "brief": str(brief_path),
        "capabilities": len(capabilities),
        "rounds_used": 0,
        "first_attempt_valid": None,
        "valid": False,
        "issues": [],
        "metrics": {},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    record = llm.call(
        "spec-1-zero-shot",
        prompts_spec.specification(brief, capabilities),
        expect_files=1,
        output_base=out_dir,
        allowed_suffixes=(".feature",),
        model=model,
    )
    if not record.files_written:
        report["issues"] = [f"the model produced no feature files: {record.failure}"]
        print("\n  the model produced no usable feature files; nothing to validate")
        _write_report(report, out_dir)
        return report

    features = gherkin.load_features(out_dir)
    issues = gherkin.lint(features, capability_ids)
    report["first_attempt_valid"] = not issues
    print(f"\n  first attempt: {len(features)} file(s), "
          f"{sum(len(f.scenarios) for f in features)} scenario(s), "
          f"{len(issues)} validation issue(s)")

    round_number = 0
    while issues and round_number < max_rounds:
        round_number += 1
        print(f"\n=== specification repair round {round_number}/{max_rounds} ===")
        print(gherkin.format_issues(issues, limit=15))

        try:
            repair_record = llm.call(
                "spec-2-repair",
                prompts_spec.repair(brief, capabilities,
                                    gherkin.format_issues(issues, limit=80),
                                    _current_specification(out_dir)),
                output_base=out_dir,
                allowed_suffixes=(".feature",),
                model=model,
                repair_round=round_number,
            )
        except llm.ModelUnavailable as exc:
            print(f"  repair stopped: {exc}")
            break
        if not repair_record.files_written:
            print("  the repair returned no usable files; stopping")
            break

        previous = len(issues)
        features = gherkin.load_features(out_dir)
        issues = gherkin.lint(features, capability_ids)
        print(f"  {len(issues)} issue(s) remain (was {previous})")
        if issues and len(issues) >= previous:
            print("  no improvement this round; stopping rather than looping")
            break

    report["rounds_used"] = round_number
    report["valid"] = not issues
    report["issues"] = [str(i) for i in issues]
    report["metrics"] = gherkin.metrics(features, capability_ids)
    _summarise(report, issues)
    _write_report(report, out_dir)
    return report


def lint_only(directory: Path, brief_path: Path | None = None) -> dict:
    """Validate a specification that already exists — generated or hand-written."""
    brief_path = brief_path or config.BRIEF_FILE
    capability_ids: set[str] | None = None
    if brief_path.exists():
        _, capabilities = gherkin.parse_brief(brief_path.read_text(encoding="utf-8"))
        capability_ids = set(capabilities) or None

    features = gherkin.load_features(directory)
    if not features:
        raise RuntimeError(f"No .feature files under {directory}")
    issues = gherkin.lint(features, capability_ids)
    report = {
        "model": None,
        "brief": str(brief_path) if capability_ids else None,
        "capabilities": len(capability_ids) if capability_ids else 0,
        "rounds_used": 0,
        "first_attempt_valid": not issues,
        "valid": not issues,
        "issues": [str(i) for i in issues],
        "metrics": gherkin.metrics(features, capability_ids),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _banner(f"SPECIFICATION LINT  —  {directory}")
    _summarise(report, issues)
    return report


def _summarise(report: dict, issues: list) -> None:
    metrics = report["metrics"]
    _banner("SPECIFICATION " + ("VALID" if report["valid"] else "INVALID"))
    print(f"  files {metrics.get('files', 0)} in {metrics.get('areas', 0)} area(s), "
          f"{metrics.get('scenarios_total', 0)} scenario(s) "
          f"({metrics.get('scenarios', 0)} plain, "
          f"{metrics.get('scenario_outlines', 0)} outlines, "
          f"{metrics.get('examples_rows', 0)} example rows)")
    print(f"  positive {metrics.get('positive', 0)}  "
          f"negative {metrics.get('negative', 0)}  "
          f"(negative share {metrics.get('negative_share', 0):.0%})")
    if "capability_coverage" in metrics:
        print(f"  capability coverage {metrics['capabilities_covered']}"
              f"/{metrics['capabilities_total']} "
              f"({metrics['capability_coverage']:.0%})")
        if metrics.get("capabilities_missing"):
            print(f"  NOT COVERED: {', '.join(metrics['capabilities_missing'])}")
    print(f"  steps {metrics.get('steps', 0)}, "
          f"{metrics.get('distinct_steps', 0)} distinct "
          f"(reuse {metrics.get('step_reuse', 0)}x, "
          f"{metrics.get('steps_per_scenario', 0)} per scenario)")
    print(f"  repair rounds used: {report['rounds_used']}"
          f"   valid on first attempt: {report['first_attempt_valid']}")
    if issues:
        print(f"\n  {len(issues)} outstanding issue(s):")
        print(gherkin.format_issues(issues, limit=25))


def _write_report(report: dict, out_dir: Path) -> None:
    run_dir = config.RUNS_DIR / llm.run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "spec-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    # A copy beside the specification itself, so a features directory carries
    # its own provenance when it is copied elsewhere or handed to another model.
    (out_dir / "SPEC-REPORT.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n  specification report: {run_dir / 'spec-report.json'}")


# ---------------------------------------------------------------- main -----
def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--brief", help="path to the brief (default: brief.md)")
    parser.add_argument("--out", help="where to write the specification "
                                      "(default: the features directory)")
    parser.add_argument("--model", help="override the model in config.py")
    parser.add_argument("--rounds", type=int, help="max repair rounds")
    parser.add_argument("--keep", action="store_true",
                        help="do not wipe the output directory first")
    parser.add_argument("--lint-only", action="store_true",
                        help="validate an existing specification and stop")
    args = parser.parse_args()

    brief_path = Path(args.brief).resolve() if args.brief else config.BRIEF_FILE
    out_dir = Path(args.out).resolve() if args.out else config.FEATURES_DIR

    try:
        if args.lint_only:
            report = lint_only(out_dir, brief_path)
        else:
            report = generate(brief_path, out_dir, args.model, args.rounds,
                              wipe=not args.keep)
    except llm.ModelUnavailable as exc:
        print(f"\n  the model could not be reached: {exc}")
        return 1
    except RuntimeError as exc:
        print(f"\n  {exc}")
        return 1

    return 0 if report["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
