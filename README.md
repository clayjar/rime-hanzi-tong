# 漢字通 / Han Character Bridge

Unified multilingual phonetic input for 漢字: type a spelling in Latin letters and 漢字通 looks up Mandarin, Cantonese, Minnan, Korean Hanja, and Japanese Kanji from that same input. Schema 0.1.0 is for characters and words on Weasel (小狼毫), Squirrel (鼠鬚管), and IBus or Fcitx.

| | |
| --- | --- |
| Chinese name | 漢字通 |
| English name | Han Character Bridge |
| Schema ID | `hanzi_tong` |

Each candidate is marked with the reading that produced it: 官, 粵, 閩, 韓, or 日.  (You can toggle any language off.)

The idea is from Discord user @ilhanmyeong.

![IME in action](https://files.mhan.dev/img/rime-hanzi-tong-1.png "when typing bang")

## Install

Build the dictionaries once if `hanzi_tong.pinyin.dict.yaml` is not already present. The same files are used on every system:

```bash
python tools/build_dictionaries.py
```

Each installer copies those files into the Rime user directory, appends `hanzi_tong` to `schema_list`, and adds the Lua hook to `rime.lua` only when they are missing. None of them deploy, and none of them write a `hanzi_tong.custom.yaml`, so language switches are not reset on the next deploy. Afterward, redeploy from the input-method menu (重新部署).

The frontend has to include librime-lua. Weasel and Squirrel 0.16 and newer do. On Linux, install `ibus-rime` or `fcitx5-rime` (Fcitx 4: `fcitx-rime`) built with librime-lua.

### Windows (Weasel)

1. Install [Weasel](https://github.com/rime/weasel) 0.16 or newer.
2. Install into `%APPDATA%\Rime`:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install-weasel.ps1
```

### macOS (Squirrel)

1. Install [Squirrel](https://github.com/rime/squirrel) 0.16 or newer.
2. Install into `~/Library/Rime`:

```bash
bash tools/install-squirrel.sh
```

### Linux (IBus or Fcitx)

With no arguments, the script updates every Rime user directory that already exists among IBus, Fcitx 5, and Fcitx 4. Name the frontend to create that directory:

```bash
bash tools/install-linux.sh
bash tools/install-linux.sh ibus
bash tools/install-linux.sh fcitx5
bash tools/install-linux.sh fcitx
```

| Frontend | User directory |
| --- | --- |
| IBus | `~/.config/ibus/rime` |
| Fcitx 5 | `~/.local/share/fcitx5/rime` |
| Fcitx 4 | `~/.config/fcitx/rime` |

`XDG_CONFIG_HOME` and `XDG_DATA_HOME` replace `~/.config` and `~/.local/share` when they are set.

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

Open the schema menu from the input-method icon, or press `Ctrl+\`` while 漢字通 is active.

Each language has a switch. The label is the current state. `官` means Mandarin is included. `官關` turns it off. 粵, 閩, 韓, and 日 work the same way. All five start on. Rime remembers the choice. The next keystroke uses it. No redeploy is needed.

A language that is off is dropped before ranking, including a word you previously picked from that language. If all five are off, character and word candidates are hidden. Punctuation and ASCII mode still work.

## Traditional and simplified

The dictionaries store traditional characters for 官, 粵, and 閩, Korean hanja as in the source table, and Japanese shinjitai. The `漢字` / `汉字` switch runs OpenCC `t2s`. That conversion also applies to Japanese and Korean candidates.

## Not in this version

- Mixed-language sentences.
- A context model over the committed sentence. `contextual_score` in `lua/hanzi_tong.lua` returns nil and is the hook for that model.
- An optional `n` / `ng` bridge between Japanese ん and a Chinese `-ng` syllable.

## Tests

```bash
python -m unittest tools/test_build.py
```

Dictionary sample checks run only after `tools/build_dictionaries.py` has written the tables.
