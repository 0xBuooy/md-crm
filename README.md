# LLM CRM Wiki

A personal CRM that lives in your terminal. Drop notes about people you meet, and your AI agent compiles them into a structured, interlinked wiki.

Based on [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern.

## Quickstart

### New directory

```bash
git clone https://github.com/0xbuooy/md-crm ~/crm
cd ~/crm
claude
```

### Inside existing Obsidian vault

```bash
cd ~/your-vault
git clone https://github.com/0xbuooy/md-crm .md-crm-skill
mkdir -p .claude/skills/md-crm
cp .md-crm-skill/SKILL.md .claude/skills/md-crm/SKILL.md
cp .md-crm-skill/AGENTS.md ./AGENTS.md
cp -r .md-crm-skill/crm ./crm
```

Then edit `crm/_config.md` to point `raw_sources` at your note directories, such as `daily/` or `meetings/`.

## Configuration

The skill needs two paths: `wiki_path` (where the compiled wiki lives) and `raw_path` (where raw interaction notes are written and scanned).

### Hermes

`hermes skills install 0xbuooy/md-crm` prompts for both paths on first install and stores them in `~/.hermes/config.yaml` under `skills.config`. See the [Hermes skills docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) for changing them later.

### OpenClaw

Drop the skill into any OpenClaw skill-discovery path (`~/.agents/skills/md-crm/`, `~/.openclaw/skills/md-crm/`, or `<workspace>/skills/md-crm/`). Set paths in `~/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "md-crm": {
        "enabled": true,
        "config": {
          "wiki_path": "/path/to/your/wiki",
          "raw_path": "/path/to/your/notes"
        }
      }
    }
  }
}
```

### Other agents (Claude Code, Codex, OpenCode)

Either clone into `~/crm` and run the agent from there (the default layout), or set `wiki_path` / `raw_path` in `crm/_config.md` to point elsewhere. Empty values fall back to `./crm` and `.` (cwd) so existing `raw_sources` like `daily/` continue to resolve relative to the vault root.

## Usage

Open your agent and talk naturally:

**Ingest**: "I just had coffee with Jane Doe. She's a PM at Stripe, interested in AI agents for payments. She wants an intro to Marcus."

**Query**: "Who do I know at Stripe?" / "What did Marcus and I last discuss?" / "Who should I follow up with?"

**Lint**: "lint" - surfaces decaying relationships, stale threads, and missing pages.

## Local Testing

The e2e suite runs in Docker — no host install of Hermes or OpenClaw
required, just Docker and an API key.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
make docker-build        # first time
make test-docker         # both suites

# Interactive shell inside the agent image
make docker-shell-hermes
```

See `tests/e2e/README.md` for filters, fixture authoring, and the matcher
reference.

## How It Works

1. You describe interactions or point at existing notes
2. The agent compiles structured person/company wiki pages
3. Knowledge accumulates - queries hit compiled pages, not raw notes
4. Lint surfaces what needs attention

No database. No API. No dependencies. Just markdown.

## Works With

- Claude Code (`SKILL.md`)
- OpenAI Codex (`AGENTS.md`)
- OpenCode / Pi (`OPENCODE.md`)
- Any agent that reads markdown instruction files

## Obsidian

Point Obsidian at the directory containing `crm/` as a vault, or place it inside an existing vault. You get:

- Graph view of your relationship network
- Backlinks between people, companies, and notes
- Full-text search across compiled pages
- Daily notes linking naturally to CRM entries

## License

MIT
