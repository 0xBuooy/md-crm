# md-crm e2e tests

Real-agent smoke tests that exercise the `md-crm` skill through the Hermes and
OpenClaw CLIs. LLM output is non-deterministic, so assertions focus on the
filesystem contract (frontmatter keys, slugs, cross-links, read-only
semantics of `query`) rather than on exact response prose.

## Layout

```text
tests/e2e/
  fixtures/transcript.yaml   structured input prompts + expected invariants
  lib/validate.py            YAML-frontmatter + body matcher
  lib/run_transcript.py      drives an agent CLI through the transcript
  hermes/run.sh              Hermes wrapper (config, install, run)
  openclaw/run.sh            OpenClaw wrapper (config, install, run)
```

## Running

Requires `python3` with `pyyaml`, the agent CLI on PATH, and an API key for
whatever provider the agent is configured to use.

```bash
pip install pyyaml

# Hermes
./tests/e2e/hermes/run.sh

# OpenClaw
./tests/e2e/openclaw/run.sh
```

Both wrappers create an isolated temp dir, point the agent's config at it,
install the skill from the current checkout, and run `lib/run_transcript.py`
against `fixtures/transcript.yaml`. No user state is modified.

If your build of Hermes or OpenClaw uses different flags for non-interactive
one-shot mode, override the command:

```bash
HERMES_AGENT_CMD="hermes ask --skill md-crm" ./tests/e2e/hermes/run.sh
OPENCLAW_AGENT_CMD="openclaw exec --skill md-crm" ./tests/e2e/openclaw/run.sh
```

The runner pipes each step's prompt on stdin and expects the agent's final
response on stdout.

## Writing new steps

Each entry in `fixtures/transcript.yaml` has the shape:

```yaml
- id: short-identifier
  description: human-readable intent
  input: |
    the prompt fed to the agent
  expect:
    response_contains: "...substring..."      # or response_any_of: [...]
    files:
      - path: "people/jane-doe.md"            # relative to wiki_path
        frontmatter:
          slug: { equals: "jane-doe" }
          company: { contains: "Stripe" }
        body_any_of: ["Key Context"]
    no_new_files: true                        # for read-only steps
    no_modified_files: true
    no_new_people: true
    no_new_companies: true
```

Matchers for frontmatter values and response checks:

| form                     | meaning                                |
|--------------------------|----------------------------------------|
| `"stripe"`               | case-insensitive substring             |
| `{ equals: "jane-doe" }` | exact string                           |
| `{ contains: "Plaid" }`  | case-insensitive substring             |
| `{ regex: "^[1-9]" }`    | regex search                           |
| `{ any_of: [...] }`      | any child matcher matches              |

## Why not assert exact prose?

The skill's contract lives in the markdown it produces, not in the agent's
natural-language reply. Asserting on prose would make the suite flaky across
model revisions without catching real regressions. Prose checks are kept as
soft `response_any_of` assertions to confirm the agent engaged at all.
