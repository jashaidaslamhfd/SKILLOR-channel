#!/usr/bin/env python3
"""Daily engagement question — the LEGAL automation of the "1 poll/day" idea.

Why this exists (and what it deliberately is NOT):
- Community-tab polls have NO official YouTube API in 2026 (the only polls
  API covers live streams). Browser-automation hacks violate YouTube ToS,
  get accounts flagged, and store fragile super-cookies in secrets — so we
  do NOT do that.
- What IS API-legal and automatable: posting the daily question as a
  top-level channel COMMENT under the latest Short (Data API v3, scope
  youtube.force-ssl — already granted by this repo's REFRESH_TOKEN), and a
  question POST on the Facebook Page (Graph API, US channel only).
- Native polls stay manual: ~10 min every Sunday in YouTube Studio using
  docs' poll bank (Studio has a Schedule button).

Idempotent: data/daily_question_state.json records the calendar date of the
last successful post, so duplicate crons (DST pairs) and manual re-runs can
never double-post.
"""

import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("daily_question")

QUESTIONS_PATH = Path(os.environ.get("DAILY_QUESTIONS_PATH", "data/daily_questions.json"))
STATE_PATH = Path(os.environ.get("DAILY_QUESTION_STATE_PATH", "data/daily_question_state.json"))
HISTORY_PATH = Path(os.environ.get("VIDEO_HISTORY_PATH", "data/video_history.json"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
FB_API_VERSION = os.environ.get("FB_API_VERSION", "v23.0").strip()

LANG = os.environ.get("CHANNEL_LANGUAGE", "en-US").strip().lower()
LANG_KEY = "fr" if LANG.startswith("fr") else "en"
_PREFIX = {"en": "Question of the day 🧠 ", "fr": "Question du jour 🧠 "}
_FB_SUFFIX = {"en": "\n\nDrop your answer below 👇", "fr": "\n\nRépondez en commentaire 👇"}


def load_questions(path: Path = QUESTIONS_PATH) -> list:
    bank = json.loads(path.read_text(encoding="utf-8"))
    questions = bank.get(LANG_KEY) or bank["en"]
    if not questions:
        raise RuntimeError(f"Question bank has no entries for {LANG_KEY!r}")
    return questions


def pick_question(questions: list, day: date) -> tuple:
    """Deterministic daily rotation — same index on every machine for a
    given date (ordinal modulo), so re-runs and both repos agree."""
    idx = day.toordinal() % len(questions)
    return idx, questions[idx]


def already_posted(state_path: Path, day: date) -> bool:
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return state.get("last_posted_date") == day.isoformat()
    except (OSError, json.JSONDecodeError):
        return False


def mark_posted(state_path: Path, day: date, idx: int, targets: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp = state_path.with_suffix(state_path.suffix + ".tmp")
    temp.write_text(json.dumps({
        "last_posted_date": day.isoformat(),
        "question_index": idx,
        "targets": targets,
    }, indent=2), encoding="utf-8")
    os.replace(temp, state_path)


def _yt_client():
    import google.oauth2.credentials
    import google.auth.transport.requests
    from googleapiclient.discovery import build

    creds = google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=os.environ["REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
    )
    creds.refresh(google.auth.transport.requests.Request())
    return build("youtube", "v3", credentials=creds)


def recent_video_ids(history_path: Path = HISTORY_PATH, limit: int = 3) -> list:
    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    ids = [v.get("youtube_video_id") for v in reversed(history) if v.get("youtube_video_id")]
    return ids[:limit]


def post_youtube_comment(text: str, video_ids: list) -> dict:
    """Try newest videos first; succeeds on the first one that still exists
    and has comments enabled. Returns {'video_id': ..., 'comment_id': ...}."""
    yt = _yt_client()
    last_error = None
    for video_id in video_ids:
        try:
            response = yt.commentThreads().insert(
                part="snippet",
                body={"snippet": {
                    "videoId": video_id,
                    "topLevelComment": {"snippet": {"textOriginal": text}},
                }},
            ).execute()
            comment_id = response.get("id")
            logger.info("YouTube comment posted on %s: %s", video_id, comment_id)
            return {"video_id": video_id, "comment_id": comment_id}
        except Exception as exc:  # commentsDisabled / videoNotFound / etc.
            last_error = exc
            logger.warning("Comment failed on %s: %s", video_id, exc)
    if not video_ids:
        last_error = "no youtube_video_id found in video_history.json"
    raise RuntimeError(f"Could not post YouTube comment: {last_error}")


def post_facebook_question(text: str) -> dict:
    """US channel only — a question post on the Page feed. Meta rewards
    comments as 'meaningful interactions'; a genuine question is fine and
    is NOT engagement bait (which is explicit 'comment YES if…')."""
    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_ACCESS_TOKEN")
    if not page_id or not token:
        logger.info("FB secrets not set — skipping Facebook question post.")
        return {"skipped": True}
    message = text + _FB_SUFFIX[LANG_KEY]
    response = requests.post(
        f"https://graph.facebook.com/{FB_API_VERSION}/{page_id}/feed",
        data={"message": message, "access_token": token},
        timeout=30,
    )
    payload = response.json()
    if response.status_code != 200 or "error" in payload:
        raise RuntimeError(f"Facebook question post failed: {payload}")
    logger.info("Facebook question posted: %s", payload.get("id"))
    return {"post_id": payload.get("id")}


def main() -> int:
    today = date.today()
    if already_posted(STATE_PATH, today):
        logger.info("Already posted today (%s) — nothing to do.", today.isoformat())
        return 0
    questions = load_questions()
    idx, question = pick_question(questions, today)
    text = _PREFIX[LANG_KEY] + question
    logger.info("Today's question (%s #%d/%d): %s", LANG_KEY, idx + 1, len(questions), question)

    if DRY_RUN:
        logger.info("DRY_RUN=true — would post to YouTube %s and Facebook.", recent_video_ids()[:1])
        return 0

    targets = {}
    targets["youtube"] = post_youtube_comment(text, recent_video_ids())
    try:
        targets["facebook"] = post_facebook_question(text)
    except Exception as exc:  # FB must never take down the YT ritual
        logger.warning("Facebook question failed (YouTube already posted): %s", exc)
        targets["facebook"] = {"error": str(exc)}

    mark_posted(STATE_PATH, today, idx, targets)
    logger.info("Done. State committed as %s", STATE_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
