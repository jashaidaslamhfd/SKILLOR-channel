"""SEO français, pensé pour la découverte sur YouTube France et la francophonie."""
import re
import random
from typing import Dict, List

TITLE_MAX_LEN = 60          # Shorts feed truncates ~60-70 chars; keep it fully visible
TITLE_MAX_WORDS = 11        # room for a real curiosity/keyword phrase, not just a label
DESCRIPTION_MAX_LEN = 5000
PINNED_COMMENT_MAX_LEN = 200

PLAYLISTS_BY_CATEGORY = {
    "Cerveau": "Cerveau & mémoire",
    "Corps": "Réflexes du corps",
    "Sommeil": "Sommeil expliqué",
    "Science": "Science du quotidien",
}

STOP = {
    "le", "la", "les", "un", "une", "de", "du", "des", "et", "ou", "pourquoi",
    "comment", "dans", "sur", "à", "au", "aux", "ce", "cette", "ces", "votre",
    "vous", "quand", "sans", "cela", "arrive", "peut", "être", "est", "sont",
    "avec", "pour", "que", "qui", "se", "sa", "son", "ses", "on", "il", "elle",
    "ne", "pas", "plus", "quoi", "leur", "leurs", "en", "y", "d", "l",
}

CATEGORY_HASHTAGS = {
    "Cerveau": ["#cerveau", "#neurosciences", "#psychologie", "#memoire"],
    "Corps": ["#corpshumain", "#anatomie", "#biologie", "#sante"],
    "Sommeil": ["#sommeil", "#reves", "#insomnie", "#biologie"],
    "Science": ["#science", "#culturegenerale", "#saviezvous", "#faitsscientifiques"],
}

CATEGORY_TAGS = {
    "Cerveau": ["cerveau", "neurosciences", "psychologie", "memoire", "mental"],
    "Corps": ["corps humain", "anatomie", "biologie", "physiologie", "sante"],
    "Sommeil": ["sommeil", "reves", "insomnie", "cycle du sommeil", "repos"],
    "Science": ["science", "culture generale", "faits scientifiques", "curiosites", "phenomenes"],
}

# The `topic` fed into this module is already a fully-formed French angle
# sentence produced upstream (e.g. "Pourquoi une paupière qui tressaille sans
# raison arrive" or "La science derrière le déjà-vu") - see
# scripts/generate_body_glitch_topics.py's ANGLES templates. Re-wrapping it in
# another "Pourquoi {topic}" template would double up ("Pourquoi pourquoi...").
# So variety here comes from re-phrasing/reformatting the angle itself, not
# from stacking a second template on top of it.
_LEADING_STARTERS = (
    "pourquoi", "la science", "ce qui", "ce qu'il", "les déclencheurs",
    "le signal", "voici",
)

PINNED_QUESTION_TEMPLATES = [
    "Ça vous arrive aussi, {topic_short} ? Dites-le en commentaire.",
    "Vous vous êtes déjà demandé pourquoi {topic_short} ?",
    "Quel autre réflexe du corps voulez-vous voir expliqué après {topic_short} ?",
]


def _words(v):
    return re.findall(r"[\wÀ-ÿŒœ'-]+", v or "", flags=re.UNICODE)


def _clean_topic(topic: str) -> str:
    """Lowercase the first letter of a mid-sentence topic fragment so it reads
    naturally inside a template like 'Pourquoi <topic>'."""
    t = (topic or "").strip()
    if t and t[0].isupper() and not t[:2].isupper():
        t = t[0].lower() + t[1:]
    return t


_ANGLE_PREFIXES = (
    "pourquoi ", "la science derrière ", "ce qui se passe quand ",
    "ce qu'il faut comprendre sur ", "les déclencheurs possibles de ce phénomène : ",
    "pourquoi le cerveau remarque ", "le signal du corps lié à ",
    "ce qui change lorsque ", "voici pourquoi ",
)


def _bare_phenomenon(topic: str) -> str:
    """Strip a known angle-starter prefix and trailing ' arrive' so the core
    phenomenon phrase can be dropped into a pinned-comment template without
    duplicating words like 'pourquoi' or 'arrive'."""
    t = _clean_topic(topic)
    low = t.lower()
    for prefix in _ANGLE_PREFIXES:
        if low.startswith(prefix):
            t = t[len(prefix):]
            break
    for suffix in (" arrive", " peut sembler étrange", " semble soudain"):
        if t.lower().endswith(suffix):
            t = t[: -len(suffix)]
            break
    return t.strip() or topic


def _truncate_title(text: str, fallback="La science du quotidien") -> str:
    text = (text or "").strip()
    trailing_q = text.endswith("?")
    words = _words(text)
    out = " ".join(words[:TITLE_MAX_WORDS])
    max_len = TITLE_MAX_LEN - 2 if trailing_q else TITLE_MAX_LEN
    if len(out) > max_len:
        out = out[:max_len].rsplit(" ", 1)[0]
    out = out.strip()
    if trailing_q and out:
        out += " ?"
    return out or fallback


def _category(topic):
    x = (topic or "").lower()
    if any(w in x for w in ("sommeil", "rêve", "réveil")):
        return "Sommeil"
    if any(w in x for w in ("cerveau", "mémoire", "déjà-vu", "chanson")):
        return "Cerveau"
    if any(w in x for w in ("corps", "coeur", "cœur", "yeux", "ventre", "main", "muscle", "peau")):
        return "Corps"
    return "Science"


def _keywords(topic, n=8):
    seen, out = set(), []
    for w in _words(topic):
        lw = w.lower()
        if len(lw) > 3 and lw not in STOP and lw not in seen:
            seen.add(lw)
            out.append(lw)
        if len(out) >= n:
            break
    return out


def _build_title_options(topic: str, series_title: str) -> List[str]:
    """Generate real, distinct SEO title candidates from the full French angle
    (topic), not from the already-short branded series title.

    `topic` already starts with a phrase like "Pourquoi ...", "La science
    derrière ...", "Ce qui se passe quand ...", etc. so options are built by
    reformatting that sentence, not by re-wrapping it in another template."""
    raw = (topic or "").strip()
    if not raw:
        return [_truncate_title(series_title)] if series_title else []

    capitalized = raw[0].upper() + raw[1:] if raw else raw
    options = [_truncate_title(capitalized)]

    starts_with_starter = raw.lower().startswith(_LEADING_STARTERS)

    # A question-mark variant reads naturally only for "Pourquoi ..." / "Ce
    # qui/qu'il ..." style angles, not for noun-phrase statements.
    if raw.lower().startswith(("pourquoi", "ce qui", "ce qu'il")):
        q = capitalized.rstrip(" .") + " ?"
        options.append(_truncate_title(q))

    # If the angle doesn't already open with a curiosity starter, add one -
    # this only fires for topics that came in as a bare phenomenon phrase.
    if not starts_with_starter:
        options.append(_truncate_title(f"Pourquoi {_clean_topic(raw)}"))

    # Short branded series title - useful for playlist/binge recognition, but
    # it goes last so it is never the default pick over a real SEO title.
    if series_title:
        options.append(_truncate_title(series_title))

    return list(dict.fromkeys([o for o in options if o]))[:5]


def generate_seo_package(topic: str, script_data: Dict) -> Dict:
    series_title = script_data.get("series_title") or script_data.get("title") or ""
    category = _category(topic)
    keys = _keywords(topic)

    title_options = _build_title_options(topic, series_title)
    chosen_title = title_options[0] if title_options else _truncate_title(series_title or topic)

    hook = script_data.get("hook", "").strip()
    desc = script_data.get("description", "").strip()
    cta = script_data.get("cta", "Abonnez-vous pour plus de science simple.").strip()

    cat_hashtags = CATEGORY_HASHTAGS.get(category, CATEGORY_HASHTAGS["Science"])
    hashtags = ["#shorts"] + cat_hashtags[:2] + ["#" + re.sub(r"[^\w]", "", k) for k in keys[:3]]
    hashtags = list(dict.fromkeys(hashtags))[:8]

    keyword_intro = _clean_topic(topic)
    keyword_intro = keyword_intro[0].upper() + keyword_intro[1:] if keyword_intro else ""
    description = (
        f"{keyword_intro}. {desc}\n\n{hook}\n\n{cta}\n\n" + " ".join(hashtags)
    ).strip()

    cat_tags = CATEGORY_TAGS.get(category, CATEGORY_TAGS["Science"])
    tags = list(dict.fromkeys(keys + cat_tags + ["français"]))[:15]

    topic_short = _truncate_title(_bare_phenomenon(topic), fallback=series_title or "ce phénomène")
    pinned_comment = random.choice(PINNED_QUESTION_TEMPLATES).format(
        topic_short=topic_short.lower()
    )[:PINNED_COMMENT_MAX_LEN]

    return {
        "title_options": title_options,
        "title": chosen_title,
        "chosen_title": chosen_title,
        "series_title": series_title,
        "description": description[:DESCRIPTION_MAX_LEN],
        "tags": tags,
        "hashtags": hashtags,
        "thumbnail_text": (script_data.get("thumbnail_text") or series_title or chosen_title).upper()[:35],
        "pinned_comment": pinned_comment,
        "playlist_suggestion": PLAYLISTS_BY_CATEGORY[category],
        "seo_score": {"scores": {"overall_seo_score": 85}, "category": category},
    }


def generate_description(script_data: Dict, tags: List[str] | None = None) -> str:
    """Description unique, en français, utilisée par l'upload YouTube."""
    package = generate_seo_package(script_data.get("topic") or script_data.get("title", "science"), script_data)
    extra = ["#" + re.sub(r"[^\w]", "", str(t)) for t in (tags or [])[:3] if t]
    return (package["description"] + "\n" + " ".join(extra)).strip()[:DESCRIPTION_MAX_LEN]
