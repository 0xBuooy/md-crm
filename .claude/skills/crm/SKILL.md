---
name: crm
description: Maintain a personal CRM as interlinked markdown files — ingest interactions, query relationships, lint relationship health
metadata:
  hermes:
    config:
      - key: wiki_path
        description: Directory containing the compiled CRM wiki (people/, companies/, interactions/, schema/, index.md, _config.md)
        default: "~/crm"
        prompt: Where should your CRM wiki live?
      - key: raw_path
        description: Directory for raw interaction notes the agent scans during ingest
        default: "~/crm/raw"
        prompt: Where are your raw notes (daily journals, meeting notes)?
---
# Personal CRM Wiki

You maintain a personal CRM as interlinked markdown files.
Raw interaction notes are compiled into structured wiki pages
that accumulate knowledge over time.

## Setup

On first use, if `${wiki_path}` does not exist, create this
structure:

```text
${wiki_path}/
  _config.md          (copy default config)
  index.md            (empty index template)
  people/
  companies/
  interactions/
    log.md            (empty log with header)
  schema/
    person.md         (person template)
    company.md        (company template)
```

Never create or modify files outside of `${wiki_path}` unless
writing a new raw note to a configured `raw_sources` directory
(resolved relative to `${raw_path}`).

## Configuration

Resolve `wiki_path` and `raw_path` at the start of every operation
in this priority order:

1. Hermes context — values injected from `~/.hermes/config.yaml`
   under `skills.config.wiki_path` and `skills.config.raw_path`.
   Takes precedence when present.
2. OpenClaw config — read `~/.openclaw/openclaw.json` and use
   `skills.entries.crm.config.wiki_path` and
   `skills.entries.crm.config.raw_path` if set.
3. `_config.md` override — read `./crm/_config.md` frontmatter;
   if `wiki_path` or `raw_path` keys are non-empty they override
   layer 4. If `wiki_path` points elsewhere, re-read the real
   config from `${wiki_path}/_config.md`. Escape hatch for agents
   without a native config system (Claude Code, Codex).
4. Defaults — `wiki_path = ./crm`, `raw_path = .` relative to
   cwd. This preserves vault-root semantics: `raw_sources:
   ["daily/"]` resolves to `./daily/`.

Then read `${wiki_path}/_config.md` for behavior settings:
raw_sources (paths resolved relative to `${raw_path}`), exclude
paths, decay thresholds, stale_thread_days, and default_strength.

## Operations

You have exactly three operations: ingest, query, lint.

### Ingest

Trigger: "ingest [file]", "I just met...", "add contact",
"log interaction", or any message describing a new interaction.

Steps:
1. Resolve input (file path, freeform text, or directory scan)
2. If freeform text, save as a new `.md` file in the first
   raw_sources directory:
   `${raw_path}/{raw_sources[0]}/{YYYY-MM-DD}-{slug}.md`
3. Extract: people (name, role, company), companies, dates,
   commitments (who → what → by when), topics, tags,
   relationship signals (intro source, warmth)
4. For each person:
   - Existing page: read, merge new info, update last_contact,
     append interaction to history, update open_threads,
     increment interaction_count. FLAG contradictions with
     `> [!warning]` callouts - never silently overwrite.
   - New person: create from `${wiki_path}/schema/person.md` template
5. Update/create company pages
6. Prepend entry to `${wiki_path}/interactions/log.md`
7. Regenerate `${wiki_path}/index.md`
8. Report: created, updated, contradictions, new threads

Idempotency: check for duplicate interactions by date +
participants before appending.

### Query

Trigger: any question about contacts, relationships, network.

Steps:
1. Read `${wiki_path}/index.md` -> find relevant pages
2. Read those pages
3. Synthesize answer from compiled wiki pages (not raw sources)
4. Use `[[wiki-links]]` in your answer
5. Offer to create pages for any mentioned-but-missing entities

Query is read-only. Never modify files during a query.

### Lint

Trigger: "lint", "crm health", "audit", "what needs attention"

Check for:
1. Decaying relationships (last_contact exceeds decay threshold
   for current strength level - thresholds from `_config.md`)
2. Stale open_threads (no activity past `stale_thread_days`)
3. Orphan pages (no inbound wiki-links)
4. Broken links (wiki-links to non-existent files)
5. Unresolved contradictions (`> [!warning]` callouts)
6. Generate follow-up queue sorted by priority:
   relationship_strength (desc) × days_since_contact (desc)

Report findings grouped by category. Do NOT auto-modify pages.
Update `${wiki_path}/index.md` stats and last lint date.

## Formatting Rules

- Frontmatter: YAML, follows schema templates exactly
- Wiki-links: use `[[people/slug]]` and `[[companies/slug]]` format
- Dates: `YYYY-MM-DD` everywhere
- Slugs: lowercase, hyphenated (`jane-doe`, `acme-corp`)
- Interaction history: reverse chronological (newest first)
- Interaction log: reverse chronological (newest first)
- Callouts: use Obsidian-compatible `> [!type]` syntax
- Line width: no hard wrapping, let the editor handle it

## Principles

1. The wiki is compiled knowledge. Queries hit the wiki,
   not raw sources.
2. Every person page should answer: "If I'm about to message
   this person, what do I need to remember?"
3. Key Context section = what matters to THEM, not your agenda.
4. Contradiction is signal, not error. Surface it, don't hide it.
5. Keep open_threads current. Close or escalate, don't let them rot.
6. Relationship strength decays. Lint surfaces this.
7. Never modify files outside `${wiki_path}` without explicit user request.
8. When in doubt, ask the user rather than guessing.
