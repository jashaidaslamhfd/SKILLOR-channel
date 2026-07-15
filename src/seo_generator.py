"""
src/seo_generator.py

PRD "AI SEO Generator" feature, adapted to SKILLOR's dark-facts Shorts niche.
Pure post-processing on top of an already-generated script_data dict — no
extra LLM calls, so it's free and instant to run for every video.

Produces:
  - title_options: 5 SEO-friendly title variants (different hook angles)
  - description: CTR-optimized YouTube description (reuses the same shape
    uploader.py already builds, factored out here so it's the single
    source of truth)
  - hashtags: deduplicated, ranked hashtag list
  - pinned_comment: a comment worth auto-pinning post-upload to seed
    engagement (main.py/uploader.py can pin it via commentThreads.insert)
  - playlist_suggestion: which existing playlist this video best fits
  - seo_score: 0-100 with a breakdown, so low-scoring videos can be
    flagged the same way quality_checker flags weak scripts

Nothing here calls the network or an LLM - it's deterministic string/rule
based scoring, matching the pattern already used in quality_checker.py and
anti_spam.py.
"""

import re
import unicodedata
import logging
from typing import Dict, List

from niche_strategy import generate_seo_tags, _make_seo_title, get_topic_category

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TITLE_MAX_LEN = 70          # YouTube truncates further titles in search UI
DESCRIPTION_MAX_LEN = 5000  # YouTube hard limit
PINNED_COMMENT_MAX_LEN = 200

# Existing playlists this channel maintains (edit to match your real
# playlist names/IDs - used only for suggestion text, not an API call).
PLAYLISTS_BY_CATEGORY = {
    "Brain": "Faits Sombres sur le Cerveau",
    "Body": "Faits Sombres sur le Corps",
    "Mystery": "Mystères du Corps",
    "Health": "Shorts Santé & Science",
}

_TITLE_TEMPLATES = [
    "{topic}",
    "Ce Que Cache {topic}",
    "La Science Derrière {topic}",
    "Pourquoi {topic} Arrive Vraiment",
    "{topic}... Ton Corps Le Fait Déjà",
]


def _clean_topic_for_title(topic: str) -> str:
    """Templates like 'The Truth About Why Your Heart Skips a Beat' read
    awkwardly - strip a leading 'Why'/'The' so templated titles stay
    grammatical. Deliberately does NOT strip a leading 'Your' - personal
    'YOU language' is a core retention technique used throughout this
    codebase (see niche_strategy/script_generator), so dropping it here
    would silently undo that for any templated title that wins on score."""
    t = topic.strip()
    t = re.sub(r'^(why|the|pourquoi|le|la|les)\s+', '', t, flags=re.IGNORECASE)
    return t[0].upper() + t[1:] if t else topic


def generate_title_options(topic: str, script_data: Dict, n: int = 5) -> List[str]:
    """Returns up to n distinct SEO-friendly title variants for the same
    video. First option is always the enhanced original AI title (already
    proven in production via niche_strategy._make_seo_title); the rest are
    template-driven alternates so there's real angle diversity, not just
    punctuation changes."""
    base_title = script_data.get('title') or topic
    options = [_make_seo_title(base_title, topic)]

    clean_topic = _clean_topic_for_title(topic)
    seen = {options[0].lower()}
    for template in _TITLE_TEMPLATES:
        if len(options) >= n:
            break
        candidate = template.format(topic=clean_topic)[:TITLE_MAX_LEN]
        if candidate.lower() not in seen:
            options.append(candidate)
            seen.add(candidate.lower())

    return options[:n]


def _to_hashtag(tag: str) -> str:
    """Convert a YouTube tag/phrase into one valid hashtag token.
    Spaces and punctuation break hashtags, so we slugify phrases while
    keeping French letters readable when possible.
    """
    tag = str(tag or '').strip().lstrip('#')
    tag = unicodedata.normalize('NFKD', tag).encode('ascii', 'ignore').decode('ascii')
    tag = re.sub(r'[^A-Za-z0-9]+', '', tag)
    return f"#{tag}" if tag else ""


def generate_hashtags(topic: str, category: str, n: int = 8) -> List[str]:
    """Wraps niche_strategy.generate_seo_tags() into ready-to-use hashtags,
    ranked broad-first (helps discovery) then niche-specific (helps
    relevance). Capped at n since YouTube only surfaces the first few
    hashtags above the title anyway, and Shorts specifically rewards a
    tight, relevant set over a long list."""
    tags = generate_seo_tags(topic, category)
    result = []
    for tag in tags:
        ht = _to_hashtag(tag)
        if ht and ht.lower() not in (x.lower() for x in result):
            result.append(ht)
        if len(result) >= n:
            break
    return result


def generate_description(script_data: Dict, tags: List[str]) -> str:
    """Same structure as uploader._build_youtube_description, factored out
    here so SEO generation and upload share one implementation instead of
    drifting apart. uploader.py should import this going forward."""
    title = script_data.get('title', '')
    hook = script_data.get('hook', '')
    cta = script_data.get('cta', 'Abonne-toi pour plus de secrets sombres sur le corps.')
    description = script_data.get('description', '')

    first_line = hook[:120] if hook else title
    yt_hashtags = ' '.join(_to_hashtag(t) for t in tags[:3] if _to_hashtag(t))

    return (
        f"{first_line}\n\n"
        f"{description}\n\n"
        f"👇 {cta}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔬 Science sombre du corps, expliquée simplement\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{yt_hashtags}"
    )[:DESCRIPTION_MAX_LEN]


def generate_pinned_comment(script_data: Dict) -> str:
    """A short comment worth pinning right after upload to seed the first
    reply/engagement signal. Keep it a genuine question or prompt - not an
    engagement-bait command like 'like if you agree', which YouTube's spam
    systems increasingly downrank."""
    topic = script_data.get('topic', script_data.get('title', 'ça'))
    comment = f"Tu savais ça sur {topic.lower()} ? Dis-moi ce qui t'a le plus surpris 👇"
    return comment[:PINNED_COMMENT_MAX_LEN]


def suggest_playlist(category: str) -> str:
    return PLAYLISTS_BY_CATEGORY.get(category, "Dark Body Facts")


def _score_title(title: str) -> int:
    """0-100. Rewards length in the sweet spot, a power word, and presence
    of a number - all correlate with higher Shorts CTR without tipping into
    all-caps/clickbait territory that risks a policy strike."""
    if not title:
        return 0
    score = 40
    length = len(title)
    if 30 <= length <= 60:
        score += 25
    elif length < 30:
        score += 10
    else:
        score += 5  # over 60 chars risks truncation in search results

    power_words = ['secret', 'hidden', 'why', 'this',
                   'vérité', 'réel', 'caché', 'pourquoi', 'vraiment', 'secrets',
                   'science', 'corps', 'cerveau', 'sommeil', 'stress']
    if any(w in title.lower() for w in power_words):
        score += 20

    if re.search(r'\d', title):
        score += 10

    if title.isupper():
        score -= 15  # reads as spam/clickbait, hurts rather than helps

    return max(0, min(score, 100))


def _score_description(description: str, hook: str) -> int:
    """0-100. Rewards putting the hook in the visible first ~125 chars
    (before YouTube's 'Show more' cutoff) and including hashtags."""
    if not description:
        return 0
    score = 30
    if hook and hook[:60].lower() in description[:150].lower():
        score += 30
    if '#' in description:
        score += 20
    length = len(description)
    if 150 <= length <= 1000:
        score += 20
    elif length > 0:
        score += 10
    return max(0, min(score, 100))


def _score_tags(tags: List[str]) -> int:
    """0-100. Rewards having enough tags for reach without over-stuffing
    (YouTube ignores tags past a certain total character budget, and
    excessive tagging is itself a spam-flag risk anti_spam.py watches for)."""
    if not tags:
        return 0
    count = len(tags)
    if 8 <= count <= 15:
        score = 90
    elif count < 8:
        score = 50 + count * 5
    else:
        score = max(40, 90 - (count - 15) * 5)

    unique_ratio = len(set(t.lower() for t in tags)) / count
    score = int(score * unique_ratio)
    return max(0, min(score, 100))


def calculate_seo_score(title: str, description: str, tags: List[str], script_data: Dict) -> Dict:
    """Overall 0-100 SEO score plus a per-component breakdown, mirroring
    the shape quality_checker.check_script_quality() returns so both can be
    logged/displayed the same way in main.py."""
    hook = script_data.get('hook', '')
    components = {
        'title_score': _score_title(title),
        'description_score': _score_description(description, hook),
        'tags_score': _score_tags(tags),
    }
    overall = round(sum(components.values()) / len(components))
    components['overall_seo_score'] = overall

    if overall >= 85:
        rating = "🟢 EXCELLENT"
    elif overall >= 70:
        rating = "🟡 GOOD"
    elif overall >= 50:
        rating = "🟠 NEEDS WORK"
    else:
        rating = "🔴 POOR"

    return {'scores': components, 'rating': rating}


def generate_seo_package(topic: str, script_data: Dict) -> Dict:
    """Single entry point main.py can call once per video. Returns
    everything the PRD's 'AI SEO Generator' section asks for, scoped to
    what actually applies to a YouTube Short (chapters are skipped - not
    supported on sub-60s videos)."""
    category = get_topic_category(topic)
    tags = generate_seo_tags(topic, category, script_data.get('title', ''))
    title_options = generate_title_options(topic, script_data)
    # Score every candidate and pick the best-scoring one instead of
    # always taking title_options[0] - the score was previously computed
    # only for logging and never actually influenced which title got
    # used, so a weak title could ship even when a stronger option was
    # sitting right there in the list.
    chosen_title = max(title_options, key=_score_title) if title_options else script_data.get('title', 'Sans titre')
    description = generate_description(script_data, tags)
    hashtags = generate_hashtags(topic, category)
    pinned_comment = generate_pinned_comment(script_data)
    playlist = suggest_playlist(category)
    seo_score = calculate_seo_score(chosen_title, description, tags, script_data)

    logger.info(f"SEO package built for '{topic}' - score: {seo_score['scores']['overall_seo_score']}/100 ({seo_score['rating']})")

    return {
        'title_options': title_options,
        'chosen_title': chosen_title,
        'description': description,
        'tags': tags,
        'hashtags': hashtags,
        'pinned_comment': pinned_comment,
        'playlist_suggestion': playlist,
        'seo_score': seo_score,
    }


if __name__ == "__main__":
    import json
    test_script = {
        'title': 'Your Heart Has Its Own Brain',
        'hook': "Doctors don't want you to know this about your heart...",
        'cta': 'Abonne-toi pour plus de science sombre du corps',
        'description': 'Your heart contains its own independent nervous system.',
    }
    result = generate_seo_package("Your Heart Has Its Own Brain", test_script)
    print(json.dumps(result, indent=2, ensure_ascii=False))
