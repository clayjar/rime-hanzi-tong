#!/usr/bin/env python3
# encoding: utf-8
"""Build the five 漢字通 dictionary tables.

Each code starts with an uppercase language marker that is not on the
keyboard: G 官, Y 粵, M 閩, H 韓, J 日. Korean and Japanese syllables
also end in 0. The schema algebra turns those stored codes into the
spellings a user can type. See hanzi_tong.schema.yaml.

Mandarin tones come from terra-pinyin because luna-pinyin has no tone
digits. Word frequencies come from rime-essay, the same list Luna uses.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "upstream"

MARKERS = {
    "guan": "G",
    "yue": "Y",
    "min": "M",
    "han": "H",
    "ri": "J",
}

SOURCES = {
    "terra": "https://raw.githubusercontent.com/rime/rime-terra-pinyin/master/terra_pinyin.dict.yaml",
    "essay": "https://raw.githubusercontent.com/rime/rime-essay/master/essay.txt",
    "jyutping_chars": "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.chars.dict.yaml",
    "jyutping_words": "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.words.dict.yaml",
    "essay_cantonese": "https://raw.githubusercontent.com/rime/rime-cantonese/main/essay-cantonese.txt",
    "poj": "https://raw.githubusercontent.com/soanseng/rime-phah-taibun/main/schema/phah_taibun.dict.yaml",
    "hanja": "https://raw.githubusercontent.com/gkovacs/rime-korean/master/korean_hanja.dict.yaml",
    "kana": "https://raw.githubusercontent.com/gkovacs/rime-japanese/master/japanese.kana.dict.yaml",
    "mozc": "https://raw.githubusercontent.com/gkovacs/rime-japanese/master/japanese.mozc.dict.yaml",
    "jmdict": "https://raw.githubusercontent.com/gkovacs/rime-japanese/master/japanese.jmdict.dict.yaml",
}

# TL spelling -> one POJ spelling. tsh is replaced before ts.
_POJ_STEPS = (
    ("tsh", "chh"),
    ("ts", "ch"),
    ("ing", "eng"),
    ("ik", "ek"),
    ("ua", "oa"),
    ("ue", "oe"),
    ("oo", "ou"),
)

_PINYIN_SYLLABLE = re.compile(r"[a-z]+[1-5]")
_JYUTPING_SYLLABLE = re.compile(r"[a-z]+[1-6]")
_POJ_SYLLABLE = re.compile(r"[a-z]+[1-8]?")
_PERCENT = re.compile(r"(\d+(?:\.\d+)?)%")
_NUMBER = re.compile(r"-?\d+")


def is_han(ch: str) -> bool:
    code = ord(ch)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x20000 <= code <= 0x2A6DF
        or 0x2A700 <= code <= 0x2B73F
        or 0x2B740 <= code <= 0x2B81F
        or 0x2B820 <= code <= 0x2CEAF
        or 0x2CEB0 <= code <= 0x2EBEF
        or 0x30000 <= code <= 0x3134F
        or 0x2F800 <= code <= 0x2FA1F
    )


def han_count(text: str) -> int:
    return sum(1 for ch in text if is_han(ch))


def is_hiragana(ch: str) -> bool:
    return 0x3041 <= ord(ch) <= 0x3096


def is_katakana(ch: str) -> bool:
    return 0x30A1 <= ord(ch) <= 0x30FA


def is_kana(ch: str) -> bool:
    return is_hiragana(ch) or is_katakana(ch) or ch == "ー"


def is_hangul_syllable(ch: str) -> bool:
    return 0xAC00 <= ord(ch) <= 0xD7A3


def is_hangul_text(text: str) -> bool:
    return bool(text) and all(is_hangul_syllable(ch) for ch in text)


def mark_code(marker: str, code: str) -> str:
    """Prefix the first syllable and, for 韓/日, end every syllable with 0."""
    parts = code.split()
    if not parts:
        raise ValueError("empty code")
    if marker in ("H", "J"):
        parts = [part if part.endswith("0") else part + "0" for part in parts]
    parts[0] = marker + parts[0]
    return " ".join(parts)


def korean_syllable(raw: str) -> str:
    """gkovacs romanization -> ASCII. Initial q is ㅇ; any other q is ng."""
    text = raw.strip().lower()
    text = re.sub(r"\d+$", "", text)
    if text.startswith("q"):
        text = text[1:]
    text = text.replace("q", "ng")
    if not re.fullmatch(r"[a-z]+", text):
        return ""
    return text


def poj_alias_syllable(syllable: str) -> str | None:
    """Return the POJ twin of one TL syllable, or None if it is unchanged."""
    match = re.fullmatch(r"([a-z]+)([1-8])?", syllable)
    if not match:
        return None
    body, tone = match.group(1), match.group(2) or ""
    rewritten = body
    for source, target in _POJ_STEPS:
        rewritten = rewritten.replace(source, target)
    if rewritten == body:
        return None
    return rewritten + tone


def poj_alias_code(code: str) -> str | None:
    parts = code.split()
    changed = False
    rewritten = []
    for part in parts:
        alias = poj_alias_syllable(part)
        if alias:
            changed = True
            rewritten.append(alias)
        else:
            rewritten.append(part)
    if not changed:
        return None
    return " ".join(rewritten)


def normalize_japanese_reading(raw: str) -> str | None:
    """Hepburn-like romaji. A hyphen after a vowel repeats that vowel (ー)."""
    text = raw.strip().lower().replace("'", "").replace("’", "")
    if not text:
        return None
    syllables = []
    for part in text.split():
        if not re.fullmatch(r"[a-z\-]+", part):
            return None
        letters = []
        for ch in part:
            if ch == "-":
                if letters and letters[-1] in "aeiou":
                    letters.append(letters[-1])
                continue
            letters.append(ch)
        syllable = "".join(letters)
        if not re.fullmatch(r"[a-z]+", syllable):
            return None
        syllables.append(syllable)
    if not syllables:
        return None
    return " ".join(syllables)


def project_syllable(syllable: str, rules: list[tuple[str, str]]) -> set[str]:
    """Mirror librime's per-syllable derive: keep the old spelling, add the new one."""
    spellings = {syllable}
    compiled = [(re.compile(pattern), repl) for pattern, repl in rules]
    for pattern, repl in compiled:
        nxt = set(spellings)
        for item in spellings:
            derived = pattern.sub(repl, item)
            if derived and derived != item:
                nxt.add(derived)
        spellings = nxt
    return spellings


def typeable_spellings(spellings: set[str]) -> set[str]:
    """Spellings the schema alphabet can actually produce."""
    return {item for item in spellings if re.fullmatch(r"[a-z1-8 ]+", item)}


def load_schema_algebra(schema_path: Path) -> list[tuple[str, str]]:
    text = schema_path.read_text(encoding="utf-8")
    rules = []
    in_algebra = False
    for line in text.splitlines():
        if line.startswith("  algebra:"):
            in_algebra = True
            continue
        if not in_algebra:
            continue
        if line.startswith("    - derive/"):
            body = line.split("derive/", 1)[1].strip()
            pattern, repl, _rest = body.split("/", 2)
            rules.append((pattern, repl))
            continue
        if line and not line.startswith("    "):
            break
    if not rules:
        raise RuntimeError("no derive rules found in " + str(schema_path))
    return rules


class Table:
    def __init__(self) -> None:
        self.best: dict[tuple[str, str], int] = {}

    def add(self, text: str, code: str, weight: int) -> None:
        if not text or not code or "\t" in text or "\n" in text:
            return
        weight = max(1, int(weight))
        key = (text, code)
        previous = self.best.get(key)
        if previous is None or weight > previous:
            self.best[key] = weight

    def __len__(self) -> int:
        return len(self.best)

    def write(self, path: Path, name: str, comment: str) -> None:
        rows = sorted(self.best.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write("# Rime dictionary\n")
            handle.write("# encoding: utf-8\n")
            handle.write("#\n")
            for line in comment.strip().splitlines():
                handle.write("# " + line + "\n")
            handle.write("\n---\n")
            handle.write(f"name: {name}\n")
            handle.write('version: "0.1.0"\n')
            handle.write("sort: by_weight\n")
            handle.write("use_preset_vocabulary: false\n")
            handle.write("columns:\n")
            handle.write("  - text\n")
            handle.write("  - code\n")
            handle.write("  - weight\n")
            handle.write("...\n")
            for (text, code), weight in rows:
                handle.write(f"{text}\t{code}\t{weight}\n")


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"cached {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(dest.suffix + ".part")
    print(f"download {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "hanzi-tong-build"})
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as handle:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            handle.write(chunk)
    temporary.replace(dest)


def iter_body_lines(path: Path):
    in_body = False
    comments = True
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n\r")
            if not in_body:
                if line.strip() == "...":
                    in_body = True
                continue
            if not line.strip():
                continue
            if comments and line.lstrip().startswith("#"):
                if line.strip() == "# no comment":
                    comments = False
                continue
            yield line


def split_row(line: str) -> tuple[str, str, str]:
    parts = line.split("\t")
    text = parts[0].strip() if parts else ""
    code = parts[1].strip() if len(parts) > 1 else ""
    extra = parts[2].strip() if len(parts) > 2 else ""
    return text, code, extra


def load_weight_table(path: Path) -> dict[str, int]:
    weights: dict[str, int] = {}
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or line in ("---", "..."):
                continue
            if "\t" in line:
                text, weight, *_rest = line.split("\t")
            else:
                pieces = line.rsplit(None, 1)
                if len(pieces) != 2:
                    continue
                text, weight = pieces
            if _NUMBER.fullmatch(weight.strip()):
                weights[text.strip()] = int(weight)
    return weights


def frequency_weight(frequency: int | None, index: int, extra: str, have_corpus: bool) -> int:
    """Rank a corpus hit above file order, and a percent reading below its headword.

    `frequency` is None when the text is absent from the frequency list.
    A listed weight of 0 stays in the low band. File order only breaks ties,
    except when there is no corpus at all.
    """
    if extra and _NUMBER.fullmatch(extra):
        return max(1, int(extra) * 1000 - min(index, 999))
    percent = _PERCENT.fullmatch(extra) if extra else None
    if have_corpus and frequency is not None and frequency > 1:
        base = frequency
        if percent:
            base = int(base * float(percent.group(1)) / 100.0)
        if base < 1:
            base = 1
        return base * 1000 - min(index, 999)
    if percent:
        return max(1, int(float(percent.group(1))))
    if have_corpus:
        return max(1, 1000 - min(index, 999))
    return max(1, 1_000_000 - index)


def valid_code(code: str, syllable: re.Pattern[str]) -> bool:
    parts = code.split()
    return bool(parts) and all(syllable.fullmatch(part) for part in parts)


def build_pinyin(terra_path: Path, essay_path: Path) -> Table:
    essay = load_weight_table(essay_path)
    table = Table()
    best: dict[str, tuple[int, str]] = {}
    index = 0
    have_corpus = bool(essay)
    for line in iter_body_lines(terra_path):
        text, code, extra = split_row(line)
        if not valid_code(code, _PINYIN_SYLLABLE):
            continue
        if not text or any(ch.isspace() for ch in text):
            continue
        index += 1
        weight = frequency_weight(essay.get(text), index, extra, have_corpus)
        table.add(text, mark_code("G", code), weight)
        # Word spelling uses the strongest single-syllable reading of each character.
        if len(text) == 1 and is_han(text) and _PINYIN_SYLLABLE.fullmatch(code):
            previous = best.get(text)
            if previous is None or weight > previous[0]:
                best[text] = (weight, code)

    words = 0
    for text, frequency in essay.items():
        if frequency <= 0 or not 2 <= len(text) <= 4:
            continue
        if not all(is_han(ch) for ch in text):
            continue
        syllables = []
        for ch in text:
            reading = best.get(ch)
            if not reading:
                syllables = []
                break
            syllables.append(reading[1])
        if not syllables:
            continue
        table.add(text, mark_code("G", " ".join(syllables)), frequency * 1000)
        words += 1
    print(f"pinyin entries {len(table)} (essay words {words})")
    return table


def build_jyutping(chars_path: Path, words_path: Path, essay_path: Path) -> Table:
    essay = load_weight_table(essay_path)
    table = Table()
    have_corpus = bool(essay)

    def add_file(path: Path, limit: int) -> None:
        index = 0
        for line in iter_body_lines(path):
            text, code, extra = split_row(line)
            if not text or len(text) > limit:
                continue
            if not valid_code(code, _JYUTPING_SYLLABLE):
                continue
            index += 1
            table.add(
                text,
                mark_code("Y", code),
                frequency_weight(essay.get(text), index, extra, have_corpus),
            )

    add_file(chars_path, 8)
    add_file(words_path, 8)
    print(f"jyutping entries {len(table)} (essay keys {len(essay)})")
    return table


def build_poj(path: Path) -> Table:
    table = Table()
    for line in iter_body_lines(path):
        text, code, extra = split_row(line)
        if not text or len(text) > 8 or han_count(text) < 1 or han_count(text) > 4:
            continue
        code = code.replace("-", " ")
        code = re.sub(r"\s+", " ", code).strip().lower()
        if not valid_code(code, _POJ_SYLLABLE):
            continue
        weight = int(extra) if _NUMBER.fullmatch(extra) else 1
        marked = mark_code("M", code)
        table.add(text, marked, weight)
        alias = poj_alias_code(code)
        if alias and alias != code and valid_code(alias, _POJ_SYLLABLE):
            table.add(text, mark_code("M", alias), weight)
    print(f"poj entries {len(table)}")
    return table


def build_hanja(path: Path) -> Table:
    table = Table()
    hangul_for_reading: dict[str, str] = {}
    index = 0
    for line in iter_body_lines(path):
        text, code, hangul = split_row(line)
        parts = []
        for raw in code.split():
            converted = korean_syllable(raw)
            if not converted:
                parts = []
                break
            parts.append(converted)
        if not parts or not text:
            continue
        reading = " ".join(parts)
        marked = mark_code("H", reading)
        if is_hangul_text(hangul) and hangul not in hangul_for_reading:
            hangul_for_reading[reading] = hangul
        if han_count(text) < 1 and not is_hangul_text(text):
            continue
        index += 1
        # Earlier rows in the source list rank above later Unihan rows.
        table.add(text, marked, 1_000_000_000 - index)
    for reading, hangul in hangul_for_reading.items():
        table.add(hangul, mark_code("H", reading), 2_000_000_000)
    print(f"hanja entries {len(table)}")
    return table


def japanese_class_weight(text: str, kana_table: bool) -> int:
    if kana_table:
        if text and is_hiragana(text[0]):
            return 72000
        return 71000
    if all(is_kana(ch) for ch in text):
        return 80000
    if len(text) == 1 and is_han(text):
        return 60000
    if han_count(text):
        return 40000
    return 10000


def build_japanese(kana_path: Path, mozc_path: Path, jmdict_path: Path) -> Table:
    table = Table()
    index = 0

    def add(text: str, reading: str, kana_table: bool) -> None:
        nonlocal index
        normalized = normalize_japanese_reading(reading)
        if not normalized or not text or len(text) > 4:
            return
        if not any(is_han(ch) or is_kana(ch) for ch in text):
            return
        index += 1
        weight = japanese_class_weight(text, kana_table) * 1_000_000 - min(index, 999_999)
        table.add(text, mark_code("J", normalized), weight)

    for line in iter_body_lines(kana_path):
        text, code, _extra = split_row(line)
        add(text, code, True)
    for path in (mozc_path, jmdict_path):
        for line in iter_body_lines(path):
            text, code, _extra = split_row(line)
            add(text, code, False)
    print(f"japanese entries {len(table)}")
    return table


def write_manifest(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Rime dictionary",
                "# encoding: utf-8",
                "#",
                "# 漢字通 / Han Character Bridge",
                "# Merges the five language tables. Codes carry a language marker",
                "# so identical spellings do not collapse into one reading.",
                "#",
                "---",
                "name: hanzi_tong",
                'version: "0.1.0"',
                "sort: by_weight",
                "use_preset_vocabulary: false",
                "import_tables:",
                "  - hanzi_tong.pinyin",
                "  - hanzi_tong.jyutping",
                "  - hanzi_tong.poj",
                "  - hanzi_tong.hanja",
                "  - hanzi_tong.kanji",
                "...",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def file_has_entry(path: Path, text: str, code: str) -> bool:
    needle = f"{text}\t{code}\t"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(needle):
                return True
    return False


def verify_samples(root: Path) -> None:
    expected = [
        (root / "hanzi_tong.pinyin.dict.yaml", "幫", "Gbang1"),
        (root / "hanzi_tong.jyutping.dict.yaml", "崩", "Ybang1"),
        (root / "hanzi_tong.poj.dict.yaml", "蠓", "Mbang2"),
        (root / "hanzi_tong.hanja.dict.yaml", "方", "Hbang0"),
        (root / "hanzi_tong.hanja.dict.yaml", "방", "Hbang0"),
        (root / "hanzi_tong.kanji.dict.yaml", "番", "Jban0"),
    ]
    missing = []
    for path, text, code in expected:
        if not file_has_entry(path, text, code):
            missing.append(f"{path.name}: {text} {code}")
    if missing:
        raise SystemExit("sample entries missing:\n" + "\n".join(missing))
    print("sample entries ok")


def build_all(cache: Path, root: Path) -> None:
    paths = {}
    for name, url in SOURCES.items():
        dest = cache / Path(url).name
        download(url, dest)
        paths[name] = dest

    pinyin = build_pinyin(paths["terra"], paths["essay"])
    jyutping = build_jyutping(
        paths["jyutping_chars"], paths["jyutping_words"], paths["essay_cantonese"]
    )
    poj = build_poj(paths["poj"])
    hanja = build_hanja(paths["hanja"])
    japanese = build_japanese(paths["kana"], paths["mozc"], paths["jmdict"])

    pinyin.write(
        root / "hanzi_tong.pinyin.dict.yaml",
        "hanzi_tong.pinyin",
        "官 Mandarin from terra-pinyin (toned CC-CEDICT) and rime-essay.\n"
        "Marker G. Tone digits are 1-5. ü is typed as v.",
    )
    jyutping.write(
        root / "hanzi_tong.jyutping.dict.yaml",
        "hanzi_tong.jyutping",
        "粵 Cantonese from rime-cantonese jyut6ping3 chars and words.\n"
        "Marker Y. LSHK Jyutping tone digits are 1-6.\n"
        "Frequencies from essay-cantonese when the word is listed there.",
    )
    poj.write(
        root / "hanzi_tong.poj.dict.yaml",
        "hanzi_tong.poj",
        "閩 Minnan from rime-phah-taibun.\n"
        "Marker M. Canonical codes are TL ASCII; a POJ twin is added\n"
        "(ch/chh, oa/oe, ou, eng/ek) so those aliases stay inside 閩.",
    )
    hanja.write(
        root / "hanzi_tong.hanja.dict.yaml",
        "hanzi_tong.hanja",
        "韓 Hanja from gkovacs/rime-korean.\n"
        "Marker H and a final 0. Initial q is dropped; other q becomes ng,\n"
        "so baq is typed bang. The hangul syllable is its own candidate.",
    )
    japanese.write(
        root / "hanzi_tong.kanji.dict.yaml",
        "hanzi_tong.kanji",
        "日 Kana, kanji, and short words from gkovacs/rime-japanese\n"
        "(kana table, Mozc, JMdict). Marker J and a final 0.\n"
        "Hepburn n is ん. A hyphen in the source reading repeats the vowel.\n"
        "Those packages omit corpus costs, so weights prefer the kana spelling,\n"
        "then a single kanji, then a short word.",
    )
    write_manifest(root / "hanzi_tong.dict.yaml")
    verify_samples(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build 漢字通 dictionaries")
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    build_all(args.cache, args.root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
