#!/usr/bin/env bash
# Copies 漢字通 into an IBus and/or Fcitx Rime user directory.
# Does not deploy. Redeploy from the input-method menu after this script finishes.
#
# Usage:
#   tools/install-linux.sh              # every frontend directory that already exists
#   tools/install-linux.sh ibus
#   tools/install-linux.sh fcitx5
#   tools/install-linux.sh fcitx        # Fcitx 4
#   tools/install-linux.sh ibus fcitx5
set -euo pipefail

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"

rime_dir_for() {
    case "$1" in
        ibus) printf '%s\n' "$config_home/ibus/rime" ;;
        fcitx5) printf '%s\n' "$data_home/fcitx5/rime" ;;
        fcitx) printf '%s\n' "$config_home/fcitx/rime" ;;
        *)
            echo "Unknown frontend '$1'. Use ibus, fcitx5, or fcitx." >&2
            return 1
            ;;
    esac
}

# shellcheck source=install-rime-user.sh
source "$(cd "$(dirname "$0")" && pwd)/install-rime-user.sh"

targets=("$@")
if [[ ${#targets[@]} -eq 0 ]]; then
    for name in ibus fcitx5 fcitx; do
        dir="$(rime_dir_for "$name")"
        if [[ -d "$dir" ]]; then
            targets+=("$name")
        fi
    done
    if [[ ${#targets[@]} -eq 0 ]]; then
        echo "No Rime user directory found. Pass the frontend you use:" >&2
        echo "  tools/install-linux.sh ibus" >&2
        echo "  tools/install-linux.sh fcitx5" >&2
        echo "  tools/install-linux.sh fcitx" >&2
        exit 1
    fi
fi

for name in "${targets[@]}"; do
    install_hanzi_tong "$(rime_dir_for "$name")"
done

echo "Redeploy IBus or Fcitx (Deploy / 重新部署). This script does not deploy."
