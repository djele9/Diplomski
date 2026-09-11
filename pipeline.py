#!/usr/bin/env python3
"""
pipeline.py — generate a full application from a Gherkin specification.

    python3 pipeline.py                  # backend, then frontend, with repair
    python3 pipeline.py --backend        # backend only
    python3 pipeline.py --frontend       # frontend only (needs a backend on disk)
    python3 pipeline.py --keep           # do not wipe app/ first
    python3 pipeline.py --no-repair      # generate without the compile loop
    python3 pipeline.py --no-install     # skip npm install
    python3 pipeline.py --model qwen3-coder:30b

What changed from the original driver, and why:

  * Stages run in dependency order, and the compiler configuration is written
    FIRST rather than last, so no file is generated without knowing the module
    system it will be compiled under.
  * Components are generated one feature area at a time. Asking for every screen
    in a single response is the most common cause of truncation.
  * The front end is given the backend's real routes, extracted from the
    generated routers, so it cannot invent URLs that do not exist.
  * Everything compiles before the run is called finished, with a bounded
    repair loop feeding compiler errors back.
  * Every prompt, response and timing is written under runs/, which is what
    lets the same script serve as the experiment driver for the thesis rather
    than only as a code generator.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import config
import context
import llm
import prompts_backend as pb
import prompts_frontend as pf
import repair


# ------------------------------------------------------------- helpers -----
def banner(text: str) -> None:
    print(f"\n{'=' * 72}\n  {text}\n{'=' * 72}")


def feature_areas() -> list[str]:
    """
    Split the specification into areas, for per-area component generation.

    Domain-agnostic by construction: a subdirectory under features/ is an area,
    and loose .feature files at the top level each become their own. Nothing
    here knows what the application is about, which is what lets the same
    pipeline run against a different specification unchanged.
    """
    areas: list[str] = []
    for child in sorted(config.FEATURES_DIR.iterdir()):
        if child.is_dir() and any(child.rglob("*.feature")):
            areas.append(child.name)
    if not areas:
        areas = [p.stem for p in sorted(config.FEATURES_DIR.glob("*.feature"))] #Stem is filename without extension
    return areas


# ------------------------------------------------------------- backend -----
BACKEND_STAGES = [
    # (name, prompt builder, minimum files expected)
    ("backend-1-scaffold",     pb.scaffold,    6),
    ("backend-2-models",       pb.models,      1),
    ("backend-3-middlewares",  pb.middlewares, 3),
    ("backend-4-services",     pb.services,    1),
    ("backend-5-controllers",  pb.controllers, 1),
    ("backend-6-routers",      pb.routers,     1),
    ("backend-7-server",       pb.server,      2),
]


def build_backend(spec: str) -> None:
    banner("BACKEND")
    print("  order: scaffold -> models -> middlewares -> services -> "
          "controllers -> routers -> server")
    for name, builder, minimum in BACKEND_STAGES:
        llm.call(name, builder(spec), expect_files=minimum)

    print("\n  extracted HTTP surface:")
    print(context.extract_api_surface())


# ------------------------------------------------------------ frontend -----
def build_frontend(spec: str) -> None:
    banner("FRONTEND")
    surface = context.extract_api_surface()
    if "not generated yet" in surface or "no routes could be extracted" in surface:
        print("  WARNING: no backend routes could be read.")
        print("  The front end will be generated against guessed URLs, which is")
        print("  exactly the failure this pipeline exists to prevent.")
        print("  Generate the backend first, or check that routers use")
        print("  router.<method>('/path', ...) and are mounted with app.use().")

    llm.call("frontend-1-scaffold", pf.scaffold(spec), expect_files=6)
    llm.call("frontend-2-models",   pf.models(spec),   expect_files=1)
    llm.call("frontend-3-services", pf.services(spec), expect_files=1)
    llm.call("frontend-4-guards",   pf.guards(spec),   expect_files=3)

    areas = feature_areas()
    print(f"\n  generating components for {len(areas)} area(s): {', '.join(areas)}")
    done: list[str] = []
    for index, area in enumerate(areas, start=1):
        llm.call(
            f"frontend-5-components-{area}",
            pf.components(spec, area=area, areas_done="\n".join(f"  - {a}" for a in done)),
            expect_files=3,   # a component is .ts + .html + .css
        )
        done.append(area)
        print(f"  area {index}/{len(areas)} done")

    llm.call("frontend-6-app", pf.app_shell(spec), expect_files=5)


# ---------------------------------------------------------------- main -----
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backend", action="store_true", help="backend only")
    parser.add_argument("--frontend", action="store_true", help="frontend only")
    parser.add_argument("--keep", action="store_true", help="do not wipe app/ first")
    parser.add_argument("--no-repair", action="store_true", help="skip the compile loop")
    parser.add_argument("--no-install", action="store_true", help="skip npm install")
    parser.add_argument("--model", help="override the model in config.py")
    parser.add_argument("--repair-rounds", type=int, help="override MAX_REPAIR_ROUNDS")
    args = parser.parse_args()

    if args.model:
        config.MODEL = args.model
    if args.repair_rounds is not None:
        config.MAX_REPAIR_ROUNDS = args.repair_rounds

    do_backend = args.backend or not args.frontend
    do_frontend = args.frontend or not args.backend

    banner(f"BDD CODE GENERATION  —  {config.MODEL}")
    print(f"  run id     {llm.run_id()}")
    print(f"  features   {config.FEATURES_DIR}")
    print(f"  output     {config.OUTPUT_DIR}")
    print(f"  num_ctx    {config.OPTIONS['num_ctx']:,}     "
          f"num_predict {config.OPTIONS['num_predict']:,}")
    print()

    spec = context.load_specification()
    sizes = context.count_scenarios(spec)
    print(f"  scenarios: {sizes['scenarios']} plain, "
          f"{sizes['scenario_outlines']} outlines")

    if not args.keep:
        if config.OUTPUT_DIR.exists():
            shutil.rmtree(config.OUTPUT_DIR)
        config.OUTPUT_DIR.mkdir(parents=True)
        print(f"  wiped and recreated {config.OUTPUT_DIR}")
    else:
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  keeping existing contents of {config.OUTPUT_DIR}")

    started = time.perf_counter()
    results: dict[str, object] = {}

    try:
        if do_backend:
            build_backend(spec)
            if not args.no_install:
                repair.install(config.BACKEND_DIR)
            if not args.no_repair:
                result = repair.repair_loop("backend", spec)
                results["backend_compiles"] = result.ok
                results["backend_errors"] = result.error_count

        if do_frontend:
            build_frontend(spec)
            if not args.no_install:
                repair.install(config.FRONTEND_DIR)
            if not args.no_repair:
                result = repair.repair_loop("frontend", spec)
                results["frontend_compiles"] = result.ok
                results["frontend_errors"] = result.error_count

    except RuntimeError as exc:
        banner("STOPPED")
        print(f"  {exc}\n")
        print(f"  Prompts and raw responses: {config.RUNS_DIR / llm.run_id()}") #Where prompts and responses are saved
        print(f"  Partial output kept in:    {config.OUTPUT_DIR}")
        print(f"  Re-run one stage with --keep once you have adjusted the cause.")
        return 1

    # ---- summary ----------------------------------------------------------
    elapsed = time.perf_counter() - started
    banner("DONE")
    print(f"  {llm.summary()}")
    print(f"  total wall time: {elapsed/60:.1f} min") #prikazi jednu decimalu
    for key, value in results.items():
        print(f"  {key}: {value}")

    manifest = {
        "run_id": llm.run_id(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "model": config.MODEL,
        "options": config.OPTIONS,
        "specification": sizes,
        "features_dir": str(config.FEATURES_DIR),
        "results": results,
        "wall_seconds": round(elapsed, 1),
    }
    run_dir = config.RUNS_DIR / llm.run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\n  run record: {run_dir}")
    print(f"  generated:  {config.OUTPUT_DIR}")
    print("\n  Next:")
    print(f"    cd {config.BACKEND_DIR}  && npm run dev")
    print(f"    cd {config.FRONTEND_DIR} && npm start")

    both_ok = all(v for k, v in results.items() if k.endswith("_compiles"))
    return 0 if both_ok or args.no_repair else 2


if __name__ == "__main__":
    sys.exit(main())
