"""
src/shorts_enhancer.py

PRD "Shorts Generator" feature. SKILLOR already produces Shorts-only videos
(video_editor.py hardcodes a 1080x1920 canvas and 40-55s target), so the
"convert a long video into Shorts" part of the PRD doesn't apply here.
What DOES apply and add value on top of the existing pipeline:

  - A finer-grained hook score with concrete fix suggestions (quality_checker
    already scores the hook 0-100 for the approve/reject gate; this module
    explains *why* and *what to change*, so a human reviewing a low-scoring
    video knows what to fix instead of just seeing a number)
  - Per-scene caption pacing check (words-per-second) - a scene can pass
    quality_checker's overall pacing check while still having one scene
    that flashes by unreadably fast or drags
  - Shorts-specific hashtag set (#shorts is close to mandatory for Shorts
    surfacing - separate from the general SEO tags in seo_generator.py)
  - SRT subtitle file export from the exact per-scene audio durations
    video_editor.py already computes - lets you upload real closed
    captions (accessibility + a documented small SEO/reach benefit),
    reusing timing that's otherwise only baked into burned-in captions
"""

import os
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Readable range for on-screen word-by-word captions. Below this, text
# flashes by too fast to read; above this, it drags and viewers swipe away.
MIN_WORDS_PER_SEC = 1.5
MAX_WORDS_PER_SEC = 3.5

SHORTS_HASHTAGS = ["#shorts", "#youtubeshorts", "#short"]


# ---------------------------------------------------------------------------
# Hook scoring with actionable feedback
# ---------------------------------------------------------------------------

_CURIOSITY_TRIGGERS = [
    "don't know", "doesn't know", "myth", "truth", "shocking",
    "secret", "discovered", "most people", "never knew",
]
_POWER_WORDS = [
    "proven", "science", "expert", "revealed", "breakthrough",
    "hidden", "trick", "hack", "amazing", "incredible",
]


def score_hook_detailed(hook: str) -> Dict:
    """Same scoring logic as quality_checker._score_hook, but returns which
    checks passed/failed and a concrete suggestion for each miss, instead
    of a single collapsed number. Meant for a human reviewing why a video
    scored low, not for the automated approve/reject gate (that stays in
    quality_checker.py so there's one source of truth for the pass/fail
    threshold)."""
    checks = []
    score = 0

    if not hook or len(hook) < 10:
        return {
            'score': 0,
            'checks': [{'name': 'length', 'passed': False,
                        'note': 'Hook missing or too short - needs at least a full sentence.'}],
        }

    score += 50
    has_question = '?' in hook
    checks.append({
        'name': 'question_format', 'passed': has_question,
        'note': 'Questions pull viewers in during the first 3 seconds.' if has_question
                else 'Consider rephrasing as a question to raise curiosity.',
    })
    if has_question:
        score += 15

    has_curiosity = any(t in hook.lower() for t in _CURIOSITY_TRIGGERS)
    checks.append({
        'name': 'curiosity_gap', 'passed': has_curiosity,
        'note': 'Good curiosity-gap phrasing.' if has_curiosity
                else f"Add a curiosity trigger, e.g. one of: {', '.join(_CURIOSITY_TRIGGERS[:4])}.",
    })
    if has_curiosity:
        score += 20

    has_power_word = any(w in hook.lower() for w in _POWER_WORDS)
    checks.append({
        'name': 'power_word', 'passed': has_power_word,
        'note': 'Good use of a power word.' if has_power_word
                else f"Add a power word, e.g. one of: {', '.join(_POWER_WORDS[:4])}.",
    })
    if has_power_word:
        score += 15

    word_count = len(hook.split())
    length_ok = 8 <= word_count <= 15
    checks.append({
        'name': 'length_8_to_15_words', 'passed': length_ok,
        'note': f"{word_count} words is in the ideal range." if length_ok
                else f"{word_count} words - {'too short, expand it a bit' if word_count < 8 else 'a bit long, tighten it'}.",
    })
    score += 10 if length_ok else (-10 if word_count < 8 else 0)

    return {'score': max(0, min(score, 100)), 'checks': checks}


# ---------------------------------------------------------------------------
# Per-scene caption pacing
# ---------------------------------------------------------------------------

def check_caption_pacing(scenes: List[Dict], audio_segments: List[Dict]) -> Dict:
    """Flags any individual scene whose words-per-second falls outside the
    readable range, even if the video's overall pacing (checked in
    quality_checker) looks fine on average. audio_segments come from
    voice_generator.generate_voice_segments() and carry the real spoken
    duration per scene."""
    issues = []
    per_scene = []

    for i, (scene, seg) in enumerate(zip(scenes, audio_segments)):
        caption = scene.get('caption', '')
        duration = max(seg.get('duration', 0), 0.01)
        word_count = len(caption.split())
        wps = word_count / duration

        status = "ok"
        if wps < MIN_WORDS_PER_SEC:
            status = "too_slow"
            issues.append(f"Scene {i+1}: {wps:.1f} words/sec - dragging, consider trimming the caption or shortening the scene.")
        elif wps > MAX_WORDS_PER_SEC:
            status = "too_fast"
            issues.append(f"Scene {i+1}: {wps:.1f} words/sec - too fast to read, consider splitting into two scenes.")

        per_scene.append({'scene': i + 1, 'words_per_sec': round(wps, 2), 'status': status})

    return {
        'per_scene': per_scene,
        'issues': issues,
        'all_readable': len(issues) == 0,
    }


# ---------------------------------------------------------------------------
# Shorts hashtags
# ---------------------------------------------------------------------------

def generate_shorts_hashtags(topic_tags: List[str], n: int = 5) -> List[str]:
    """#shorts-family tags first (near-mandatory for Shorts shelf
    placement), then the top niche tags already computed by
    seo_generator/niche_strategy - avoids re-deriving tags from scratch."""
    result = list(SHORTS_HASHTAGS)
    for t in topic_tags:
        tag = f"#{t}" if not t.startswith('#') else t
        if tag.lower() not in (x.lower() for x in result):
            result.append(tag)
        if len(result) >= n:
            break
    return result[:n]


# ---------------------------------------------------------------------------
# SRT subtitle export
# ---------------------------------------------------------------------------

def _seconds_to_srt_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(scenes: List[Dict], audio_segments: List[Dict], output_path: str = None) -> str:
    """Builds standard SRT subtitle content from each scene's caption and
    its real audio duration (same timing source video_editor.py uses for
    burned-in captions, so the uploaded closed-caption file matches what's
    on screen). Writes to output_path if given, always returns the SRT
    text either way."""
    lines = []
    t = 0.0
    for i, (scene, seg) in enumerate(zip(scenes, audio_segments), start=1):
        duration = max(seg.get('duration', 0), 0.6)
        start, end = t, t + duration
        lines.append(str(i))
        lines.append(f"{_seconds_to_srt_timestamp(start)} --> {_seconds_to_srt_timestamp(end)}")
        lines.append(scene.get('caption', '').strip())
        lines.append("")
        t = end

    srt_content = "\n".join(lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        logger.info(f"SRT subtitles written to {output_path}")

    return srt_content


# ---------------------------------------------------------------------------
# Combined report
# ---------------------------------------------------------------------------

def build_shorts_report(script_data: Dict, audio_segments: List[Dict], topic_tags: List[str]) -> Dict:
    """Single entry point main.py can call alongside quality_checker /
    anti_spam. Doesn't gate publishing on its own (quality_checker already
    owns the approve/reject decision) - this is diagnostic + asset output."""
    hook_detail = score_hook_detailed(script_data.get('hook', ''))
    pacing = check_caption_pacing(script_data.get('scenes', []), audio_segments)
    hashtags = generate_shorts_hashtags(topic_tags)

    return {
        'hook_detail': hook_detail,
        'caption_pacing': pacing,
        'shorts_hashtags': hashtags,
    }


if __name__ == "__main__":
    import json
    test_scenes = [
        {"visual": "human heart beating", "caption": "Your heart has its own brain."},
        {"visual": "close up neurons", "caption": "It contains over 40000 neurons that operate independently of your actual brain."},
    ]
    test_segments = [{"duration": 2.0}, {"duration": 3.0}]
    report = build_shorts_report(
        {"hook": "Doctors don't want you to know this about your heart...", "scenes": test_scenes},
        test_segments,
        ["darkfacts", "heartfacts", "science"],
    )
    print(json.dumps(report, indent=2))
    print(generate_srt(test_scenes, test_segments))
