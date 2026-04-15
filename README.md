# LLM CRM Wiki

A personal CRM that lives in your terminal. Drop notes about people you meet, and your AI agent compiles them into a structured, interlinked wiki.

Based on [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern.

## Quickstart

### New directory

```bash
git clone https://github.com/0xbuooy/agent-crm ~/crm
cd ~/crm
claude
```

### Inside existing Obsidian vault

```bash
cd ~/your-vault
git clone https://github.com/0xbuooy/agent-crm .crm-skill
mkdir -p .claude/skills/crm
cp .crm-skill/SKILL.md .claude/skills/crm/SKILL.md
cp .crm-skill/AGENTS.md ./AGENTS.md
cp -r .crm-skill/crm ./crm
```

Then edit `crm/_config.md` to point `raw_sources` at your note directories, such as `daily/` or `meetings/`.

## Configuration

The skill needs two paths: `wiki_path` (where the compiled wiki lives) and `raw_path` (where raw interaction notes are written and scanned).

### Hermes

`hermes skills install 0xbuooy/agent-crm` prompts for both paths on first install and stores them in `~/.hermes/config.yaml` under `skills.config`. See the [Hermes skills docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) for changing them later.

### Other agents (Claude Code, Codex, OpenCode)

Either clone into `~/crm` and run the agent from there (the default layout), or set `wiki_path` / `raw_path` in `crm/_config.md` to point elsewhere. Empty values fall back to `./crm` and `./raw` relative to the current working directory.

## Usage

Open your agent and talk naturally:

**Ingest**: "I just had coffee with Jane Doe. She's a PM at Stripe, interested in AI agents for payments. She wants an intro to Marcus."

**Query**: "Who do I know at Stripe?" / "What did Marcus and I last discuss?" / "Who should I follow up with?"

**Lint**: "lint" - surfaces decaying relationships, stale threads, and missing pages.

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
