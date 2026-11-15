# 漢字通 / Han Character Bridge

One QWERTY spelling looks up Mandarin, Cantonese, Minnan, Korean Hanja, and Japanese Kanji. Version 0.1.0 is a Weasel (小狼毫) schema for characters and words.

| | |
| --- | --- |
| Chinese name | 漢字通 |
| English name | Han Character Bridge |
| Schema ID | `hanzi_tong` |

Each candidate is marked with the reading that produced it: 官, 粵, 閩, 韓, or 日.

## Install on Windows

1. Install [Weasel](https://github.com/rime/weasel) 0.16 or newer. That build includes librime-lua.
2. From this repository, build the dictionaries if `hanzi_tong.pinyin.dict.yaml` is not already present:

```bash
python tools/build_dictionaries.py
```

3. Install into the Weasel user folder:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install-weasel.ps1
```

4. Redeploy Weasel (重新部署). The script copies files and registers the schema. It does not deploy.

The installer appends `hanzi_tong` to `schema_list` and adds the Lua hook to `rime.lua` only when they are missing. It does not write a `hanzi_tong.custom.yaml`, so language switches are not reset on the next deploy.

## Typing

Digits `1` through `8` are tone keys. Space commits the highlighted candidate. `[` `]` and `-` `=` page. Arrow keys move the highlight.

`bang` returns every tone. `bang1` keeps 官 / 粵 / 閩 tone 1 and still returns 韓 and 日, which have no tone. A trailing digit on those two is ignored.

| Language | Spelling | Tones |
| --- | --- | --- |
| 官 Mandarin | Hanyu Pinyin. `v` is ü. | 1–5, and 5 is neutral |
| 粵 Cantonese | LSHK Jyutping | 1–6 |
| 閩 Minnan | TL ASCII (`ts`, `oo`, `nn`) and the POJ twins (`ch`, `ou`, `oa`) | 1–8, as stored |
| 韓 Korean | The rime-korean romanization, with `q` written as `ng` | ignored |
| 日 Japanese | Hepburn. `n` is ん | ignored |

`bang` is not rewritten to Japanese `ban`. `ban` is ばん and 番. `bang` is 幫, 崩, 濛, 방, and 方.

Completion is off, so `ban` does not list `bang`. Sentence mode is off: a spelling has to be in the dictionary as a character or a word.

## Languages

Open the schema menu from the Weasel tray icon, or press `Ctrl+\`` while 漢字通 is active.

Each language has a switch. The label is the current state. `官` means Mandarin is included. `官關` turns it off. 粵, 閩, 韓, and 日 work the same way. All five start on. Weasel remembers the choice. The next keystroke uses it. No redeploy is needed.

A language that is off is dropped before ranking, including a word you previously picked from that language. If all five are off, character and word candidates are hidden. Punctuation and ASCII mode still work.

## Traditional and simplified

The dictionaries store traditional characters for 官, 粵, and 閩, Korean hanja as in the source table, and Japanese shinjitai. The `漢字` / `汉字` switch runs OpenCC `t2s`. That conversion also applies to Japanese and Korean candidates.

## Not in 0.1.0

- macOS Squirrel and Linux IBus/Fcitx.
- Mixed-language sentences.
- A context model over the committed sentence. `contextual_score` in `lua/hanzi_tong.lua` returns nil and is the hook for that model.
- An optional `n` / `ng` bridge between Japanese ん and a Chinese `-ng` syllable.

## Tests

```bash
python -m unittest tools/test_build.py
```

Dictionary sample checks run only after `tools/build_dictionaries.py` has written the tables.
