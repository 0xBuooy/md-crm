#!/usr/bin/env bash
# OpenClaw e2e runner for md-crm.
#
# Creates a temp workspace with the skill dropped into OpenClaw's discovery
# path and an isolated openclaw.json that points wiki_path / raw_path at
# temp dirs, then drives the transcript through the openclaw CLI.
#
# Requirements:
#   - openclaw CLI on PATH
#   - an API key for whatever provider openclaw is configured for
#   - python3 with pyyaml
#
# Override OPENCLAW_AGENT_CMD if your build uses a different flag for
# one-shot / non-interactive mode.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TESTS_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd "$TESTS_DIR/../.." && pwd)

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

WIKI_PATH="$TMP/wiki"
RAW_PATH="$TMP/raw"
mkdir -p "$WIKI_PATH" "$RAW_PATH/daily"

SKILLS_DIR="$TMP/.openclaw/skills"
mkdir -p "$SKILLS_DIR"
# Per README, OpenClaw discovers skills by directory. Drop the repo contents
# (SKILL.md, crm/, raw/, etc.) into a named skill dir.
cp -R "$REPO_ROOT"/. "$SKILLS_DIR/md-crm/"

cat > "$TMP/.openclaw/openclaw.json" <<EOF
{
  "skills": {
    "entries": {
      "md-crm": {
        "enabled": true,
        "config": {
          "wiki_path": "$WIKI_PATH",
          "raw_path": "$RAW_PATH"
        }
      }
    }
  }
}
EOF

export OPENCLAW_HOME="$TMP/.openclaw"

AGENT_CMD="${OPENCLAW_AGENT_CMD:-openclaw run --skill md-crm --non-interactive}"

echo "[openclaw-e2e] wiki=$WIKI_PATH raw=$RAW_PATH"
echo "[openclaw-e2e] agent-cmd=$AGENT_CMD"

python3 "$TESTS_DIR/lib/run_transcript.py" \
  --transcript "$TESTS_DIR/fixtures/transcript.yaml" \
  --agent-cmd "$AGENT_CMD" \
  --wiki-path "$WIKI_PATH" \
  --raw-path "$RAW_PATH"
