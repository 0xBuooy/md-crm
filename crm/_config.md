---
# LLM CRM Wiki Configuration

# Optional explicit paths (fallback for agents without a native
# config system). Leave empty to use cwd-relative defaults
# (./crm, .). Ignored when running under Hermes or OpenClaw,
# which inject these from ~/.hermes/config.yaml or
# ~/.openclaw/openclaw.json respectively.
wiki_path: ""
raw_path: ""

# Directories to scan for raw interaction notes (vault mode)
# Paths are resolved relative to raw_path above
# Glob patterns supported
raw_sources:
  - "daily/"
  - "meetings/"
  - "notes/"

# Directories to exclude from scanning
exclude:
  - "crm/"
  - "templates/"
  - ".obsidian/"

# Relationship decay thresholds (days)
decay:
  warm_to_cold: 30
  hot_to_warm: 21
  close_to_hot: 45

# Follow-up staleness threshold (days)
stale_thread_days: 14

# Default relationship strength for new contacts
default_strength: "warm"
---

# CRM Configuration

Edit the frontmatter above to customize behavior.
The agent reads this file before every operation.

Path precedence: Hermes `~/.hermes/config.yaml` (under
`skills.config`) > OpenClaw `~/.openclaw/openclaw.json` (under
`skills.entries.md-crm.config`) > this file's `wiki_path` /
`raw_path` keys > cwd-relative defaults (`./crm`, `.`).
