# BDD code generation — thesis pipeline

Generates a full web application from a Gherkin specification, generates the
Gherkin specification itself from a plain-language brief, and measures both — so
that several models can be compared at each step.

```
briefs/<project>.md  ──zero-shot──▶  specs/<project>/**.feature
   (the only human input)              (model, linted and scored)
                                              │
                                    detect the domain profile
                                              │
                                              ▼
                              apps/<project>/{backend,frontend}
                                    (model, compiled and repaired)
```

Nothing in the pipeline knows what any project is about. Swap the brief and the
whole chain follows.

## Install

```
pip install ollama
```

Node.js and npm must be on PATH for the compile stage.

## Run

```bash
python3 test_pipeline.py                    # 182 checks, no model needed
python3 pipeline.py --list                  # what projects exist

python3 pipeline.py --project library-lending --spec-only --model qwen3-coder:30b
python3 pipeline.py --project library-lending --generate-spec --model qwen3-coder:30b
python3 pipeline.py --project coworking-spaces --backend --model llama3.1:8b

python3 spec_generation.py --lint-only      # score a specification that exists
```

## Adding a domain

Copy `briefs/TEMPLATE.md` to `briefs/<name>.md`, write the brief, and run
`pipeline.py --project <name> --generate-spec`. Nothing else changes: no code,
no prompt, no configuration.

Three briefs ship, chosen to be different shapes rather than to be interesting:

| Project | Shape |
|---|---|
| `coworking-spaces` | accounts, roles, uploads, bookings, money, ratings |
| `library-lending` | accounts and roles, **no uploads**, loans and fines |
| `city-issue-reports` | **no accounts at all**, public reporting, uploads, search |

`city-issue-reports` earns its place: it is the one that fails loudly if the
pipeline has quietly grown an assumption that every application has a login.

## The domain profile

Before generating code, the pipeline reads the specification and works out which
cross-cutting concerns the domain actually has:

```
authentication  authorization  roles      uploads   search   pagination
scheduling      money          email      import_export      ratings
state_machine
```

Every prompt is assembled from that. A catalogue with no accounts is never asked
for an authentication middleware, a route guard or a token interceptor; a domain
with no dates never reads the half-open-interval rule; a domain with no money
never reads the minor-units rule. Prompts get shorter and more accurate at once,
which matters most for small models — context spent on advice about features the
domain does not have is context not spent on the specification.

This is a measurement concern, not tidiness. Ask a model for files the domain
does not need and it will produce them, and the stage is then scored as failed
for returning fewer files than a manifest written for somebody else's
application. **The profile is printed at the start of every run, with the phrase
that triggered each flag, and recorded in the manifest.** Two models given
different profiles were given different tasks.

Detection is keyword matching and errs generously — a false positive costs one
unused file, a false negative costs an application with no access control on a
specification that needed it. Override it when it is wrong:

```bash
--profile authentication,search      # force on
--no-profile uploads                 # force off
--only-profile search,money          # skip detection entirely
```

## The three conditions

| Command | What it isolates |
|---|---|
| `pipeline.py --model M` | **Code generation.** M writes code from a specification you fixed. The clean ranking. |
| `pipeline.py --generate-spec --model M` | **End to end.** M specifies, then codes from its own specification. Confounded on purpose. |
| `pipeline.py --generate-spec --spec-model S --model M` | **Code generation from machine-written input.** Fix S across every M. |

The second needs care: a model that writes a thin specification gets an easy
coding task and can outscore one that specified thoroughly and then struggled.
Always report the specification metrics beside the compile result.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Completed, and everything produced is sound |
| 1 | Could not complete — model unreachable, crash, interrupt |
| 2 | Completed, but a stage failed or the code does not compile |
| 3 | The compile check was **blocked** — says nothing about the code |

3 is separate from 2 deliberately. "Did not compile" is a fact about the model;
"could not be checked" is a fact about the toolchain, and putting the second in a
results table as though it were the first is how a comparison ends up measuring a
missing `npx`.

## What gets measured

**Specification** (`runs/<id>/spec-report.json`, also copied beside the spec):

- `capability_coverage` — of the capabilities the brief states, how many have a
  scenario. Padding does not move it.
- `negative_share` — fraction of scenarios exercising a refusal. Most real
  requirements are about what a system refuses.
- `step_reuse` — steps ÷ distinct steps, with quoted values and numbers treated
  as arguments. Saying "the member is signed in" five different ways is the most
  common flaw in machine-written Gherkin and makes automation five times the work.
- `first_attempt_valid` and `rounds_used` — unaided validity is a different claim
  from validity after being told what was wrong.

**Code** (`runs/<id>/{stages,manifest,*-compile}.json`): per-stage wall time,
tokens, throughput (with the measure named), truncation, placeholder markers,
rejected and repaired paths, trailing chatter, compile errors per file, repair
rounds, and the profile the run used.

## The zero-shot property

`prompts_spec.py` contains no worked example — no sample scenario, no Gherkin at
all. The notation is described in prose; the model's knowledge of it is the thing
under test. `test_spec_prompt_is_zero_shot` enforces this, because one exemplar
added later "to help the model" would silently turn the condition into one-shot
and every number collected under it would describe a different experiment than
the write-up claims.

The rules in that prompt are detailed — tag vocabulary, one area per directory,
every scenario mapped to a capability. Zero-shot permits that, and it is worth
stating plainly: what is measured is "can this model produce a usable
specification from instructions alone", not "does this model know what Gherkin
is". A few-shot variant carrying two or three exemplar scenarios, run against the
same models and briefs, is the natural comparison.

## Files

| File | Role |
|---|---|
| `briefs/*.md` | **The only hand-written input.** Numbered `C<n>:` capabilities. |
| `prompts_spec.py` | The zero-shot specification prompt, and its repair prompt |
| `spec_generation.py` | Stage zero: generate, validate, repair, report |
| `gherkin.py` | Gherkin parser, linter and specification metrics |
| `domain_profile.py` | Infers what the application needs from the specification |
| `config.py` | Every setting, and `set_project()` |
| `context.py` | What each prompt may see; extracts the backend's real routes |
| `prompts_backend.py` | Backend stages, assembled from the profile |
| `prompts_frontend.py` | Front-end stages, assembled from the profile |
| `llm.py` | Call the model, parse the answer, write files, record the run |
| `compilers.py` | Run tsc / ng build, parse every output format they emit |
| `repair.py` | Compile, feed errors back, bounded |
| `pipeline.py` | The driver |
| `test_pipeline.py` | Tests for the measuring instrument |

## Before collecting data

1. `python3 test_pipeline.py` — no model needed, takes a second.
2. `python3 pipeline.py --project city-issue-reports --spec-only --model <smallest>`
   — the specification stage is cheap and tells you immediately whether a model
   can follow a contract at all. Check the printed profile has no authentication.
3. `python3 pipeline.py --project coworking-spaces --backend --model <same>` for
   one green backend run before adding the front end.
4. Then repeat each condition N≥3 times per model. `seed: 42` and
   `temperature: 0.1` give near-determinism, not determinism — Ollama is not
   bit-reproducible across batch sizes — so report variance, not a single run.
