# Linux (IBus or Fcitx)

The schema, dictionaries, and Lua filter stay at the repository root. This directory has no separate copy.

Release archive: `hanzi-tong-<version>-linux-ibus-fcitx.zip`. IBus, Fcitx 5, and Fcitx 4 share this archive. It contains this installer, `tools/install-rime-user.sh`, and `rime.lua`.

Install `ibus-rime` or `fcitx5-rime` (Fcitx 4: `fcitx-rime`) built with librime-lua. From the repository root:

```bash
bash tools/install-linux.sh
bash tools/install-linux.sh ibus
bash tools/install-linux.sh fcitx5
bash tools/install-linux.sh fcitx
```

With no arguments, the script updates every Rime user directory that already exists.

| Frontend | User directory |
| --- | --- |
| IBus | `~/.config/ibus/rime` |
| Fcitx 5 | `~/.local/share/fcitx5/rime` |
| Fcitx 4 | `~/.config/fcitx/rime` |

`XDG_CONFIG_HOME` and `XDG_DATA_HOME` replace `~/.config` and `~/.local/share` when they are set. The script does not deploy. Redeploy from the input-method menu (重新部署).
