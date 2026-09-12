#!/usr/bin/env python3
"""
pipeline.py — generate a full application from a Gherkin specification.

    python3 pipeline.py --list                      # what projects exist
    python3 pipeline.py --project library           # code from an existing spec
    python3 pipeline.py --project library --generate-spec   # spec first, then code
    python3 pipeline.py --backend                   # backend only
    python3 pipeline.py --frontend                  # frontend only (keeps backend)
    python3 pipeline.py --keep                      # do not wipe first
    python3 pipeline.py --no-repair --no-install
    python3 pipeline.py --model llama3.1:8b
    python3 pipeline.py --profile authentication,search --no-profile uploads

## Projects

A project is one application domain: one brief, one generated specification, one
generated application, kept side by side with the others.

    briefs/<project>.md
    specs/<project>/<area>/*.feature
    apps/<project>/{backend,frontend}

Nothing in this pipeline knows what any project is about. The brief is the only
domain-specific input; the specification is derived from it, the profile is
derived from the specification, and the prompts are assembled from the profile.

## The profile

Before generating any code the pipeline reads the specification and works out
which cross-cutting concerns the domain actually has — accounts, roles, uploads,
search, scheduling, money, email, bulk import, ratings, state machines — and the
prompts are built from that. A catalogue with no accounts is never asked for an
authentication middleware or a route guard; a domain with no dates never reads
the half-open-interval rule.

This matters for the comparison and not only for tidiness. Asking a model for
files the domain does not need produces them, then scores the stage as failed
for returning fewer files than a manifest written for somebody else's
application. The profile is printed at the start of every run and recorded in
the manifest: two models given different profiles were given different tasks.

## Three conditions worth naming

    pipeline.py --model M
        M writes code from a specification you fixed. Isolates CODE generation.

    pipeline.py --generate-spec --model M
        M specifies zero-shot, then codes from its own specification.
        End-to-end, and confounded on purpose: a model that specifies thinly
        gets an easy coding task. Report the specification metrics alongside.

    pipeline.py --generate-spec --spec-model S --model M
        S specifies, M codes. Fix S across every M and you are back to
        isolating code generation from a machine-written specification.

## On failure

A failing stage does not end the run. It is recorded and the pipeline
continues. The models worth studying are the small ones, and those are exactly
the ones that truncate at stage four; a run that aborts there produces no data
about the model, only about the abort. The manifest is written whatever
happens, including on a crash — failures are the measurement.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import config
import context
import gherkin
import llm
import domain_profile as profiling
import prompts_backend as pb
import prompts_frontend as pf
import repair
import spec_generation


# ------------------------------------------------------------- helpers -----
def banner(text: str) -> None:
    print(f"\n{'=' * 72}\n  {text}\n{'=' * 72}")


def feature_areas() -> list[str]:
    """
    Split the specification into areas, for per-area component generation.

    Domain-agnostic by construction: a subdirectory under the specification root
    is an area, and loose .feature files at the top level each become their own.
    Nothing here knows what the application is about, which is what lets the
    same pipeline run against a different specification unchanged.
    """
    areas: list[str] = []
    for child in sorted(config.FEATURES_DIR.iterdir()):
        if child.is_dir() and any(child.rglob("*.feature")):
            areas.append(child.name)
    if not areas:
        areas = [p.stem for p in sorted(config.FEATURES_DIR.glob("*.feature"))]
    return areas


def resolve_profile(args) -> profiling.Profile:
    """Detect the profile from the specification, then apply any overrides."""
    enable = [s.strip() for s in (args.profile or "").split(",") if s.strip()]
    disable = [s.strip() for s in (args.no_profile or "").split(",") if s.strip()]

    if args.only_profile:
        prof = profiling.from_names(
            [s.strip() for s in args.only_profile.split(",") if s.strip()])
        features = gherkin.load_features(config.FEATURES_DIR)
        detected = profiling.detect(features)
        prof.areas, prof.scenarios = detected.areas, detected.scenarios
        prof.entities_hint = detected.entities_hint
    else:
        features = gherkin.load_features(config.FEATURES_DIR)
        prof = profiling.detect(features)

    return profiling.apply_overrides(prof, enable, disable)


# --------------------------------------------------------------- stages ----
def build_backend(spec: str, prof: profiling.Profile, failures: list[str]) -> None:
    banner("BACKEND")
    print("  order: " + " -> ".join(s.name.split("-", 2)[-1] for s in pb.STAGES))
    for stage in pb.STAGES:
        record = llm.call(stage.name, stage.build(spec, prof),
                          expect_files=stage.minimum(prof),
                          expected_root="backend/")
        if not record.ok:
            failures.append(f"{record.label()}: {record.failure}")

    surface = context.extract_api_surface()
    print("\n  extracted HTTP surface:")
    print(surface)
    if not context.surface_is_usable(surface):
        failures.append("backend: no HTTP routes could be extracted from the routers")


def build_frontend(spec: str, prof: profiling.Profile, failures: list[str]) -> None:
    banner("FRONTEND")
    surface = context.extract_api_surface()
    if not context.surface_is_usable(surface):
        print("  WARNING: no backend routes could be read.")
        print("  The front end will be generated against guessed URLs, which is")
        print("  exactly the failure this pipeline exists to prevent.")
        print("  Generate the backend first, or check that routers use")
        print("  router.<method>('/path', ...) and are mounted with app.use().")
        failures.append("frontend: generated without a usable backend HTTP surface")

    for stage in pf.STAGES:
        record = llm.call(stage.name, stage.build(spec, prof),
                          expect_files=stage.minimum(prof),
                          expected_root="frontend/")
        if not record.ok:
            failures.append(f"{record.label()}: {record.failure}")

    areas = feature_areas()
    print(f"\n  generating components for {len(areas)} area(s): {', '.join(areas)}")
    done: list[str] = []
    for index, area in enumerate(areas, start=1):
        record = llm.call(
            f"frontend-5-components-{area}",
            pf.components(spec, prof, area=area,
                          areas_done="\n".join(f"  - {a}" for a in done)),
            expect_files=3,   # a component is .ts + .html + .css
            expected_root="frontend/",
        )
        if not record.ok:
            failures.append(f"{record.label()}: {record.failure}")
        done.append(area)
        print(f"  area {index}/{len(areas)} done")

    final = pf.FINAL_STAGE
    record = llm.call(final.name, final.build(spec, prof),
                      expect_files=final.minimum(prof), expected_root="frontend/")
    if not record.ok:
        failures.append(f"{record.label()}: {record.failure}")


# ---------------------------------------------------------------- main -----
def wipe(target: Path, label: str) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    print(f"  wiped and recreated {label}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", help="which brief/specification to use")
    parser.add_argument("--list", action="store_true",
                        help="list the available projects and stop")
    parser.add_argument("--backend", action="store_true", help="backend only")
    parser.add_argument("--frontend", action="store_true", help="frontend only")
    parser.add_argument("--keep", action="store_true", help="do not wipe first")
    parser.add_argument("--no-repair", action="store_true", help="skip the compile loop")
    parser.add_argument("--no-install", action="store_true", help="skip npm install")
    parser.add_argument("--model", help="override the model in config.py")
    parser.add_argument("--features", help="override the specification directory")
    parser.add_argument("--repair-rounds", type=int, help="override MAX_REPAIR_ROUNDS")
    parser.add_argument("--generate-spec", action="store_true",
                        help="write the Gherkin specification first, zero-shot")
    parser.add_argument("--spec-model",
                        help="model for the specification stage (default: --model)")
    parser.add_argument("--spec-rounds", type=int,
                        help="override MAX_SPEC_REPAIR_ROUNDS")
    parser.add_argument("--brief", help="path to the brief, overriding --project")
    parser.add_argument("--spec-only", action="store_true",
                        help="generate the specification and stop")
    parser.add_argument("--profile", metavar="A,B",
                        help="force these concerns on, whatever the spec says")
    parser.add_argument("--no-profile", metavar="A,B",
                        help="force these concerns off")
    parser.add_argument("--only-profile", metavar="A,B",
                        help="use exactly these concerns; skip detection entirely")
    args = parser.parse_args()

    if args.list:
        projects = config.available_projects()
        print("Projects (briefs/*.md):")
        for name in projects:
            spec_dir = config.SPECS_ROOT / name
            count = len(list(spec_dir.rglob("*.feature"))) if spec_dir.exists() else 0
            print(f"  {name:<24} {count} feature file(s) generated"
                  if count else f"  {name:<24} no specification generated yet")
        if not projects:
            print(f"  (none — add one to {config.BRIEFS_DIR})")
        print(f"\nKnown profile concerns: {', '.join(profiling.ALL_CONCERNS)}")
        return 0

    if args.project:
        config.set_project(args.project)
    if args.brief:
        config.BRIEF_FILE = Path(args.brief).resolve()
    if args.features:
        config.FEATURES_DIR = Path(args.features).resolve()
    if args.model:
        config.MODEL = args.model
    if args.repair_rounds is not None:
        config.MAX_REPAIR_ROUNDS = args.repair_rounds

    generate_spec = args.generate_spec or args.spec_only
    do_backend = (args.backend or not args.frontend) and not args.spec_only
    do_frontend = (args.frontend or not args.backend) and not args.spec_only
    spec_model = args.spec_model or config.MODEL

    banner(f"BDD CODE GENERATION  —  {config.PROJECT}  —  {config.MODEL}")
    print(f"  run id     {llm.run_id()}")
    print(f"  brief      {config.BRIEF_FILE}")
    print(f"  spec       {config.FEATURES_DIR}")
    print(f"  output     {config.OUTPUT_DIR}")
    print(f"  building   {'spec' if generate_spec else ''}"
          f"{' + ' if generate_spec and (do_backend or do_frontend) else ''}"
          f"{'backend' if do_backend else ''}"
          f"{' + ' if do_backend and do_frontend else ''}"
          f"{'frontend' if do_frontend else ''}")
    if generate_spec and spec_model != config.MODEL:
        print(f"  spec model {spec_model}   (code model {config.MODEL})")
    print(f"  num_ctx    {config.OPTIONS['num_ctx']:,}     "
          f"num_predict {config.OPTIONS['num_predict']:,}")
    print()

    # ---- stage zero: the model writes the specification -------------------
    spec_report: dict = {}
    if generate_spec:
        try:
            spec_report = spec_generation.generate(
                brief_path=config.BRIEF_FILE,
                out_dir=config.FEATURES_DIR,
                model=spec_model,
                max_rounds=args.spec_rounds,
                wipe=not args.keep,
            )
        except llm.ModelUnavailable as exc:
            banner("STOPPED — the model could not be reached")
            print(f"  {exc}")
            return 1
        except RuntimeError as exc:
            banner("STOPPED — the specification stage could not start")
            print(f"  {exc}")
            return 1

        if not spec_report.get("metrics", {}).get("scenarios_total"):
            banner("STOPPED — no usable specification was produced")
            print("  There is nothing to generate code from. The raw response is")
            print(f"  under {config.RUNS_DIR / llm.run_id()}.")
            return 2

        if args.spec_only:
            print("\n  --spec-only: stopping before code generation.")
            return 0 if spec_report.get("valid") else 2

        if not spec_report.get("valid"):
            print("\n  NOTE: the specification still has validation issues. "
                  "Continuing, because\n  code generated from a flawed "
                  "specification is a result, not an accident.")

    if not config.FEATURES_DIR.exists() or not any(config.FEATURES_DIR.rglob("*.feature")):
        banner("STOPPED — no specification")
        print(f"  Nothing under {config.FEATURES_DIR}.")
        print(f"  Generate one:  python3 pipeline.py --project {config.PROJECT} "
              f"--spec-only")
        return 1

    spec = context.load_specification()
    sizes = context.count_scenarios(spec)
    print(f"  scenarios: {sizes['scenarios']} plain, "
          f"{sizes['scenario_outlines']} outlines, "
          f"{sizes['examples_rows']} example rows")

    # ---- what kind of application is this? --------------------------------
    try:
        prof = resolve_profile(args)
    except ValueError as exc:
        print(f"\n  {exc}")
        return 1

    banner("DOMAIN PROFILE")
    print(f"  source: {prof.source}")
    print(prof.describe())
    print(f"\n  areas {prof.areas}, scenarios {prof.scenarios}, "
          f"entity estimate {prof.entities_hint}")
    off = [c for c in profiling.ALL_CONCERNS if not getattr(prof, c)]
    if off:
        print(f"  not present: {', '.join(off)}")
    print("\n  The prompts below are assembled from this. If a line above is")
    print("  wrong, correct it with --profile / --no-profile and say so when")
    print("  you report the run.")

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.keep:
        print(f"\n  keeping existing contents of {config.OUTPUT_DIR}")
    else:
        # Wipe only the side being built. Wiping all of the output directory
        # would mean `--frontend` deleting the backend whose routes it needs.
        print()
        if do_backend:
            wipe(config.BACKEND_DIR, f"apps/{config.PROJECT}/backend")
        if do_frontend:
            wipe(config.FRONTEND_DIR, f"apps/{config.PROJECT}/frontend")

    started = time.perf_counter()
    results: dict[str, object] = {}
    failures: list[str] = []
    crash: str = ""

    try:
        if do_backend:
            build_backend(spec, prof, failures)
            if not args.no_install:
                installed = repair.install(config.BACKEND_DIR)
                results["backend_installed"] = installed.ok
                if not installed.ok:
                    failures.append(f"backend install: {installed.detail}")
            if not args.no_repair:
                result = repair.repair_loop("backend", spec)
                results["backend_compiles"] = result.ok
                results["backend_errors"] = result.error_count
                results["backend_check_blocked"] = result.blocked()

        if do_frontend:
            build_frontend(spec, prof, failures)
            if not args.no_install:
                installed = repair.install(config.FRONTEND_DIR)
                results["frontend_installed"] = installed.ok
                if not installed.ok:
                    failures.append(f"frontend install: {installed.detail}")
            if not args.no_repair:
                result = repair.repair_loop("frontend", spec)
                results["frontend_compiles"] = result.ok
                results["frontend_errors"] = result.error_count
                results["frontend_check_blocked"] = result.blocked()

    except llm.ModelUnavailable as exc:
        crash = str(exc)
        banner("STOPPED — the model could not be reached")
        print(f"  {exc}")
        print("  This is an infrastructure failure, not a result. Check that")
        print(f"  ollama is running and that `{config.MODEL}` has been pulled.")
    except KeyboardInterrupt:
        crash = "interrupted by the user"
        banner("INTERRUPTED")
    except Exception:                                  # noqa: BLE001 — see below
        # Anything unexpected is still written to the manifest before it is
        # reported. A run that dies without a record is a run that has to be
        # repeated, and these runs cost an hour each.
        crash = traceback.format_exc(limit=6)
        banner("CRASHED")
        print(crash)

    # ---- record, always ---------------------------------------------------
    elapsed = time.perf_counter() - started
    stage_records = llm.records()
    manifest = {
        "run_id": llm.run_id(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "project": config.PROJECT,
        "model": config.MODEL,
        "options": config.OPTIONS,
        "specification": sizes,
        "features_dir": str(config.FEATURES_DIR),
        "spec_sha256_16": context.spec_fingerprint(spec),
        # Provenance of the specification. Without this a manifest cannot say
        # whether the code was written from a human specification or from one
        # the model wrote itself, which is the difference between two entirely
        # different experiments.
        "spec_source": "generated" if generate_spec else "provided",
        "spec_model": spec_model if generate_spec else None,
        "spec_report": spec_report or None,
        # The profile decided which prompts were sent. Two runs with different
        # profiles are not comparable, so it is recorded rather than inferred.
        "profile": prof.to_dict(),
        "built": {"spec": generate_spec, "backend": do_backend,
                  "frontend": do_frontend},
        "flags": {
            "keep": args.keep, "no_repair": args.no_repair,
            "no_install": args.no_install,
        },
        "results": results,
        "stages_total": len(stage_records),
        "stages_failed": [r.label() for r in stage_records if not r.ok],
        "failures": failures,
        "crashed": bool(crash),
        "crash": crash,
        "wall_seconds": round(elapsed, 1),
    }
    run_dir = config.RUNS_DIR / llm.run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")

    # ---- summary ----------------------------------------------------------
    banner("DONE" if not crash else "DONE (incomplete)")
    print(f"  project: {config.PROJECT}   profile: "
          f"{', '.join(prof.enabled()) or 'plain CRUD'}")
    print(f"  {llm.summary()}")
    print(f"  total wall time: {elapsed/60:.1f} min")
    if spec_report:
        spec_metrics = spec_report.get("metrics", {})
        print(f"  specification: {spec_metrics.get('scenarios_total', 0)} scenarios, "
              f"{spec_metrics.get('negative_share', 0):.0%} negative, "
              f"coverage {spec_metrics.get('capability_coverage', 0):.0%}, "
              f"valid={spec_report.get('valid')}")
    for key, value in results.items():
        print(f"  {key}: {value}")
    if failures:
        print(f"\n  {len(failures)} problem(s) recorded:")
        for line in failures:
            print(f"    - {line}")

    print(f"\n  run record: {run_dir}")
    print(f"  generated:  {config.OUTPUT_DIR}")
    if not crash and not failures:
        print("\n  Next:")
        print(f"    cd {config.BACKEND_DIR}  && npm run dev")
        print(f"    cd {config.FRONTEND_DIR} && npm start")

    # ---- exit code --------------------------------------------------------
    # 0 the run completed and everything it produced is sound
    # 1 the run could not complete (model unreachable, crash, interrupt)
    # 2 the run completed but the output is not sound — a stage failed, or the
    #   generated code does not compile
    # 3 the compile check itself was blocked, so the result says nothing about
    #   the code and must not be reported as either a pass or a failure
    #
    # The last two are the distinction that matters for the write-up. "Did not
    # compile" is a fact about the model; "could not be checked" is a fact about
    # the toolchain, and putting the second in a results table as though it were
    # the first is how a comparison ends up measuring a missing npx.
    if crash:
        return 1
    if any(v for k, v in results.items() if k.endswith("_check_blocked")):
        return 3
    compiles = [v for k, v in results.items() if k.endswith("_compiles")]
    if compiles and not all(compiles):
        return 2
    if failures:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
