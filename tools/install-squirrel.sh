#!/usr/bin/env bash
# Copies 漢字通 into the Squirrel user directory and registers the schema.
# Does not deploy. Redeploy from the Squirrel menu after this script finishes.
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Squirrel install runs on macOS. This machine is $(uname -s)." >&2
    exit 1
fi

# shellcheck source=install-rime-user.sh
source "$(cd "$(dirname "$0")" && pwd)/install-rime-user.sh"
install_hanzi_tong "${HOME}/Library/Rime"
echo "Redeploy Squirrel (Deploy / 重新部署). This script does not deploy."
