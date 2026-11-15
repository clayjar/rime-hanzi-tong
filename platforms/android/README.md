# Android (Trime)

Trime (同文輸入法) is the Android frontend. It includes librime-lua, so the same `lua/hanzi_tong.lua` filter runs here as on the desktop. The schema, dictionaries, and Lua module stay in the shared repository. This directory only adds the Trime patches.

Release archive: `hanzi-tong-<version>-android-trime.zip`, built by `tools/package_release.py`. The archive has no wrapper folder.

## Install

1. Install [Trime](https://github.com/osfans/trime) and enable it as the input method. Grant the Rime directory it asks for. The usual path is `/rime` on shared storage. If you set a different directory in Trime, use that one. When Trime is set to copy an external directory over its internal data at deploy time, edit the external directory.
2. Unzip the archive directly into that directory. `hanzi_tong.schema.yaml` and `lua/hanzi_tong.lua` sit next to each other, not inside another folder. Do not copy a computer's `build/` directory or `*.bin` files. The phone compiles its own.
3. The archive does not contain `rime.lua` or `default.yaml`. Leave those files as they are.
4. `hanzi_tong.custom.yaml` is included and only replaces the schema filter list so the filter loads as a Lua module. If you already have that file, merge `lua_filter@*hanzi_tong*balance` into it instead of discarding your other patches.
5. Language switches are saved only when their names are listed in `switcher/save_options`. If `default.custom.yaml` does not exist, copy `hanzi_tong.default-patch.yaml` to `default.custom.yaml`. If it exists, add the `schema_list` and `switcher/save_options` entries from the patch under its `patch:` key. Trime's schema screen can also enable 漢字通. The save_options entries are still required, or a language you turn off comes back at the next deploy.
6. Tone digits need a number row. If `trime.custom.yaml` does not exist, copy `hanzi_tong.trime-patch.yaml` to `trime.custom.yaml`. If it exists, add this entry under `patch:`:

```yaml
"preset_keyboards/hanzi_tong/import_preset": qwerty0
```

Trime then uses its built-in 36-key layout while 漢字通 is the active schema. Digits 1–8 are tones. Long-press `f` pages up and long-press `g` pages down. Long-press the 中/英 key opens the schema menu. This patch applies to the default theme. A theme you chose under another file name keeps its own keys until you add the same entry there.

7. Deploy in Trime (部署). The first deploy compiles the dictionaries and can take several minutes. Wait for it to finish.

The 漢字 / 汉字 switch uses Trime's OpenCC data (`t2s.json`). This package does not ship OpenCC.

## Update

Copy the new schema, dictionaries, `lua/hanzi_tong.lua`, and `hanzi_tong.custom.yaml` over the old ones. Keep your `default.custom.yaml` and `trime.custom.yaml` if you have already merged the patches. Deploy again.
