#!/usr/bin/env bash
# Hermes e2e runner for md-crm.
#
# Provisions an isolated HERMES_HOME with wiki_path/raw_path pointing at temp
# dirs, installs the skill from this checkout, then drives the transcript
# through the hermes CLI.
#
# Requirements:
#   - hermes CLI on PATH (https://hermes-agent.nousresearch.com)
#   - ANTHROPIC_API_KEY (or whatever provider hermes is configured for)
#   - python3 with pyyaml
#
# Override HERMES_AGENT_CMD to change the one-shot invocation if your hermes
# build uses a different flag for non-interactive mode.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TESTS_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd "$TESTS_DIR/../.." && pwd)

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

WIKI_PATH="$TMP/wiki"
RAW_PATH="$TMP/raw"
mkdir -p "$WIKI_PATH" "$RAW_PATH/daily"

export HERMES_HOME="$TMP/.hermes"
mkdir -p "$HERMES_HOME"

cat > "$HERMES_HOME/config.yaml" <<EOF
skills:
  config:
    wiki_path: "$WIKI_PATH"
    raw_path: "$RAW_PATH"
EOF

echo "[hermes-e2e] installing skill from $REPO_ROOT"
hermes skills install "$REPO_ROOT"

AGENT_CMD="${HERMES_AGENT_CMD:-hermes chat --skill md-crm --non-interactive}"

echo "[hermes-e2e] wiki=$WIKI_PATH raw=$RAW_PATH"
echo "[hermes-e2e] agent-cmd=$AGENT_CMD"

python3 "$TESTS_DIR/lib/run_transcript.py" \
  --transcript "$TESTS_DIR/fixtures/transcript.yaml" \
  --agent-cmd "$AGENT_CMD" \
  --wiki-path "$WIKI_PATH" \
  --raw-path "$RAW_PATH"
