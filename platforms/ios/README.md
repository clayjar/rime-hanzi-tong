# iOS / iPadOS (Hamster)

Hamster (倉輸入法) is the iOS and iPadOS frontend. It loads custom schemas from a zip, and the same `lua/hanzi_tong.lua` filter runs there. Hamster's own scheme rules ask a package not to include `rime.lua`, because an import replaces any file of the same name. The schema, dictionaries, and Lua module stay in the shared repository. This directory only adds the Hamster keyboard and the patches you merge by hand.

Release archive: `hanzi-tong-<version>-ios-hamster.zip`, built by `tools/package_release.py`. The archive has no wrapper folder. Hamster fails the import when a zip contains one.

## Install

1. Install 倉輸入法 (Hamster).
2. Import the zip from 输入方案 → + → 导入方案, from the system share sheet, or by Wi-Fi upload into the app's Rime directory (应用文件 / Rime, not SharedSupport and not the keyboard copy). Files land directly in that directory.
3. Import replaces files of the same name. This archive does not contain `rime.lua` or `default.yaml`. It does contain `hanzi_tong.custom.yaml`, which only switches the Lua filter to `lua_filter@*hanzi_tong*balance`. If you already have `hanzi_tong.custom.yaml`, copy it aside before importing and merge that one filter line back.
4. Enable 漢字通 in the schema list. Language switches are saved only when their names are listed in `switcher/save_options`. If `default.custom.yaml` does not exist, copy `hanzi_tong.default-patch.yaml` to `default.custom.yaml`. If it exists, add the `schema_list` and `switcher/save_options` entries from the patch under its `patch:` key.
5. Import the keyboard from 键盘设置 → 键盘布局 → + and choose `hanzi_tong.keyboard.yaml`. The top row is tones 1–8, then 上頁 and 下頁. Space commits. `'` separates syllables. Swipe up on 退格 to clear the spelling. 語言 opens the schema switches. The import adds a layout named 漢字通. It does not replace `hamster.yaml`.
6. Redeploy (重新部署) from the app. Deploy copies 应用文件 over the keyboard files, so edit the app side.

The 漢字 / 汉字 switch uses Hamster's OpenCC data (`t2s.json`). This package does not ship OpenCC.

## Update

Import the new zip, or upload the new schema, dictionaries, and `lua/hanzi_tong.lua` over Wi-Fi. Keep your `default.custom.yaml`. If you changed `hanzi_tong.custom.yaml`, merge again after the import. Redeploy. Re-import the keyboard only when `hanzi_tong.keyboard.yaml` changed.
