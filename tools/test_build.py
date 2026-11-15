#!/usr/bin/env python3
# encoding: utf-8
"""Tests for 漢字通 spelling rules and the generated sample entries."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dictionaries as build
import package_release

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "hanzi_tong.schema.yaml"


class AlgebraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = build.load_schema_algebra(SCHEMA)

    def typeable(self, syllable: str) -> set[str]:
        return build.typeable_spellings(build.project_syllable(syllable, self.rules))

    def test_mandarin_tone_is_optional_and_exact(self) -> None:
        spellings = self.typeable("Gbang1")
        self.assertIn("bang", spellings)
        self.assertIn("bang1", spellings)
        self.assertNotIn("bang2", spellings)
        self.assertNotIn("bang3", spellings)

    def test_cantonese_tone_six(self) -> None:
        spellings = self.typeable("Ybang6")
        self.assertIn("bang", spellings)
        self.assertIn("bang6", spellings)
        self.assertNotIn("bang1", spellings)

    def test_minnan_tone_two_does_not_match_tone_one(self) -> None:
        spellings = self.typeable("Mbang2")
        self.assertIn("bang", spellings)
        self.assertIn("bang2", spellings)
        self.assertNotIn("bang1", spellings)

    def test_korean_ignores_a_typed_tone(self) -> None:
        spellings = self.typeable("Hbang0")
        self.assertIn("bang", spellings)
        for tone in range(1, 9):
            self.assertIn(f"bang{tone}", spellings)
        self.assertNotIn("bang0", spellings)

    def test_japanese_ban_is_not_bang(self) -> None:
        spellings = self.typeable("Jban0")
        self.assertIn("ban", spellings)
        self.assertIn("ban1", spellings)
        self.assertNotIn("bang", spellings)

    def test_rules_cover_every_sentinel_tone(self) -> None:
        for tone in range(1, 9):
            self.assertTrue(
                any(pattern == "0$" and repl == str(tone) for pattern, repl in self.rules),
                tone,
            )


class SpellingTests(unittest.TestCase):
    def test_markers(self) -> None:
        self.assertEqual(build.mark_code("G", "zhong1 guo2"), "Gzhong1 guo2")
        self.assertEqual(build.mark_code("H", "bang"), "Hbang0")
        self.assertEqual(build.mark_code("J", "ni hon"), "Jni0 hon0")

    def test_korean_q_to_ng(self) -> None:
        self.assertEqual(build.korean_syllable("baq"), "bang")
        self.assertEqual(build.korean_syllable("qan"), "an")
        self.assertEqual(build.korean_syllable("gaiq"), "gaing")
        self.assertEqual(build.mark_code("H", build.korean_syllable("baq")), "Hbang0")

    def test_poj_twins(self) -> None:
        self.assertEqual(build.poj_alias_syllable("tsoo2"), "chou2")
        self.assertEqual(build.poj_alias_syllable("tshia1"), "chhia1")
        self.assertEqual(build.poj_alias_syllable("kua1"), "koa1")
        self.assertEqual(build.poj_alias_syllable("ing5"), "eng5")
        self.assertIsNone(build.poj_alias_syllable("bang2"))
        self.assertEqual(build.poj_alias_code("tsia1 png1"), "chia1 png1")
        self.assertEqual(build.mark_code("M", "chou2"), "Mchou2")

    def test_japanese_long_vowel_hyphen(self) -> None:
        self.assertEqual(build.normalize_japanese_reading("ti-shatsu"), "tiishatsu")
        self.assertEqual(build.normalize_japanese_reading("ban"), "ban")
        self.assertIsNone(build.normalize_japanese_reading("_a"))


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = SCHEMA.read_text(encoding="utf-8")
        cls.lua = (ROOT / "lua" / "hanzi_tong.lua").read_text(encoding="utf-8")

    def test_identity(self) -> None:
        self.assertIn("schema_id: hanzi_tong", self.schema)
        self.assertIn('name: "漢字通"', self.schema)
        self.assertIn('version: "0.1.0"', self.schema)

    def test_language_switches_persist(self) -> None:
        for option in ("disable_guan", "disable_yue", "disable_min", "disable_han", "disable_ri"):
            self.assertIn(f"name: {option}", self.schema)
            self.assertIn(option, self.lua)
        # reset would force the switch on every load. Persistence is the
        # switcher/save_options list added by the installers.
        section = self.schema.split("name: disable_guan", 1)[1]
        self.assertNotIn("\n    reset:", section)
        self.assertIn("switcher/save_options", self.schema)

    def test_installers_save_language_options(self) -> None:
        weasel = (ROOT / "tools" / "install-weasel.ps1").read_text(encoding="utf-8")
        shared = (ROOT / "tools" / "install-rime-user.sh").read_text(encoding="utf-8")
        for script in (weasel, shared):
            self.assertIn("switcher/save_options/+", script)
            for option in ("disable_guan", "disable_yue", "disable_min", "disable_han", "disable_ri"):
                self.assertIn(option, script)

    def test_future_hooks_are_comments_not_behavior(self) -> None:
        self.assertIn("enable_sentence: false", self.schema)
        self.assertIn("enable_completion: false", self.schema)
        self.assertIn("contextual_score", self.lua)
        self.assertIn("return nil", self.lua)


class GeneratedSampleTests(unittest.TestCase):
    def test_bang_and_ban_samples(self) -> None:
        samples = [
            ("hanzi_tong.pinyin.dict.yaml", "幫", "Gbang1"),
            ("hanzi_tong.jyutping.dict.yaml", "崩", "Ybang1"),
            ("hanzi_tong.poj.dict.yaml", "蠓", "Mbang2"),
            ("hanzi_tong.hanja.dict.yaml", "方", "Hbang0"),
            ("hanzi_tong.hanja.dict.yaml", "방", "Hbang0"),
            ("hanzi_tong.kanji.dict.yaml", "番", "Jban0"),
        ]
        missing_files = [name for name, _text, _code in samples if not (ROOT / name).exists()]
        if missing_files:
            self.skipTest("dictionaries are not built yet")
        for name, text, code in samples:
            self.assertTrue(
                build.file_has_entry(ROOT / name, text, code),
                f"{name} should contain {text} {code}",
            )


def yaml_list(text: str, header: str) -> list[str]:
    items: list[str] = []
    started = False
    for line in text.splitlines():
        if not started:
            if line == header:
                started = True
            continue
        if line.startswith("    - "):
            items.append(line[6:].strip().strip('"'))
            continue
        if line.strip() == "" or line.lstrip().startswith("#"):
            continue
        break
    return items


class PlatformTests(unittest.TestCase):
    def test_mobile_filter_follows_the_schema(self) -> None:
        schema_filters = yaml_list(SCHEMA.read_text(encoding="utf-8"), "  filters:")
        self.assertIn("lua_filter@hanzi_tong_balance", schema_filters)
        expected = [
            "lua_filter@*hanzi_tong*balance" if item == "lua_filter@hanzi_tong_balance" else item
            for item in schema_filters
        ]
        android = ROOT / "platforms" / "android" / "trime" / "hanzi_tong.custom.yaml"
        ios = ROOT / "platforms" / "ios" / "hamster" / "hanzi_tong.custom.yaml"
        self.assertEqual(android.read_bytes(), ios.read_bytes())
        self.assertEqual(yaml_list(android.read_text(encoding="utf-8"), "  engine/filters:"), expected)

    def test_default_patches_match_and_save_languages(self) -> None:
        android = ROOT / "platforms" / "android" / "trime" / "hanzi_tong.default-patch.yaml"
        ios = ROOT / "platforms" / "ios" / "hamster" / "hanzi_tong.default-patch.yaml"
        self.assertEqual(android.read_bytes(), ios.read_bytes())
        text = android.read_text(encoding="utf-8")
        self.assertIn("schema: hanzi_tong", text)
        for option in ("disable_guan", "disable_yue", "disable_min", "disable_han", "disable_ri"):
            self.assertIn(f"- {option}", text)
        self.assertNotIn("default.custom.yaml:", text)

    def test_trime_patch_selects_the_digit_row(self) -> None:
        text = (ROOT / "platforms" / "android" / "trime" / "hanzi_tong.trime-patch.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn('"preset_keyboards/hanzi_tong/import_preset": qwerty0', text)

    def test_hamster_keyboard_sends_tones_through_rime(self) -> None:
        text = (ROOT / "platforms" / "ios" / "hamster" / "hanzi_tong.keyboard.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("keyboards:", text)
        self.assertIn('name: "漢字通"', text)
        for digit in "12345678":
            self.assertIn(f'char: "{digit}"', text)
        self.assertGreaterEqual(text.count("processByRIME: true"), 8 + 26)
        self.assertIn('keys: "Page_Up"', text)
        self.assertIn('keys: "Page_Down"', text)
        self.assertNotIn("hamster.yaml", text.split("does not replace hamster.yaml", 1)[-1])

    def test_install_notes_do_not_replace_user_files(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("hanzi-tong-<version>-rime.zip", readme)
        self.assertIn("hanzi-tong-<version>-android-trime.zip", readme)
        self.assertIn("hanzi-tong-<version>-ios-hamster.zip", readme)
        for path in (
            ROOT / "platforms" / "android" / "README.md",
            ROOT / "platforms" / "ios" / "README.md",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn("rime.lua", text)
            self.assertIn("default.yaml", text)
            self.assertIn("switcher/save_options", text)
            self.assertIn("no wrapper folder", text.lower())


class PackageTests(unittest.TestCase):
    def test_mobile_archives_leave_user_files_alone(self) -> None:
        for kind in ("android-trime", "ios-hamster"):
            names = [arc for arc, _rel in package_release.members(kind)]
            self.assertIn("hanzi_tong.schema.yaml", names)
            self.assertIn("lua/hanzi_tong.lua", names)
            self.assertIn("hanzi_tong.custom.yaml", names)
            self.assertNotIn("rime.lua", names)
            self.assertNotIn("default.yaml", names)
            self.assertNotIn("default.custom.yaml", names)
            self.assertTrue(all(not name.startswith("hanzi-tong") for name in names))
        desktop = [arc for arc, _rel in package_release.members("rime")]
        self.assertIn("rime.lua", desktop)
        self.assertIn("tools/install-linux.sh", desktop)

    def test_sources_other_than_generated_tables_exist(self) -> None:
        generated = {
            "hanzi_tong.pinyin.dict.yaml",
            "hanzi_tong.jyutping.dict.yaml",
            "hanzi_tong.poj.dict.yaml",
            "hanzi_tong.kanji.dict.yaml",
        }
        for kind in package_release.PACKAGES:
            absent = [
                rel
                for _arc, rel in package_release.members(kind)
                if rel not in generated and not (ROOT / rel).is_file()
            ]
            self.assertEqual(absent, [], kind)

    def test_zip_is_flat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text("## 9.9.9 - test\n", encoding="utf-8")
            (root / "lua").mkdir()
            (root / "tools").mkdir()
            (root / "platforms" / "android" / "trime").mkdir(parents=True)
            (root / "platforms" / "ios" / "hamster").mkdir(parents=True)
            for kind in package_release.PACKAGES:
                for _arc, rel in package_release.members(kind):
                    path = root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists():
                        path.write_text("x", encoding="utf-8")
            dest = root / "out"
            written = package_release.write_package(root, "ios-hamster", dest, "9.9.9")
            self.assertEqual(written.name, "hanzi-tong-9.9.9-ios-hamster.zip")
            with zipfile.ZipFile(written) as archive:
                names = archive.namelist()
            self.assertIn("hanzi_tong.schema.yaml", names)
            self.assertIn("lua/hanzi_tong.lua", names)
            self.assertNotIn("rime.lua", names)
            self.assertFalse(any(name.startswith("hanzi-tong") for name in names))


if __name__ == "__main__":
    unittest.main()
