---
# LLM CRM Wiki Configuration

# Directories to scan for raw interaction notes (vault mode)
# Paths are relative to the vault/workspace root
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
