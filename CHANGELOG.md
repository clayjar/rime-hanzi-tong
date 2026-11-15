# Changelog

## 0.3.0 - 2026-11-15

- Add Android (Trime) and iOS / iPadOS (Hamster) packages built from the same schema, dictionaries, and Lua filter.
- Those packages omit `rime.lua` and `default.yaml`. The filter is loaded as a Lua module, and schema registration is a patch you merge into `default.custom.yaml`.
- Trime uses the built-in 36-key layout so digits 1–8 are on the keyboard. Hamster gets a 26-key layout with a tone row.

## 0.2.1 - 2026-11-14

- Save the five language switches in `user.yaml`, so a language that is turned off stays off after leaving Rime.

## 0.2.0 - 2026-11-14

- Add installers for macOS Squirrel and Linux IBus, Fcitx 5, and Fcitx 4.
- The schema, dictionaries, and Lua filter stay shared with the Weasel install.

## 0.1.0 - 2026-11-14

- Add the 漢字通 / Han Character Bridge schema for Weasel.
- Look up Mandarin, Cantonese, Minnan, Korean Hanja, and Japanese from one spelling.
- Tone digits are optional for 官, 粵, and 閩, and ignored for 韓 and 日.
- Each language can be turned off from the schema menu, and the choice is remembered.
