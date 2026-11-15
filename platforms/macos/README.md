# macOS (Squirrel)

The schema, dictionaries, and Lua filter stay at the repository root. This directory has no separate copy.

1. Install [Squirrel](https://github.com/rime/squirrel) 0.16 or newer, with librime-lua.
2. From the repository root:

```bash
bash tools/install-squirrel.sh
```

The script copies the shared files into `~/Library/Rime`, registers `hanzi_tong`, and appends the Lua hook to `rime.lua` only when that hook is missing. It does not deploy. Redeploy from the Squirrel menu (重新部署).
