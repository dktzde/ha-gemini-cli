#!/usr/bin/env bash
# ==============================================================================
# Gemini CLI Add-on: Gemini entrypoint
# Launches Gemini CLI with flags based on add-on configuration.
# This runs inside tmux, spawned by ttyd.
# ==============================================================================
set -e

# Source environment (written by init-gemini)
if [[ -f /etc/profile.d/gemini.sh ]]; then
    # shellcheck source=/dev/null
    source /etc/profile.d/gemini.sh
fi

# Build gemini args
declare -a GEMINI_ARGS=()

# Model selection
if [[ -n "${GEMINI_MODEL:-}" && "${GEMINI_MODEL}" != "default" ]]; then
    GEMINI_ARGS+=(--model "${GEMINI_MODEL}")
fi

# Yolo mode is handled via managed-settings.json (permissions.allow all tools)
# instead of --dangerously-skip-permissions which is blocked when running as root.

echo "Starting Gemini CLI..."
echo "Working directory: $(pwd)"
echo ""

# Launch Gemini CLI
exec gemini "${GEMINI_ARGS[@]}"
