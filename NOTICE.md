# Notices

漢字通 / Han Character Bridge, version 0.1.0.

The schema, Lua filter, build script, and installer are BSD-3-Clause. See LICENSE.

The generated dictionary tables are derived data. They stay under the terms of the projects they come from.

## Mandarin

- [rime/rime-terra-pinyin](https://github.com/rime/rime-terra-pinyin), which adapts [CC-CEDICT](https://cc-cedict.org/) (Creative Commons Attribution-ShareAlike 3.0). Terra Pinyin supplies the tone digits. Luna Pinyin does not.
- [rime/rime-essay](https://github.com/rime/rime-essay) supplies character and word frequencies, the same list Luna Pinyin uses for common words.

## Cantonese

- [rime/rime-cantonese](https://github.com/rime/rime-cantonese) `jyut6ping3.chars`, `jyut6ping3.words`, and `essay-cantonese.txt`.
- Licensed under Creative Commons Attribution 4.0 and the Open Database License, as stated in that repository.

## Minnan

- [soanseng/rime-phah-taibun](https://github.com/soanseng/rime-phah-taibun) `schema/phah_taibun.dict.yaml`.
- The program is MIT. The dictionary mixes CC BY-SA 4.0 data (including iCorpus and 李江却台語文教基金會 / KipSutian) with other sources listed in that repository's LICENSE, including 教育部 Taiwanese entries. Entries kept here are those with at least one Han character and at most four.

## Korean

- [gkovacs/rime-korean](https://github.com/gkovacs/rime-korean) `korean_hanja.dict.yaml` (Patrick, 한글・漢字).
- That repository does not ship a LICENSE file. The table is included with attribution. Initial `q` is dropped and any other `q` is written `ng`, so `baq` is typed `bang`. The hangul syllable in the third column is also a candidate.

## Japanese

- [gkovacs/rime-japanese](https://github.com/gkovacs/rime-japanese):
  - `japanese.kana.dict.yaml`, Hepburn kana table.
  - `japanese.mozc.dict.yaml`, converted from [Google Mozc](https://github.com/google/mozc) dictionaries (BSD-3-Clause).
  - `japanese.jmdict.dict.yaml`, converted from [JMdict](http://www.edrdg.org/jmdict/j_jmdict.html), property of the Electronic Dictionary Research and Development Group, used under the [EDRDG licence](http://www.edrdg.org/edrdg/licence.html).
- Surfaces longer than four characters are left out. The packaged tables do not include Mozc cost, so the weights in this project prefer a kana spelling, then a single kanji, then a short word.
