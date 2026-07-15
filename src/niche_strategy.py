"""
Niche Strategy Module for SKILLOR Pipeline
French-first niche: Science sombre du corps après 40 ans
Optimized for: retention, French metadata, safe health/science content.
"""

import logging
import os
import random
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ============================================
# 1. FRENCH DARK BODY / BRAIN / SLEEP TOPICS
# ============================================

DARK_TOPICS = [
    "Pourquoi tu te réveilles à 3h du matin",
    "Ce que ton cerveau fait pendant ton sommeil",
    "Ton cerveau se nettoie la nuit",
    "Pourquoi ta mémoire change après 40 ans",
    "Le stress laisse une trace dans ton corps",
    "Ton microbiote parle à ton cerveau",
    "Pourquoi ton ventre influence ton humeur",
    "Ce que les écrans font à ton sommeil",
    "Ton cœur réagit avant ton cerveau",
    "Pourquoi ton corps fatigue sans raison",
    "Le signal discret d'un cerveau épuisé",
    "Pourquoi tu oublies les prénoms si vite",
    "Ton cerveau déforme tes souvenirs",
    "Pourquoi le déjà-vu te paraît si réel",
    "Ce que la peur fait à ton corps en silence",
    "Pourquoi ton cœur s'emballe sans danger",
    "Le lien caché entre sommeil et mémoire",
    "Pourquoi ton corps sursaute quand tu t'endors",
    "Ce que ton corps prépare avant le réveil",
    "Pourquoi la lumière bleue piège ton cerveau",
    "Ton système nerveux a un mode alarme",
    "Pourquoi le stress bloque ta digestion",
    "Le rôle étrange du nerf vague",
    "Pourquoi respirer lentement calme le cerveau",
    "Ce que ton cœur révèle sur ton stress",
    "Pourquoi ton corps garde les tensions",
    "Le mystère des frissons sans froid",
    "Pourquoi tes mains deviennent froides sous stress",
    "Ce que ton sommeil dit de ton cerveau",
    "Pourquoi tu penses trop la nuit",
    "Ton cerveau trie tes émotions pendant le sommeil",
    "Pourquoi une mauvaise nuit te rend plus anxieux",
    "Ce que ton corps fait pendant le sommeil profond",
    "Pourquoi ton cerveau adore les routines",
    "Le danger silencieux du manque de sommeil",
    "Pourquoi tu te sens vidé après trop d'écran",
    "Ton attention est plus fragile que tu crois",
    "Pourquoi ton cerveau cherche toujours la nouveauté",
    "Ce que les notifications font à ton stress",
    "Pourquoi ton corps confond stress et menace",
    "Le signal que ton système nerveux est saturé",
    "Pourquoi ton cerveau préfère le négatif",
    "Ce que la solitude fait à ton corps",
    "Pourquoi ton cœur bat différemment la nuit",
    "Ton corps change après 40 ans en silence",
    "Pourquoi tu récupères moins vite qu'avant",
    "Le premier signe d'un métabolisme ralenti",
    "Pourquoi la fatigue mentale devient physique",
    "Ce que ton foie fait pendant que tu dors",
    "Pourquoi ton ventre gonfle sous stress",
    "Le microbiote et ton humeur sont liés",
    "Pourquoi ton intestin est appelé deuxième cerveau",
    "Ce que tes bactéries intestinales influencent",
    "Pourquoi ton sommeil dépend aussi de ton ventre",
    "Le lien caché entre inflammation et fatigue",
    "Pourquoi ton corps aime les horaires réguliers",
    "Ton horloge biologique contrôle plus que tu crois",
    "Pourquoi manger tard perturbe ton sommeil",
    "Ce que le cortisol fait le matin",
    "Pourquoi tu te réveilles fatigué malgré huit heures",
    "Ton cerveau manque parfois de vraie récupération",
    "Pourquoi les rêves paraissent si émotionnels",
    "Ce que les cauchemars révèlent sur le stress",
    "Pourquoi ton corps se bloque sous pression",
    "Le mécanisme étrange de la chair de poule",
    "Pourquoi tes muscles restent tendus sans raison",
    "Ce que la respiration change dans ton rythme cardiaque",
    "Pourquoi le silence aide ton cerveau",
    "Ton cerveau consomme énormément d'énergie",
    "Pourquoi la déshydratation brouille l'esprit",
    "Le lien entre sucre et fatigue mentale",
    "Pourquoi ton corps réclame du mouvement",
    "Ce que la marche fait à ton cerveau",
    "Pourquoi ton cœur a son propre système électrique",
    "Le secret des battements irréguliers occasionnels",
    "Pourquoi ton visage rougit sous émotion",
    "Ce que ton sang transporte en permanence",
    "Pourquoi tes vaisseaux réagissent au froid",
    "Ton système immunitaire apprend tous les jours",
    "Pourquoi ton corps se répare pendant la nuit",
    "Ce que la peau révèle sur le stress",
    "Pourquoi tes yeux fatiguent devant un écran",
    "Le clignement des yeux protège ton cerveau",
    "Pourquoi ton ouïe reste active pendant le sommeil",
    "Ce que ton corps entend avant ton esprit",
    "Pourquoi certaines odeurs déclenchent des souvenirs",
    "Ton cerveau relie odeurs et émotions",
    "Pourquoi ton corps tremble sous adrénaline",
    "Le signal caché derrière les palpitations de stress",
    "Pourquoi ton cerveau ralentit quand tu manques de sommeil",
    "Ce que la sieste courte fait vraiment",
    "Pourquoi ton corps aime la lumière du matin",
    "Le lien entre soleil et horloge interne",
    "Pourquoi ton cerveau déteste l'incertitude",
    "Ce que l'anxiété change dans ta respiration",
    "Pourquoi ton corps scanne le danger sans arrêt",
    "Le rôle discret du système lymphatique",
    "Pourquoi ton cerveau nettoie ses déchets la nuit",
    "Ce que ton âge change dans ton sommeil",
    "Pourquoi la mémoire émotionnelle reste plus forte",
    "Ton corps envoie des signaux avant la fatigue",
]

# ============================================
# 2. HOOK FORMULAS
# ============================================

HOOK_FORMULAS = [
    "Ton corps fait ça en silence... et tu ne le remarques presque jamais.",
    "Ce détail sur {topic} peut changer ta façon de voir ton corps.",
    "Tu crois connaître ton corps... mais {topic} cache une autre histoire.",
    "Personne ne t'explique {topic} comme ça, et pourtant c'est fascinant.",
    "Ce qui se passe dans ton corps est plus étrange que tu l'imagines.",
    "Si ça t'arrive, ton corps essaie peut-être de s'adapter...",
    "La science derrière {topic} est beaucoup plus surprenante qu'elle en a l'air.",
    "Ton cerveau te protège parfois d'une façon vraiment bizarre.",
    "Ce signal discret de ton corps passe souvent inaperçu...",
    "Après 40 ans, ton corps change doucement... mais pas au hasard.",
    "Ton sommeil révèle plus de choses que tu ne crois.",
    "Ton ventre et ton cerveau communiquent en permanence...",
    "Ton stress laisse parfois une empreinte physique très réelle.",
    "Le détail troublant, c'est que ton corps le fait avant même que tu comprennes.",
    "Voici pourquoi {topic} peut paraître banal... alors que ça ne l'est pas.",
]

TRANSITION_HOOKS = [
    "mais ce n'est que la moitié de l'histoire...",
    "et tu ne vas pas croire pourquoi...",
    "et c'est là que ça devient vraiment étrange...",
    "mais attends... il y a plus...",
    "et voici la partie que personne ne te dit...",
    "mais voici la partie choquante...",
    "et c'est là que ça devient sombre...",
    "mais ton corps a un secret...",
    "et ça change tout...",
    "mais la vraie raison va te surprendre...",
    "et ça devient encore plus étrange...",
    "mais voici le twist...",
]

PAIN_POINTS = [
    "S'inquiète que quelque chose ne va pas avec son corps",
    "N'arrive pas à dormir car son esprit ne s'arrête jamais",
    "Se sent anxieux face à des symptômes corporels aléatoires",
    "Remarque quelque chose sur son corps sans pouvoir l'expliquer",
    "A l'impression que son propre corps est un mystère",
    "A peur de symptômes qu'il ne comprend pas",
    "Se demande si ce qui lui arrive est normal",
    "Se sent déconnecté du fonctionnement de son propre corps",
    "Cherche ses symptômes sur Google tard le soir et panique",
    "A l'impression que personne n'explique ça clairement",
    "S'inquiète du vieillissement et de ce que ça signifie pour son corps",
    "Se sent impuissant quand son corps ne coopère pas",
    "Veut comprendre pourquoi son corps réagit différemment des autres",
    "A honte de fonctions corporelles qu'il ne peut pas contrôler",
    "Se demande si son corps fonctionne correctement",
]

CTAS = [
    "Abonne-toi pour plus de secrets sombres sur le corps",
    "Partage si ça t'a soufflé l'esprit",
    "Commente : ça t'est déjà arrivé ?",
    "Enregistre avant de l'oublier",
    "Abonne-toi si ton corps vient de te faire ça",
    "Identifie quelqu'un qui doit voir ça",
    "Commente 'pareil' si ça t'arrive aussi",
    "Partage à quelqu'un qui pense trop à tout",
    "Abonne-toi pour le prochain fait sombre sur le corps",
    "Envoie ça à l'ami toujours frigorifié, fatigué ou anxieux",
    "Mets un cœur si tu as appris un truc",
    "Commente si ça t'a choqué",
    "Enregistre pour impressionner quelqu'un avec des faits",
    "Partage pour faire réfléchir quelqu'un sur son corps",
    "Abonne-toi pour débloquer plus de mystères du corps",
]

# ============================================
# 3. SEO TAGS
# ============================================

CATEGORY_TAGS = {
    "Brain": [
        "cerveau", "neuroscience", "mémoire", "sommeil", "santeducerveau",
        "neuroplasticité", "concentration", "fatiguementale", "systemenerveux",
        "psychologie", "cerveauhumain", "shortsfrançais",
    ],
    "Body": [
        "corpshumain", "anatomie", "physiologie", "mystèresducorps", "sciencecorps",
        "santé", "bienêtre", "fatigue", "stress", "hormones", "cœur", "longévité",
    ],
    "Mystery": [
        "sciencesombre", "mystèresducorps", "faitsétranges", "faitsscientifiques",
        "secretsducorps", "inexpliqué", "curiosités", "faitsfrançais", "savoir",
    ],
    "Health": [
        "santé", "sommeil", "microbiote", "stress", "longévité", "bienêtre",
        "santéaprès40ans", "prévention", "équilibre", "rythmecircadien", "énergie",
    ],
}

BASE_TAGS = [
    "shorts", "youtubeshorts", "shortsfrançais", "science", "vulgarisation",
    "corpshumain", "cerveau", "sommeil", "stress", "microbiote", "longévité",
    "bienêtre", "santé", "faitsscientifiques", "sciencefrançaise",
]

TARGET_WORD_RANGE = (130, 170)
MAX_TAGS = 15
MAX_TITLE_LENGTH = 55
SCENES_PER_SCRIPT = 9

_MEDICAL_ADVICE_RED_FLAGS = [
    "guérit", "diagnostique", "tu as", "arrête de prendre", "pas besoin de médecin",
    "au lieu du médicament", "guérison garantie", "signifie forcément que tu as",
    "tu devrais", "tu dois", "ne va jamais chez le médecin", "ignore ton médecin",
    "c'est le seul remède", "meilleur que la médecine", "remplace ton traitement",
    "cure", "diagnose", "you have", "stop taking", "don't need a doctor",
]

# ============================================
# 4. PROMPT GENERATION
# ============================================

def get_script_prompt_for_niche(topic: str, hook_preference: Optional[str] = None) -> str:
    """Generate a retention-optimized French script prompt."""
    if not hook_preference:
        hook_preference = random.choice(HOOK_FORMULAS)
        if "{topic}" in hook_preference:
            hook_preference = hook_preference.format(topic=topic)

    pain_point = random.choice(PAIN_POINTS)
    cta = random.choice(CTAS)

    min_w, max_w = TARGET_WORD_RANGE
    num_scenes = SCENES_PER_SCRIPT
    per_scene_lo = min_w // num_scenes
    per_scene_hi = max_w // num_scenes
    transitions = random.sample(TRANSITION_HOOKS, min(5, len(TRANSITION_HOOKS)))

    prompt = f"""
Tu es un communicateur scientifique expert en mystères, spécialisé dans la création de YouTube Shorts À FORTE RÉTENTION en FRANÇAIS, pour un public adulte francophone 18+.

IMPORTANT :
- Tout le contenu public doit être en FRANÇAIS naturel et courant.
- N'écris jamais en anglais dans title, hook, captions, cta ou description.
- Contenu éducatif/divertissement uniquement : pas de diagnostic, pas de promesse de guérison, pas de conseil de traitement.
- Utilise un ton mystérieux, scientifique, sombre, mais responsable.

SUJET : {topic}

HOOK À UTILISER OU ADAPTER :
"{hook_preference}"

STRATÉGIE DE RÉTENTION :
- Chaque scène doit finir par un cliffhanger léger ou une tension.
- Utilise "tu", "ton", "ta", "tes" pour rendre le contenu personnel.
- Chaque scène doit durer 3 à 5 secondes de parole.
- Structure : curiosité > problème > révélation > boucle finale.
- Ne fais pas peur gratuitement : reste factuel et éducatif.

POINT DE DOULEUR :
{pain_point}

TRANSITIONS SUGGÉRÉES :
{', '.join(transitions)}

EXIGENCES STRICTES :
- Total voix off : {min_w}-{max_w} mots.
- Exactement {num_scenes} scènes.
- Caption de chaque scène : {per_scene_lo}-{per_scene_hi} mots.
- Phrases courtes, naturelles, conversationnelles.
- Aucun avis médical.
- Aucun anglais dans les textes publics.

VISUELS :
- "visual" doit décrire une image cinématographique verticale.
- Style : macro, sombre, contraste élevé, lumière dramatique, anatomie abstraite, science mystérieuse.
- Chaque visual doit être unique.

Retourne UNIQUEMENT du JSON valide :

{{
  "title": "Titre court et accrocheur EN FRANÇAIS",
  "hook": "Hook EN FRANÇAIS",
  "scenes": [
    {{"visual": "description visuelle cinématographique", "caption": "texte parlé EN FRANÇAIS"}}
  ],
  "cta": "CTA naturel EN FRANÇAIS",
  "description": "Description EN FRANÇAIS en 1-2 phrases"
}}
"""
    return prompt


def get_random_transition_hook() -> str:
    return random.choice(TRANSITION_HOOKS)


def get_transition_hooks(count: int = 3) -> List[str]:
    return random.sample(TRANSITION_HOOKS, min(count, len(TRANSITION_HOOKS)))

# ============================================
# 5. TOPIC SELECTION / CATEGORY / TAGS
# ============================================

def get_random_topic(exclude: Optional[List[str]] = None) -> str:
    """Pick a French topic, avoiding recent topics."""
    exclude_set = {t.strip().lower() for t in (exclude or []) if t}

    trending = []
    if os.environ.get("USE_TREND_RESEARCH", "false").lower() == "true":
        try:
            from trend_research import fetch_trending_topics
            trending = fetch_trending_topics()
        except ImportError:
            logger.debug("Trend research module not available")
        except Exception as e:
            logger.warning(f"Trend research failed: {e}")

    trend_candidates = [t for t in trending if t.strip().lower() not in exclude_set]

    if trend_candidates and random.random() < 0.6:
        chosen = random.choice(trend_candidates)
        logger.info(f"Selected trending topic: {chosen}")
        return chosen

    static_candidates = [t for t in DARK_TOPICS if t.strip().lower() not in exclude_set]

    if static_candidates:
        chosen = random.choice(static_candidates)
        logger.info(f"Selected static topic: {chosen}")
        return chosen

    logger.warning("All topics recently used - allowing repeat from static pool")
    return random.choice(DARK_TOPICS)


def get_topic_category(topic: str) -> str:
    """Categorize French-first topics into Brain, Body, Mystery, or Health."""
    topic_lower = topic.lower()

    brain_keywords = [
        "cerveau", "mémoire", "memoire", "sommeil", "réveil", "reveil",
        "réveilles", "reveille", "nuit", "rêve", "reve", "cauchemar",
        "attention", "stress", "anxiété", "anxiete", "nerveux", "neuro",
        "pens", "émotion", "emotion", "cortisol",
    ]
    body_keywords = [
        "corps", "cœur", "coeur", "sang", "foie", "peau", "muscle",
        "vaisseau", "respiration", "mains", "yeux", "oreille", "système",
        "systeme",
    ]
    health_keywords = [
        "microbiote", "ventre", "intestin", "digestion", "fatigue",
        "longévité", "longevite", "après 40", "apres 40", "métabolisme",
        "metabolisme", "bienêtre", "bien-etre", "bien-être", "rythme circadien",
    ]
    mystery_keywords = [
        "mystère", "mystere", "secret", "étrange", "etrange", "signal",
        "silence", "caché", "cache",
    ]

    def _has_word(words):
        return any(re.search(r"\b" + re.escape(w), topic_lower) for w in words)

    if _has_word(health_keywords):
        return "Health"
    if _has_word(brain_keywords):
        return "Brain"
    if _has_word(mystery_keywords):
        return "Mystery"
    if _has_word(body_keywords):
        return "Body"
    return "Body"


def get_seo_tags(topic: str, category: str = "Body") -> List[str]:
    """Return French-first YouTube tags, max 15."""
    stopwords = {
        "pourquoi", "comment", "dans", "avec", "sans", "après", "avant",
        "cette", "cela", "ceci", "ton", "ta", "tes", "tous", "toutes",
        "plus", "moins", "vraiment", "pendant", "quand", "fait", "font",
        "peut", "être", "etre",
    }

    topic_words = [
        re.sub(r"[^a-zA-ZÀ-ÿ0-9]", "", w.lower())
        for w in topic.split()
    ]
    tags = [w for w in topic_words if len(w) > 3 and w not in stopwords][:5]

    tags.extend(CATEGORY_TAGS.get(category, []))
    tags.extend([
        "corps humain", "faits scientifiques", "science sombre",
        "secrets du corps", "mystères du corps", "santé après 40 ans",
        "cerveau et sommeil", "vulgarisation scientifique", "shorts français",
    ])
    tags.extend(BASE_TAGS)

    seen, result = set(), []
    for tag in tags:
        clean = tag.strip().lower().replace("#", "")
        if clean and clean not in seen:
            seen.add(clean)
            result.append(tag.strip())
        if len(result) >= MAX_TAGS:
            break

    return result


def generate_seo_tags(topic: str, category: str = "Body", title: str = "") -> List[str]:
    return get_seo_tags(topic, category)

# ============================================
# 6. MEDICAL SAFETY
# ============================================

def validate_script_for_medical_accuracy(script_data: Dict) -> Dict:
    """Validate script does not contain medical advice or cure/diagnosis claims."""
    voiceover = script_data.get("voiceover", "")
    if not voiceover:
        voiceover = " ".join([
            s.get("caption", "")
            for s in script_data.get("scenes", [])
            if isinstance(s, dict)
        ])

    lowered = voiceover.lower()
    flags = [phrase for phrase in _MEDICAL_ADVICE_RED_FLAGS if phrase in lowered]

    return {
        "valid": len(flags) == 0,
        "flags": flags,
        "has_red_flags": len(flags) > 0,
    }


def auto_add_disclaimer(script_data: Dict) -> Dict:
    """Add a safe educational disclaimer."""
    disclaimer = (
        "Cette vidéo est uniquement à but éducatif/divertissant et ne constitue pas un avis médical. "
        "Consulte un professionnel de santé pour toute question personnelle."
    )

    script_data["cta"] = (script_data.get("cta", "") + " " + disclaimer).strip()

    if "description" in script_data:
        script_data["description"] = (script_data["description"] + " " + disclaimer).strip()

    script_data["disclaimer_added"] = True
    logger.info("Added medical disclaimer to script")
    return script_data

# ============================================
# 7. TITLE / EMOJI
# ============================================

_TOPIC_EMOJI_MAP = [
    (["cerveau", "mémoire", "memoire", "pensée", "pensee", "attention", "mental"], "🧠"),
    (["sommeil", "nuit", "réveil", "reveil", "rêve", "reve", "cauchemar"], "😴"),
    (["cœur", "coeur", "sang", "pouls", "palpitation", "battement"], "🫀"),
    (["microbiote", "ventre", "intestin", "digestion", "bactérie", "bacterie"], "🦠"),
    (["stress", "cortisol", "anxiété", "anxiete", "système nerveux", "systeme nerveux"], "⚡"),
    (["respiration", "souffle", "poumon", "nerf vague"], "🌬️"),
    (["œil", "oeil", "yeux", "vision", "écran", "ecran", "lumière", "lumiere"], "👁️"),
    (["peau", "frisson", "température", "temperature", "froid"], "🥶"),
    (["muscle", "tension", "mouvement", "marche"], "💪"),
    (["foie", "métabolisme", "metabolisme", "énergie", "energie", "fatigue"], "🔥"),
    (["longévité", "longevite", "après 40", "apres 40", "âge", "age"], "⏳"),
]

_EMOJI_PATTERN = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+\\s*"
)


def _pick_topic_emoji(topic: str) -> str:
    topic_lower = topic.lower()
    for keywords, emoji in _TOPIC_EMOJI_MAP:
        if any(re.search(r"\b" + re.escape(kw) + r"\b", topic_lower) for kw in keywords):
            return emoji

    category = get_topic_category(topic)
    return {
        "Brain": "🧠",
        "Body": "🫀",
        "Mystery": "👁️",
        "Health": "🦠",
    }.get(category, "🫀")


def _make_seo_title(title: str, topic: str) -> str:
    """Enhance title while keeping it short."""
    clean_title = _EMOJI_PATTERN.sub("", title, count=1).strip()

    power_words = [
        "secret", "vérité", "jamais", "personne", "caché", "choc", "réel",
        "sombre", "attention", "secrets", "science", "cerveau", "sommeil",
        "stress", "corps",
    ]

    if any(pw in clean_title.lower() for pw in power_words):
        return clean_title[:MAX_TITLE_LENGTH]

    emoji = _pick_topic_emoji(topic)
    enhanced = f"{clean_title} {emoji}"

    if len(enhanced) <= MAX_TITLE_LENGTH:
        return enhanced

    return clean_title[:MAX_TITLE_LENGTH]

# ============================================
# 8. UTILITY FUNCTIONS
# ============================================

def get_random_hook(topic: Optional[str] = None) -> str:
    hook = random.choice(HOOK_FORMULAS)
    if topic and "{topic}" in hook:
        hook = hook.format(topic=topic)
    return hook


def get_random_pain_point() -> str:
    return random.choice(PAIN_POINTS)


def get_random_cta() -> str:
    return random.choice(CTAS)


def get_category_tags(category: str) -> List[str]:
    return CATEGORY_TAGS.get(category, CATEGORY_TAGS["Body"])


def get_scene_count() -> int:
    return SCENES_PER_SCRIPT

# ============================================
# 9. RETENTION ANALYSIS
# ============================================

def analyze_retention_potential(script_data: Dict) -> Dict:
    """French-aware retention scoring for Shorts."""
    scenes = script_data.get("scenes", [])
    score = 0
    suggestions = []

    if len(scenes) == SCENES_PER_SCRIPT:
        score += 20
    elif 8 <= len(scenes) <= 12:
        score += 15
    else:
        suggestions.append(f"Nombre de scènes idéal: {SCENES_PER_SCRIPT}, actuellement {len(scenes)}")

    cliffhanger_words = [
        "...", "mais", "pourtant", "sauf que", "et là", "voici",
        "attends", "étrange", "twist",
    ]

    cliffhanger_count = 0
    for scene in scenes:
        caption = scene.get("caption", "")
        if any(word in caption.lower() for word in cliffhanger_words):
            cliffhanger_count += 1

    cliffhanger_ratio = cliffhanger_count / len(scenes) if scenes else 0
    if cliffhanger_ratio >= 0.65:
        score += 25
    else:
        suggestions.append(f"Seulement {cliffhanger_ratio:.0%} scènes ont un cliffhanger - vise 65%+")

    you_count = 0
    for scene in scenes:
        caption = " " + scene.get("caption", "").lower() + " "
        you_count += sum(caption.count(f" {w} ") for w in ["tu", "ton", "ta", "tes", "toi", "te"])

    if you_count >= len(scenes) * 1.2:
        score += 25
    else:
        suggestions.append("Ajoute plus de langage direct: tu/ton/ta/tes")

    visual_keywords = [
        "cinématographique", "cinematographique", "macro", "sombre",
        "contraste", "dramatique", "gros plan", "lumière", "ombre",
    ]

    visual_quality = 0
    for scene in scenes:
        visual = scene.get("visual", "")
        if any(word in visual.lower() for word in visual_keywords):
            visual_quality += 1

    if scenes and visual_quality >= len(scenes) * 0.6:
        score += 20
    else:
        suggestions.append("Rends les visuels plus cinématographiques, sombres et dynamiques")

    voiceover = " ".join(s.get("caption", "") for s in scenes)
    wc = len(voiceover.split())

    if TARGET_WORD_RANGE[0] <= wc <= TARGET_WORD_RANGE[1]:
        score += 10
    else:
        suggestions.append(f"Mots totaux: {wc}; cible {TARGET_WORD_RANGE[0]}-{TARGET_WORD_RANGE[1]}")

    return {
        "retention_score": min(100, score),
        "suggestions": suggestions,
        "cliffhanger_ratio": cliffhanger_ratio,
        "you_count": you_count,
        "visual_quality": visual_quality / len(scenes) if scenes else 0,
        "word_count": wc,
        "is_viral_ready": score >= 80,
    }

# ============================================
# 10. SELF TEST
# ============================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("FRENCH RETENTION-OPTIMIZED NICHE STRATEGY TEST")
    print("=" * 60)

    print("\n1. Topic Selection:")
    for _ in range(3):
        topic = get_random_topic()
        print(f"   - {topic}")

    print("\n2. Topic Categorization:")
    test_topics = [
        "Pourquoi tu te réveilles à 3h du matin",
        "Ton microbiote parle à ton cerveau",
        "Le stress laisse une trace dans ton corps",
    ]
    for topic in test_topics:
        print(f"   {topic} → {get_topic_category(topic)}")

    print("\n3. Prompt Generation:")
    topic = "Pourquoi ta mémoire change après 40 ans"
    prompt = get_script_prompt_for_niche(topic)
    print(f"   Prompt length: {len(prompt)}")
    print(f"   Preview: {prompt[:200]}...")

    print("\n4. SEO Tags:")
    tags = get_seo_tags(topic, get_topic_category(topic))
    print(f"   {', '.join(tags[:8])}")

    print("\n5. Medical Validation:")
    script = {
        "voiceover": "Cette vidéo explique un phénomène du sommeil sans donner de diagnostic.",
        "scenes": [{"caption": "Ton cerveau trie des signaux pendant la nuit..."}],
    }
    result = validate_script_for_medical_accuracy(script)
    print(f"   Valid: {result['valid']}")
    print(f"   Flags: {result['flags']}")

    print("\n✅ MODULE READY")
