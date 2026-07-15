"""
French quality and policy gate for SKILLOR.

Purpose:
- keep every public-facing field French-first
- block risky medical/YMYL claims before video generation/upload
- enforce Shorts-friendly metadata and scene structure

This gate cannot guarantee virality, but it prevents the most common reasons
faceless health/science Shorts get low trust signals: mixed language, repeated
metadata, exaggerated medical claims, weak structure, and unreadable captions.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

FRENCH_MARKERS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "ce", "cet", "cette",
    "ton", "ta", "tes", "tu", "toi", "te", "se", "son", "sa", "ses", "dans",
    "pour", "avec", "sans", "mais", "et", "ou", "donc", "car", "quand", "comme",
    "pourquoi", "voici", "vraiment", "corps", "cerveau", "sommeil", "cœur",
    "santé", "mémoire", "stress", "ventre", "microbiote", "après", "nuit", "science", "secret",
}

ENGLISH_MARKERS = {
    "your", "you", "the", "this", "that", "why", "how", "what", "when", "body",
    "brain", "heart", "sleep", "blood", "health", "truth", "doctors",
    "actually", "never", "always", "people",
}

# Hard blocks: medical diagnosis/cure/guarantee language.
FORBIDDEN_MEDICAL_PATTERNS = [
    r"\bgu[eé]rit\b", r"\bgu[eé]rison garantie\b", r"\brem[eè]de miracle\b",
    r"\bdiagnostique\b", r"\btu as (un|une|la|le)\b", r"\btu souffres de\b",
    r"\barr[eê]te (ton|tes|le|la) traitement\b", r"\bremplace ton traitement\b",
    r"\bpas besoin de m[eé]decin\b", r"\bignore ton m[eé]decin\b",
    r"\b100\s*%\s*(garanti|efficace|vrai)\b", r"\bpreuve absolue\b",
    # English slips
    r"\bcures?\b", r"\bdiagnos(e|is)\b", r"\bguaranteed\b", r"\bdoctor[s]? don't want\b",
]

SAFE_DISCLAIMER = (
    "Contenu éducatif, pas un avis médical. Si un symptôme persiste, parle à un professionnel de santé."
)


def _all_public_text(script_data: Dict) -> str:
    parts: List[str] = []
    for key in ("title", "hook", "cta", "description", "topic"):
        if script_data.get(key):
            parts.append(str(script_data[key]))
    for scene in script_data.get("scenes", []) or []:
        if isinstance(scene, dict):
            parts.append(str(scene.get("caption", "")))
            parts.append(str(scene.get("visual", "")))
    for seq_key in ("tags", "hashtags"):
        val = script_data.get(seq_key)
        if isinstance(val, list):
            parts.extend(map(str, val))
    return "\n".join(parts)


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ']+", text.lower())


def language_score(text: str) -> Dict:
    tokens = _tokens(text)
    if not tokens:
        return {"french_hits": 0, "english_hits": 0, "english_ratio": 0.0, "ok": False}
    french_hits = sum(1 for t in tokens if t in FRENCH_MARKERS)
    english_hits = sum(1 for t in tokens if t in ENGLISH_MARKERS)
    english_ratio = english_hits / max(len(tokens), 1)
    # French text can include universal words like science/shorts; allow small ratio.
    ok = french_hits >= 8 and english_ratio <= 0.035
    return {
        "french_hits": french_hits,
        "english_hits": english_hits,
        "english_ratio": round(english_ratio, 4),
        "ok": ok,
    }


def medical_policy_flags(text: str) -> List[str]:
    flags: List[str] = []
    lowered = text.lower()
    for pat in FORBIDDEN_MEDICAL_PATTERNS:
        if re.search(pat, lowered, flags=re.IGNORECASE):
            flags.append(pat)
    return flags


def ensure_safe_disclaimer(script_data: Dict) -> Dict:
    desc = script_data.get("description", "") or ""
    cta = script_data.get("cta", "") or ""
    if SAFE_DISCLAIMER.lower() not in (desc + " " + cta).lower():
        script_data["description"] = (desc.strip() + "\n\n" + SAFE_DISCLAIMER).strip()
        script_data["safety_disclaimer_added"] = True
    return script_data


def validate_publication_quality(script_data: Dict) -> Tuple[bool, Dict]:
    """Return (ok, report). Does not mutate except adding a safe disclaimer."""
    issues: List[str] = []
    warnings: List[str] = []

    scenes = script_data.get("scenes", []) or []
    if not (8 <= len(scenes) <= 12):
        issues.append(f"Scene count should be 8-12 for Shorts; got {len(scenes)}")

    for i, scene in enumerate(scenes, start=1):
        caption = scene.get("caption", "") if isinstance(scene, dict) else ""
        wc = len(caption.split())
        if wc < 8 or wc > 24:
            warnings.append(f"Scene {i} caption has {wc} words; target 12-20")

    title = script_data.get("title", "") or ""
    if len(title) > 70:
        warnings.append("Title is longer than 70 chars; mobile truncation risk")
    if title.isupper() and len(title) > 10:
        issues.append("Title is all caps; spam/clickbait risk")

    text = _all_public_text(script_data)
    lang = language_score(text)
    if not lang["ok"]:
        issues.append(
            f"French language gate failed: french_hits={lang['french_hits']}, "
            f"english_ratio={lang['english_ratio']}"
        )

    med_flags = medical_policy_flags(text)
    if med_flags:
        issues.append("Risky medical/guarantee language detected: " + ", ".join(med_flags[:5]))

    # Always add educational disclaimer for body/health science content.
    ensure_safe_disclaimer(script_data)

    report = {
        "approved": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "language": lang,
        "medical_flags": med_flags,
        "disclaimer": SAFE_DISCLAIMER,
    }

    if report["approved"]:
        logger.info("French quality gate approved publication")
    else:
        logger.error(f"French quality gate blocked publication: {issues}")

    return report["approved"], report
