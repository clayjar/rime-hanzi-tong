#!/usr/bin/env python3
# encoding: utf-8
"""Tests for 漢字通 spelling rules and the generated sample entries."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dictionaries as build

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


if __name__ == "__main__":
    unittest.main()
