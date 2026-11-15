# Windows (Weasel)

The schema, dictionaries, and Lua filter stay at the repository root. This directory has no separate copy.

Release archive: `hanzi-tong-<version>-windows-weasel.zip`. It contains this installer and `rime.lua`, not the Squirrel or Linux scripts.

1. Install [Weasel](https://github.com/rime/weasel) 0.16 or newer, with librime-lua.
2. From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install-weasel.ps1
```

The script copies the shared files into `%APPDATA%\Rime`, registers `hanzi_tong`, and appends the Lua hook to `rime.lua` only when that hook is missing. It does not deploy. Redeploy from the Weasel menu (重新部署).
