# md-crm e2e tests

Real-agent smoke tests that drive the `md-crm` skill through Hermes and
OpenClaw. Each scenario is a small YAML transcript of prompts + expected
filesystem invariants. LLM output is non-deterministic, so assertions focus
on the markdown the skill produces — not on the agent's prose.

## Layout

```text
tests/e2e/
  fixtures/                  one YAML per scenario (22 and growing)
    01-basic-coffee-chat.yaml
    02-email-captured.yaml
    ...
  lib/validate.py            YAML-frontmatter + file/body matcher
  lib/run_transcript.py      runs one transcript or a whole dir
  hermes/run.sh              Hermes wrapper (config, install, run)
  openclaw/run.sh            OpenClaw wrapper (config, install, run)
```

## Scenarios

| #  | name                       | what it exercises                               |
|----|----------------------------|-------------------------------------------------|
| 01 | basic-coffee-chat          | minimal single-person ingest                    |
| 02 | email-captured             | email address preserved somewhere on the page   |
| 03 | phone-captured             | phone number preserved verbatim                 |
| 04 | full-contact-details       | email + phone + LinkedIn + location             |
| 05 | multi-person-single-note   | one note → three people pages                   |
| 06 | introduction-chain         | intros produce network backlinks                |
| 07 | repeat-interaction         | interaction_count increments across ingests    |
| 08 | duplicate-ingest-idempotent| same note twice → no duplicate log entry       |
| 09 | company-change             | job change flagged, not silently overwritten    |
| 10 | role-change                | promotion updates role, keeps company           |
| 11 | commitments-and-followups  | commitments become open_threads                 |
| 12 | query-by-company           | "who at Stripe?" returns everyone               |
| 13 | query-last-discussed       | returns most recent interaction topic           |
| 14 | query-readonly             | query must not touch the filesystem             |
| 15 | query-missing-entity       | unknown person → offer-to-create, no fabrication|
| 16 | lint-stale-thread          | old open thread → flagged stale                 |
| 17 | lint-decay                 | warm contact past 30d → flagged decaying        |
| 18 | lint-readonly              | lint doesn't modify person/company pages        |
| 19 | slug-normalization         | titles, hyphens, accents → clean slug           |
| 20 | contradiction-warning      | conflicting facts → `> [!warning]` callout      |
| 21 | tags-extracted             | topics in note populate tags array              |
| 22 | interaction-log-ordering   | global log stays reverse-chronological          |

## Running

Requires `python3` with `pyyaml`, the agent CLI on PATH, and API credentials
for whatever provider the agent is configured to use.

```bash
pip install pyyaml

# Hermes — runs all 22 transcripts
./tests/e2e/hermes/run.sh

# OpenClaw — runs all 22 transcripts
./tests/e2e/openclaw/run.sh

# Filter to a subset (matched against filenames)
E2E_FILTER=09-company ./tests/e2e/hermes/run.sh
E2E_FILTER=lint       ./tests/e2e/openclaw/run.sh
```

Each wrapper creates an isolated temp dir, points the agent's config at it,
installs the skill from the current checkout, and invokes the runner. The
runner wipes `wiki_path` and `raw_path` between transcripts so scenarios
don't contaminate each other. No user state is touched.

If your build uses different flags for one-shot / non-interactive mode:

```bash
HERMES_AGENT_CMD="hermes ask --skill md-crm" ./tests/e2e/hermes/run.sh
OPENCLAW_AGENT_CMD="openclaw exec --skill md-crm" ./tests/e2e/openclaw/run.sh
```

The runner pipes each step's prompt on stdin and expects the agent's final
response on stdout.

## Writing a new scenario

Drop a new YAML in `fixtures/`. One file per scenario; keep each focused on
a single behavior. Shape:

```yaml
name: short-identifier
description: one-line intent
steps:
  - id: step-name
    input: |
      the prompt fed to the agent
    expect:
      response_contains: "...substring..."
      response_any_of: [...]
      response_not_contains: [...]
      response_regex: "..."
      files:
        - path: "people/jane-doe.md"         # relative to wiki_path
          frontmatter:
            slug: { equals: "jane-doe" }
            company: { contains: "Stripe" }
          body_contains: "Key Context"
          body_any_of: [...]
          file_contains: [...]               # searches frontmatter+body
          file_any_of: [...]
          file_regex: "..."
          file_not_contains: [...]
      files_absent: ["people/ghost.md"]
      no_new_files: true
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

## Why fuzzy assertions?

The skill's contract lives in the markdown it produces, not in the agent's
natural-language reply. Asserting on prose would make the suite flaky across
model revisions without catching real regressions. Per-field matchers use
case-insensitive substring by default so minor phrasing changes (e.g. "head
of partnerships" vs. "Head of Partnerships") don't trip the suite, while
structural keys (slugs, schema fields, cross-links) are checked exactly.
