# Shared installer for a Rime user directory.
# Sourced by the Squirrel and Linux wrappers. Does not deploy.
# Usage: install_hanzi_tong /path/to/rime/user

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
    if [[ ! -f "$custom" ]] || ! grep -q 'schema:[[:space:]]*hanzi_tong' "$custom"; then
        if [[ -f "$custom" ]] && grep -q '^patch:[[:space:]]*$' "$custom"; then
            local tmp
            tmp="$(mktemp)"
            awk '
                BEGIN { inserted = 0 }
                /^patch:[[:space:]]*$/ && !inserted {
                    print
                    print "  schema_list/+:"
                    print "    - schema: hanzi_tong"
                    inserted = 1
                    next
                }
                { print }
            ' "$custom" > "$tmp"
            mv "$tmp" "$custom"
        else
            if [[ -f "$custom" && -s "$custom" ]]; then
                printf '\n' >> "$custom"
            fi
            printf 'patch:\n  schema_list/+:\n    - schema: hanzi_tong\n' >> "$custom"
        fi
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
