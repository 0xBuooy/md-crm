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

if [[ -z "${HERMES_AGENT_CMD:-}" ]] && ! command -v hermes >/dev/null 2>&1; then
  echo "[hermes-e2e] hermes CLI not found on PATH. Install Hermes or set HERMES_AGENT_CMD to a valid hermes command." >&2
  exit 127
fi

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
# Newer hermes `skills install` only accepts registry identifiers. Local skills
# are picked up from $HERMES_HOME/skills/<name>/, so symlink the checkout there.
mkdir -p "$HERMES_HOME/skills"
ln -sfn "$REPO_ROOT" "$HERMES_HOME/skills/md-crm"

E2E_MODEL="${E2E_MODEL:-claude-sonnet-4-6}"

if [[ -z "${HERMES_AGENT_CMD:-}" ]]; then
  # hermes chat takes the prompt as -q ARG (not stdin). Wrap so the transcript
  # runner's stdin-based invocation still works.
  WRAPPER="$TMP/hermes-oneshot.sh"
  cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
prompt=\$(cat)
exec hermes chat -s md-crm -Q --model "$E2E_MODEL" -q "\$prompt"
EOF
  chmod +x "$WRAPPER"
  AGENT_CMD="$WRAPPER"
else
  AGENT_CMD="$HERMES_AGENT_CMD"
fi

echo "[hermes-e2e] wiki=$WIKI_PATH raw=$RAW_PATH"
echo "[hermes-e2e] model=$E2E_MODEL"
echo "[hermes-e2e] agent-cmd=$AGENT_CMD"

python3 "$TESTS_DIR/lib/run_transcript.py" \
  --transcripts-dir "$TESTS_DIR/fixtures" \
  ${E2E_FILTER:+--filter "$E2E_FILTER"} \
  --agent-cmd "$AGENT_CMD" \
  --wiki-path "$WIKI_PATH" \
  --raw-path "$RAW_PATH"
