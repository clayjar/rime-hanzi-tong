# Shared installer for a Rime user directory.
# Sourced by the Squirrel and Linux wrappers. Does not deploy.
# Usage: install_hanzi_tong /path/to/rime/user

# Append YAML lines under the first patch: key, or create a patch block.
insert_patch_list() {
    local custom="$1"
    shift
    local block tmp
    block="$(mktemp)"
    tmp="$(mktemp)"
    printf '%s\n' "$@" > "$block"
    if [[ -f "$custom" ]] && grep -q '^patch:[[:space:]]*$' "$custom"; then
        awk -v block="$block" '
            BEGIN { inserted = 0 }
            /^patch:[[:space:]]*$/ && !inserted {
                print
                while ((getline line < block) > 0) print line
                close(block)
                inserted = 1
                next
            }
            { print }
        ' "$custom" > "$tmp"
        mv "$tmp" "$custom"
    else
        if [[ ! -f "$custom" || ! -s "$custom" ]]; then
            : > "$custom"
        elif [[ -n "$(tail -c 1 "$custom")" ]]; then
            printf '\n' >> "$custom"
        fi
        {
            printf 'patch:\n'
            cat "$block"
        } >> "$custom"
        rm -f "$tmp"
    fi
    rm -f "$block"
}

install_hanzi_tong() {
    local dest="$1"
    local root
    root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    local names=(
        hanzi_tong.schema.yaml
        hanzi_tong.dict.yaml
        hanzi_tong.pinyin.dict.yaml
        hanzi_tong.jyutping.dict.yaml
        hanzi_tong.poj.dict.yaml
        hanzi_tong.hanja.dict.yaml
        hanzi_tong.kanji.dict.yaml
    )
    local name source custom lua_path hook

    mkdir -p "$dest/lua"
    for name in "${names[@]}"; do
        source="$root/$name"
        if [[ ! -f "$source" ]]; then
            echo "Missing $source. Run tools/build_dictionaries.py first." >&2
            return 1
        fi
        cp "$source" "$dest/$name"
    done
    cp "$root/lua/hanzi_tong.lua" "$dest/lua/hanzi_tong.lua"

    custom="$dest/default.custom.yaml"
    # A copy at column 0 sits outside patch:, so Rime ignores it.
    if [[ -f "$custom" ]] && grep -q '^switcher/save_options/+:' "$custom"; then
        local stripped
        stripped="$(mktemp)"
        awk '
            /^switcher\/save_options\/\+:[[:space:]]*$/ { skip = 1; next }
            skip && /^[[:space:]]*- disable_(guan|yue|min|han|ri)[[:space:]]*$/ { next }
            skip { skip = 0 }
            { print }
        ' "$custom" > "$stripped"
        mv "$stripped" "$custom"
    fi
    if [[ ! -f "$custom" ]] || ! grep -q 'schema:[[:space:]]*hanzi_tong' "$custom"; then
        insert_patch_list "$custom" \
            "  schema_list/+:" \
            "    - schema: hanzi_tong"
    fi
    # Omitting reset on a switch is not enough. Rime writes a menu choice to
    # user.yaml only when the option name is listed in switcher/save_options.
    if [[ ! -f "$custom" ]] || ! grep -Eq '^[[:space:]]+switcher/save_options/\+:[[:space:]]*$' "$custom"; then
        insert_patch_list "$custom" \
            "  switcher/save_options/+:" \
            "    - disable_guan" \
            "    - disable_yue" \
            "    - disable_min" \
            "    - disable_han" \
            "    - disable_ri"
    fi

    lua_path="$dest/rime.lua"
    hook="$root/rime.lua"
    if [[ ! -f "$lua_path" ]]; then
        cp "$hook" "$lua_path"
    elif ! grep -q 'hanzi_tong_balance' "$lua_path"; then
        printf '\n' >> "$lua_path"
        cat "$hook" >> "$lua_path"
    fi

    echo "Installed 漢字通 into $dest"
}
