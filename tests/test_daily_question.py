"""Offline tests for scripts/post_daily_question.py — no API calls."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(state_path: Path, questions_path: Path = None) -> object:
    """Import the script fresh with env pointed at temp paths."""
    tmp = tempfile.TemporaryDirectory()
    state = tmp.name + "/state.json"
    os.environ["DAILY_QUESTION_STATE_PATH"] = state
    if questions_path:
        os.environ["DAILY_QUESTIONS_PATH"] = str(questions_path)
    else:
        os.environ.pop("DAILY_QUESTIONS_PATH", None)
    spec = importlib.util.spec_from_file_location(
        "post_daily_question", ROOT / "scripts" / "post_daily_question.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._tmp_cleanup = tmp  # keep dir alive
    return module, Path(state)


class RotationTests(unittest.TestCase):
    def setUp(self):
        os.environ["CHANNEL_LANGUAGE"] = "en-US"
        self.dq, self.state = _load_module(None)

    def test_rotation_is_deterministic_and_wraps(self):
        questions = ["q0", "q1", "q2"]
        d0 = date(2026, 7, 23)
        idx0, q0 = self.dq.pick_question(questions, d0)
        idx1, q1 = self.dq.pick_question(questions, d0 + timedelta(days=1))
        self.assertNotEqual(idx0, idx1)
        # wraps around the list length
        idxN, _ = self.dq.pick_question(questions, d0 + timedelta(days=3))
        self.assertEqual(idxN, idx0)

    def test_all_questions_have_content(self):
        bank_path = ROOT / "data" / "daily_questions.json"
        bank = json.loads(bank_path.read_text(encoding="utf-8"))
        for lang, entries in bank.items():
            self.assertGreaterEqual(len(entries), 14, f"{lang} needs >=14 entries (2-week rotation)")
            for entry in entries:
                self.assertTrue(entry.strip().endswith("?") or entry.strip()[-1] in "?!.",
                                f"{lang} entry is not phrased as a question: {entry[:60]}")


class LanguageSelectionTests(unittest.TestCase):
    def test_french_channel_gets_french_questions(self):
        os.environ["CHANNEL_LANGUAGE"] = "fr-FR"
        dq, _ = _load_module(None)
        idx, question = self.dq_pick(dq)
        self.assertTrue(any(fr_word in question for fr_word in ("vous", "pourquoi", "quel", "quoi")))
        os.environ["CHANNEL_LANGUAGE"] = "en-US"

    dq_pick = lambda self, dq: dq.pick_question(dq.load_questions(), date(2026, 7, 23))


class IdempotencyTests(unittest.TestCase):
    def setUp(self):
        os.environ["CHANNEL_LANGUAGE"] = "en-US"
        self.dq, self.state = _load_module(None)

    def test_second_run_same_day_is_skipped(self):
        today = date.today()
        self.assertFalse(self.dq.already_posted(self.state, today))
        self.dq.mark_posted(self.state, today, 3, {"youtube": {"comment_id": "x"}})
        self.assertTrue(self.dq.already_posted(self.state, today))
        self.assertFalse(self.dq.already_posted(self.state, today + timedelta(days=1)))

    def test_missing_state_file_means_not_posted(self):
        self.assertFalse(self.dq.already_posted(Path("/nonexistent/state.json"), date.today()))


class FacebookPayloadTests(unittest.TestCase):
    def test_question_post_has_no_engagement_bait(self):
        # 'comment YES if', 'tag a friend', 'like this' = demoted by Meta.
        os.environ["CHANNEL_LANGUAGE"] = "en-US"
        dq, _ = _load_module(None)
        excerpt = dq._FB_SUFFIX["en"]
        for bait in ("like this", "tag a friend", "comment yes", "share this"):
            self.assertNotIn(bait, excerpt.lower())


if __name__ == "__main__":
    unittest.main()
