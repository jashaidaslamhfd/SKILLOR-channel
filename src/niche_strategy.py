"""
Niche Strategy Module for SKILLOR Pipeline
OPTIMIZED FOR: HIGH RETENTION + PSYCHOLOGICAL PACING
"""

import logging
import random
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ============================================
# 1. EXPANDED DARK TOPICS (100+ topics)
# ============================================
DARK_TOPICS = [
    # Brain / Mind / Neuroscience (25+)
    "Your Heart Has Its Own Brain",
    "This Happens Inside Your Brain When You Sleep",
    "Why You Get Goosebumps",
    "Your Brain Eats Itself While You Sleep",
    "The Part of Your Brain That Never Sleeps",
    "Why Your Brain Lies to You Every Day",
    "This Is What Deja Vu Actually Is",
    "Your Brain Can Rewire Itself Overnight",
    "The Reason You Talk to Yourself in Your Head",
    "Why Nightmares Exist At All",
    "Your Brain Deletes Memories on Purpose",
    "The Real Reason You Freeze Under Pressure",
    "Why Some People Never Forget a Face",
    "Your Brain Has a Hidden Backup System",
    "The Chemical That Makes You Fall in Love",
    "Why Your Brain Processes Fear Faster Than Logic",
    "The Part of Your Brain That Never Stops Growing",
    "Why You Can't Remember Being a Baby",
    "Your Brain Has Its Own Immune System",
    "The Reason You Get Brain Freeze",
    "Why Your Brain Shrinks When You're Depressed",
    "The Secret Language of Your Brain Waves",
    "Why Your Brain Makes You See Ghosts",
    "The Reason Your Brain Forgets Names",
    "Your Brain Creates Reality, Not Just Perceives It",
    
    # Heart / Blood / Circulatory (20+)
    "Your Body Has 100,000 km of Veins",
    "Why Your Heart Skips a Beat",
    "Your Blood Has a Secret Weapon",
    "Your Heart Beats 100,000 Times a Day Without Asking",
    "The Sound Your Heart Makes That You've Never Heard",
    "Why Your Face Turns Red When You're Angry",
    "The Reason Cold Hands Mean a Warm Heart",
    "Your Blood Changes Color Inside Your Body",
    "Your Heart Can Predict Your Death",
    "The Secret Behind Your Heartbeat",
    "Why Your Blood Is Actually Blue Inside",
    "Your Heart Has Its Own Electrical System",
    "The Reason Your Pulse Changes When You Lie",
    "Your Blood Vessels Could Circle the Earth",
    "Why Your Heart Breaks When You're Sad",
    "The Hidden Power of Your Blood Type",
    "Why Your Heart Beats Faster in the Morning",
    "The Reason Your Blood Clots When You Cut Yourself",
    "Your Heart Has a Memory of Its Own",
    "Why Your Blood Pressure Rises When You're Stressed",
    
    # Lungs / Breathing (15+)
    "Your Lungs Can Drown You From Inside",
    "Why You Yawn When You See Someone Else Yawn",
    "The Real Reason You Can't Tickle Yourself",
    "Why Holding Your Breath Feels Like Panic",
    "Your Lungs Have Their Own Cleaning System",
    "The Reason You Sneeze When You Look at Light",
    "Your Breathing Changes When You Think",
    "Why Your Lungs Never Fully Empty",
    "The Secret Power of Deep Breathing",
    "Why You Breathe Differently at Night",
    "The Reason Your Lungs Hurt in Cold Weather",
    "Your Lungs Can Heal Themselves",
    "Why Asthma Attacks Happen at Night",
    "The Hidden Connection Between Breath and Anxiety",
    "Why Your Breathing Slows When You Sleep",
    
    # Bones / Muscles (15+)
    "The Bone That Breaks Most in Fights",
    "Your Bones Are Being Replaced Right Now",
    "Why Cracking Your Knuckles Makes That Sound",
    "The Strongest Muscle in Your Body Isn't What You Think",
    "Why You Lose Height During the Day",
    "Your Bones Are Stronger Than Steel",
    "The Muscle That Never Tires",
    "Why Your Jaw Is the Strongest Muscle",
    "Your Skeleton Regenerates Every 10 Years",
    "The Bone That's Actually Fused at Birth",
    "Why Your Muscles Get Sore After Exercise",
    "The Secret to Building Muscle Faster",
    "Why Your Bones Weaken With Age",
    "The Strongest Bone in Your Body",
    "Why You Can't Move When You Sleep",
    
    # Digestive / Organs (15+)
    "Your Stomach Can Digest Itself",
    "The Organ You Can Live Without",
    "Your Gut Has Its Own Nervous System",
    "Why Your Stomach Growls Even When You're Not Hungry",
    "The Organ That Regrows Itself Completely",
    "Why You Can't Breathe and Swallow at the Same Time",
    "Your Liver Can Regrow in 30 Days",
    "The Reason You Get Heartburn",
    "Your Gut Has More Neurons Than Your Spinal Cord",
    "The Organ That Decides Your Mood",
    "Why Your Digestion Slows at Night",
    "The Secret to a Healthy Gut",
    "Why Your Stomach Hurts When You're Nervous",
    "The Organ That Controls Your Appetite",
    "Why You Get Food Cravings",
    
    # Skin / Senses (15+)
    "Your Skin Replaces Itself Every Month",
    "Why Your Eyes Never Actually Stop Moving",
    "The Reason Your Ears Never Stop Growing",
    "Why You Can't See Your Own Blind Spot",
    "Your Fingerprints Started Forming Before You Were Born",
    "Your Skin Has Its Own Immune System",
    "Why Your Hair Changes Color With Age",
    "The Reason You Get Goosebumps When Cold",
    "Your Eyes Have a Blind Spot You Never Notice",
    "Why Your Sense of Smell Changes at Night",
    "The Secret of Your Skin's Microbiome",
    "Why Your Skin Changes With Stress",
    "The Reason You Get Dark Circles Under Your Eyes",
    "Why Your Fingers Prune in Water",
    "The Hidden Power of Your Sense of Touch",
    
    # Mystery / Dark Facts (20+)
    "The Sound Only Your Body Can Hear",
    "Why Fear Has a Physical Smell",
    "The Moment Your Body Knows You're Lying",
    "Why Your Body Remembers Trauma Before Your Mind Does",
    "The Reflex You Can't Control No Matter What",
    "Why Some People Feel Pain Differently Than Others",
    "The Signal Your Body Sends Before You Even Notice It's Sick",
    "Why Your Body Temperature Drops Right Before You Wake Up",
    "Your Body Has a Hidden Backup Organ",
    "The Reason You Get Chills When You're Scared",
    "Why Your Body Twitches When You Sleep",
    "The Secret Death Signal Your Body Sends",
    "Why Your Body Smells Different When You're Anxious",
    "The Hidden Language of Your Body Language",
    "Why Your Body Freezes When You're in Danger",
    "The Reason Your Heart Pounds in a Crowd",
    "Why Your Body Can Heal Itself Without You Knowing",
    "The Hidden Intelligence of Your Immune System",
    "Why Your Body Yearns for Nature",
    "The Secret Rhythms of Your Body Clock",
]

# ============================================
# 2. HOOK FORMULAS (25+ with CLIFFHANGER ENDINGS)
# ============================================
HOOK_FORMULAS = [
    "Ceci arrive à ton corps chaque nuit... et tu n'en as aucune idée.",
    "Les médecins ne veulent pas que tu saches ça sur {topic}...",
    "Ton corps te ment à propos de {topic}. Voici la vérité.",
    "Personne ne t'a dit que ça se passait en toi, là, maintenant.",
    "C'est la partie de {topic} que ton prof de biologie a zappée.",
    "Tu as fait ça un million de fois sans jamais te demander pourquoi.",
    "Quelque chose dans ton corps se produit sans ta permission.",
    "Ça a l'air faux, mais {topic} est 100% réel.",
    "Les scientifiques viennent tout juste de comprendre ça sur {topic}.",
    "Ton corps te cache ça depuis toute ta vie.",
    "Voici pourquoi {topic} devient troublant une fois qu'on le sait.",
    "La plupart des gens ne sauront jamais ça sur {topic} de toute leur vie.",
    "Si ça t'est arrivé, ton corps a fait quelque chose d'incroyable.",
    "Il y a une raison pour laquelle personne ne parle de {topic}.",
    "C'est la chose la plus flippante que fait ton propre corps.",
    "Et si je te disais que {topic} est complètement différent de ce que tu penses ?",
    "La vérité sur {topic} que personne ne veut admettre.",
    "Ce seul fait sur {topic} va changer ta façon de te voir.",
    "Tu ne vas pas croire ce que {topic} signifie vraiment pour ton corps.",
    "Voici ce qui se passe à l'intérieur quand {topic} se produit.",
    "Le secret caché de {topic} qui était juste sous tes yeux.",
    "Pourquoi {topic} est la chose la plus incomprise sur ton corps.",
    "Chaque fois que {topic} se produit, ton corps essaie de te dire quelque chose.",
    "La science derrière {topic} est plus étrange que la fiction.",
    "Voici la vraie raison pour laquelle {topic} se produit dans ton corps.",
]

# ============================================
# 3. TRANSITION HOOKS (For Scene-to-Scene Retention)
# ============================================
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

# ============================================
# 4. PAIN POINTS (15+)
# ============================================
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

# ============================================
# 5. CTAS (15+)
# ============================================
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
    "Envoie ça à l'ami toujours frigorifié/fatigué/anxieux",
    "Mets un ❤️ si tu as appris un truc",
    "Commente '🤯' si ça t'a choqué",
    "Enregistre pour impressionner quelqu'un avec des faits",
    "Partage pour faire réfléchir quelqu'un sur son corps",
    "Abonne-toi pour débloquer plus de mystères du corps",
]

# ============================================
# 6. CATEGORY TAGS (SEO)
# ============================================
CATEGORY_TAGS = {
    "Brain": [
        "neuroscience", "faitscerveau", "faitspsycho", "espritchoque",
        "sciencecerveau", "cerveauhumain", "systemenerveux", "astucesmentales",
        "santeducerveau", "neuroplasticite", "cognition", "memoire",
    ],
    "Body": [
        "corpshumain", "faitscorps", "anatomie", "partiesducorps", "faitshumains",
        "conscienceducorps", "mystereducorps", "toncorps", "physiologie",
        "anatomiehumaine", "sciencecorps", "faitssante",
    ],
    "Mystery": [
        "sciencemystere", "faitsetranges", "faitseffrayants", "faitsinconnus",
        "sciencesombre", "secretsducorps", "plusonensait", "espritsouffle",
        "choquant", "inexplique", "paranormal",
    ],
    "Health": [
        "faitssante", "astucescorps", "faitsscience", "sciencesante",
        "mysteremedical", "santehumaine", "bienetre", "conseilssante",
        "parcoursbienetre", "viesaine",
    ],
}

# ============================================
# 7. BASE TAGS
# ============================================
BASE_TAGS = [
    "faitssombres", "faits", "shorts", "youtubeshorts", "science",
    "leSavaisTu", "espritchoque", "faitsamusants", "faitseffrayants", "viral",
    "mystere", "inconnu", "flippant", "interessant", "education",
]

# ============================================
# 8. CONSTANTS
# ============================================
TARGET_WORD_RANGE = (130, 170)
MAX_TAGS = 15
MAX_TITLE_LENGTH = 55
SCENES_PER_SCRIPT = 9  # Optimized for 3-5 second scenes

# ============================================
# 9. MEDICAL RED FLAGS
# ============================================
_MEDICAL_ADVICE_RED_FLAGS = [
    "guérit", "diagnostique", "tu as", "arrête de prendre", "pas besoin de médecin",
    "au lieu du médicament", "guérison garantie", "signifie forcément que tu as",
    "tu devrais", "tu dois", "ne va jamais chez le médecin", "ignore ton médecin",
    "c'est le seul remède", "meilleur que la médecine", "remplace ton traitement",
    # English fallbacks kept in case the LLM slips into English
    "cure", "diagnose", "you have", "stop taking", "don't need a doctor",
]

# ============================================
# 10. RETENTION-OPTIMIZED PROMPT GENERATION
# ============================================

def get_script_prompt_for_niche(
    topic: str, 
    hook_preference: Optional[str] = None
) -> str:
    """
    Generates a RETENTION-OPTIMIZED prompt for script generation.
    Focuses on: Psychological Pacing, Visual Stimulation, and Cliffhangers.
    
    Args:
        topic: Topic string
        hook_preference: Specific hook to use (optional)
    
    Returns:
        Prompt string for AI
    """
    # Select hook
    if not hook_preference:
        hook_preference = random.choice(HOOK_FORMULAS)
        if "{topic}" in hook_preference:
            hook_preference = hook_preference.format(topic=topic)
    
    # Select pain point and CTA
    pain_point = random.choice(PAIN_POINTS)
    cta = random.choice(CTAS)
    
    # Word count and scene configuration
    min_w, max_w = TARGET_WORD_RANGE
    num_scenes = SCENES_PER_SCRIPT
    per_scene_lo = min_w // num_scenes
    per_scene_hi = max_w // num_scenes
    
    # Select random transitions for cliffhangers
    transitions = random.sample(TRANSITION_HOOKS, min(5, len(TRANSITION_HOOKS)))
    
    # Build RETENTION-OPTIMIZED prompt (French output)
    prompt = f"""
Tu es un communicateur scientifique expert en mystères, spécialisé dans la création de YouTube Shorts À FORTE RÉTENTION en FRANÇAIS, pour un public adulte francophone 18+.

**IMPORTANT : Tout le contenu (titre, hook, captions, cta, description) DOIT être écrit en FRANÇAIS naturel et courant, jamais en anglais.**

SUJET : {topic}

🎯 STRATÉGIE DE RÉTENTION (CRITIQUE) :
- Chaque scène doit se terminer par un CLIFFHANGER qui donne envie de voir la suite
- Utilise le langage "TU/TON/TA" partout (ex : "Ton cerveau", "Tu ressens") - rends-le PERSONNEL
- Chaque scène DOIT durer 3 à 5 secondes de contenu parlé (court, percutant, intense)
- Construis un schéma CURIOSITÉ > RÉVÉLATION > CLIFFHANGER dans chaque scène

STRUCTURE DU SCRIPT :
1. HOOK SOMBRE : "{hook_preference}"
2. RELIER l'information à la vie quotidienne du spectateur
3. SCIENCE derrière le phénomène (simplifiée, intrigante)
4. RÉVÉLATION qui choque ou surprend
5. TRANSITION CLIFFHANGER vers la scène suivante
6. CTA : "{cta}"
7. AVERTISSEMENT : Contenu éducatif/divertissement uniquement, pas un avis médical

TON : Sombre, mystérieux, factuel, engageant, personnel
POINT DE DOULEUR : {pain_point}
TRANSITIONS CLIFFHANGER SUGGÉRÉES (utilise un style similaire entre les scènes) : {', '.join(transitions)}

📝 EXIGENCES DES SCÈNES :

NOMBRE DE MOTS (EXIGENCE STRICTE) :
- La voix off totale DOIT faire {min_w}-{max_w} mots
- Divisée en exactement {num_scenes} scènes
- Caption de chaque scène : {per_scene_lo}-{per_scene_hi} mots
- Chaque scène = 3-5 secondes de parole

QUALITÉ DES CAPTIONS POUR LA RÉTENTION :
- Commence chaque scène par un MICRO-HOOK (ex : "Mais voici le twist...")
- Termine chaque scène par un CLIFFHANGER (ex : "...et c'est là que ça devient étrange")
- Utilise des phrases courtes et percutantes (5-10 mots max par phrase)
- Construis la tension à chaque phrase
- AUCUN mot de remplissage - chaque mot doit apporter de la valeur
- Connecte chaque scène à l'expérience personnelle du spectateur

🎨 DESCRIPTION VISUELLE (CRITIQUE POUR LA RÉTENTION) :
- "visual" : Décris une image VISUELLEMENT STIMULANTE
- Utilise des mots comme : cinématographique, contraste élevé, macro, flou de mouvement, sombre, feutré
- Chaque visuel doit être UNIQUE et DYNAMIQUE (pas d'images statiques)
- Pense à : éclairage dramatique, gros plans, représentations abstraites, métaphores
- Note : la description "visual" elle-même peut rester en anglais/termes techniques cinématographiques si besoin, mais la "caption" doit toujours être en français.

FORMAT DE SCÈNE :
Pour chaque scène, fournis :
- "visual": 5-8 mots décrivant une image CINÉMATOGRAPHIQUE (ex : "Macro shot of a beating heart, dark background")
- "caption": Le texte EXACT à dire, EN FRANÇAIS (percutant, orienté cliffhanger, personnel)

FORMAT DE SORTIE :
Retourne UNIQUEMENT du JSON valide, aucun autre texte, avec tout le texte en FRANÇAIS :

{{
  "title": "Titre court et accrocheur EN FRANÇAIS (moins de 55 caractères)",
  "hook": "{hook_preference}",
  "scenes": [
    {{"visual": "...", "caption": "..."}},
    ...
  ],
  "cta": "{cta}",
  "description": "Description de la vidéo en 1-2 phrases, EN FRANÇAIS"
}}

⚡ LISTE DE VÉRIFICATION RÉTENTION (AVANT DE FINALISER) :
✓ Chaque scène se termine par un cliffhanger
✓ Langage "TU/TON/TA" utilisé partout
✓ Chaque scène dure 3-5 secondes de parole
✓ Descriptions visuelles CINÉMATOGRAPHIQUES et UNIQUES
✓ Nombre de mots total : {min_w}-{max_w}
✓ Exactement {num_scenes} scènes
✓ Aucun avis médical
✓ Ton sombre, mystérieux, scientifique
✓ Tout le texte (title, hook, caption, cta, description) est en FRANÇAIS

RAPPEL : Le spectateur doit se sentir OBLIGÉ de regarder la scène suivante. Rends-le ADDICTIF.
"""
    return prompt


def get_random_transition_hook() -> str:
    """Get a random transition hook for scene endings"""
    return random.choice(TRANSITION_HOOKS)


def get_transition_hooks(count: int = 3) -> List[str]:
    """Get multiple transition hooks"""
    return random.sample(TRANSITION_HOOKS, min(count, len(TRANSITION_HOOKS)))

# ============================================
# 11. CORE FUNCTIONS
# ============================================

def get_random_topic(exclude: Optional[List[str]] = None) -> str:
    """
    Picks a topic for the next video.
    
    Priority:
    1. Live trend-research topics (60% chance when available)
    2. Static DARK_TOPICS pool (fallback)
    3. Skips recently used topics from exclude list
    
    Args:
        exclude: List of topics to exclude (recently used)
    
    Returns:
        Selected topic string
    """
    exclude_set = {t.strip().lower() for t in (exclude or []) if t}
    logger.debug(f"Excluding {len(exclude_set)} recent topics")

    # Try to get trending topics
    trending = []
    try:
        from trend_research import fetch_trending_topics
        trending = fetch_trending_topics()
        logger.debug(f"Fetched {len(trending)} trending topics")
    except ImportError:
        logger.debug("Trend research module not available")
    except Exception as e:
        logger.warning(f"Trend research failed: {e}")

    # Filter trending topics
    trend_candidates = [
        t for t in trending 
        if t.strip().lower() not in exclude_set
    ]
    
    # 60% chance to use trending if available
    if trend_candidates and random.random() < 0.6:
        chosen = random.choice(trend_candidates)
        logger.info(f"Selected trending topic: {chosen}")
        return chosen

    # Fallback to static pool
    static_candidates = [
        t for t in DARK_TOPICS 
        if t.strip().lower() not in exclude_set
    ]
    
    if static_candidates:
        chosen = random.choice(static_candidates)
        logger.info(f"Selected static topic: {chosen}")
        return chosen
    
    # If everything is excluded, allow a repeat
    logger.warning("All topics recently used - allowing repeat from static pool")
    return random.choice(DARK_TOPICS)


def get_topic_category(topic: str) -> str:
    """
    Categorizes a topic into Brain, Body, Mystery, or Health.
    
    Args:
        topic: Topic string
    
    Returns:
        Category name
    """
    topic_lower = topic.lower()
    
    brain_keywords = ['brain', 'mind', 'sleep', 'nerve', 'psych', 'memory', 'thought', 'conscious']
    body_keywords = ['heart', 'blood', 'lung', 'kidney', 'bone', 'organ', 'muscle', 'vein', 'artery']
    mystery_keywords = ['scary', 'secret', 'dark', 'mystery', 'hidden', 'unknown', 'creepy', 'weird']
    
    def _has_word(words):
        return any(re.search(r'\b' + re.escape(w), topic_lower) for w in words)
    
    if _has_word(brain_keywords):
        return "Brain"
    elif _has_word(mystery_keywords):
        return "Mystery"
    elif _has_word(body_keywords):
        return "Body"
    else:
        return "Body"  # Default


def get_seo_tags(topic: str, category: str = "Body") -> List[str]:
    """
    Returns YouTube-optimized tags (max 15).
    Priority order (most video-specific first, so with MAX_TAGS capping
    the list, unique/relevant tags always win over generic filler):
      1. Topic-specific keywords (unique per video)
      2. Category tags (Brain/Body/Mystery/Health - varies by topic)
      3. Related niche phrases
      4. Generic base/reach tags (same every video - filler only)
    
    Args:
        topic: Topic string
        category: Category name
    
    Returns:
        List of SEO tags
    """
    # 1. Topic-specific keywords FIRST - these make each video's tags unique
    topic_words = [
        w for w in topic.lower().split()
        if len(w) > 3 and w not in ['your', 'this', 'that', 'what', 'when']
    ]
    tags = topic_words[:5]

    # 2. Category-specific tags (varies by Brain/Body/Mystery/Health)
    tags.extend(CATEGORY_TAGS.get(category, []))

    # 3. Related niche phrases
    related_phrases = [
        "human body", "science facts", "dark science",
        "body secrets", "mysterious facts", "human anatomy"
    ]
    tags.extend(related_phrases)

    # 4. Generic discovery tags LAST - only fill whatever slots remain
    tags.extend(BASE_TAGS)
    
    # Deduplicate and limit
    seen = set()
    result = []
    for tag in tags:
        clean = tag.strip().lower()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(tag)
        if len(result) >= MAX_TAGS:
            break
    
    return result


def generate_seo_tags(topic: str, category: str = "Body", title: str = "") -> List[str]:
    """
    Wrapper for get_seo_tags for compatibility.
    
    Args:
        topic: Topic string
        category: Category name
        title: Video title (optional)
    
    Returns:
        List of SEO tags
    """
    return get_seo_tags(topic, category)


def validate_script_for_medical_accuracy(script_data: Dict) -> Dict:
    """
    Validates that script doesn't contain medical advice.
    
    Args:
        script_data: Script dictionary
    
    Returns:
        Dict with 'valid' boolean and 'flags' list
    """
    # Extract voiceover text
    voiceover = script_data.get('voiceover', '')
    if not voiceover:
        voiceover = ' '.join([
            s.get('caption', '') 
            for s in script_data.get('scenes', []) 
            if isinstance(s, dict)
        ])
    
    # Check for red flags
    lowered = voiceover.lower()
    flags = [
        phrase for phrase in _MEDICAL_ADVICE_RED_FLAGS 
        if phrase in lowered
    ]
    
    return {
        "valid": len(flags) == 0,
        "flags": flags,
        "has_red_flags": len(flags) > 0
    }


def auto_add_disclaimer(script_data: Dict) -> Dict:
    """
    Adds medical disclaimer to script.
    
    Args:
        script_data: Script dictionary
    
    Returns:
        Modified script dictionary
    """
    disclaimer = "Cette vidéo est uniquement à but éducatif/divertissant et ne constitue pas un avis médical. Consulte un médecin pour toute question de santé."
    
    # Add to CTA
    script_data['cta'] = (
        script_data.get('cta', '') + " " + disclaimer
    ).strip()
    
    # Add to description
    if 'description' in script_data:
        script_data['description'] = (
            script_data['description'] + " " + disclaimer
        ).strip()
    
    # Add flag
    script_data['disclaimer_added'] = True
    
    logger.info("Added medical disclaimer to script")
    return script_data


# Emoji chosen by matching actual topic keywords (most specific first),
# not just a generic per-category icon - and placed at the END of the
# title, not the start, so the keyword text leads (better for YouTube
# search matching / SEO than a leading emoji).
_TOPIC_EMOJI_MAP = [
    (['bone', 'bones', 'skeleton'], '🦴'),
    (['leg', 'legs', 'knee', 'knees'], '🦵'),
    (['ear', 'ears', 'hearing', 'sound'], '👂'),
    (['heart', 'blood', 'pulse', 'heartbeat'], '🫀'),
    (['immune', 'microbiome', 'bacteria', 'germ', 'germs', 'virus'], '🦠'),
    (['fingerprint', 'fingerprints', 'finger', 'fingers'], '🫆'),
    (['cold', 'chill', 'chills', 'temperature', 'fever'], '🥶'),
    (['eye', 'eyes', 'see', 'sight', 'blind spot'], '👁️'),
    (['muscle', 'muscles', 'strength', 'exercise'], '💪'),
    (['sleep', 'sleeping', 'night', 'nightmare', 'nightmares'], '😴'),
    (['brain', 'mind', 'memory', 'thought'], '🧠'),
]

_EMOJI_PATTERN = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+\\s*"
)


def _pick_topic_emoji(topic: str) -> str:
    """Pick the most relevant emoji for a topic from the approved emoji
    set, based on keyword match. Falls back to a category default."""
    topic_lower = topic.lower()
    for keywords, emoji in _TOPIC_EMOJI_MAP:
        if any(re.search(r'\b' + re.escape(kw) + r'\b', topic_lower) for kw in keywords):
            return emoji
    
    # Fallback by category if no specific keyword matched
    category = get_topic_category(topic)
    return {"Brain": "🧠", "Body": "🫀", "Mystery": "👁️", "Health": "🦠"}.get(category, "🫀")


def _make_seo_title(title: str, topic: str) -> str:
    """
    Enhances title for SEO while keeping under 55 chars.
    
    Args:
        title: Original title
        topic: Topic string
    
    Returns:
        SEO-optimized title
    """
    # Strip any emoji the LLM may have already put at the start of the
    # title - otherwise we'd stack a second emoji on top of it below.
    clean_title = _EMOJI_PATTERN.sub('', title, count=1).strip()
    
    # If title already has power words, keep it (already punchy, skip emoji)
    power_words = ["secret", "nobody", "never", "actually", "dark", "scary",
                   "real", "hidden", "warning", "shock", "fact", "truth",
                   "vérité", "jamais", "personne", "caché", "choc", "réel",
                   "sombre", "attention", "secrets"]
    if any(pw in clean_title.lower() for pw in power_words):
        return clean_title[:MAX_TITLE_LENGTH]
    
    emoji = _pick_topic_emoji(topic)
    
    # Emoji goes at the END - keyword text leads for search matching
    enhanced = f"{clean_title} {emoji}"
    if len(enhanced) <= MAX_TITLE_LENGTH:
        return enhanced
    
    return clean_title[:MAX_TITLE_LENGTH]


# ============================================
# 12. UTILITY FUNCTIONS
# ============================================

def get_random_hook(topic: Optional[str] = None) -> str:
    """
    Get a random hook formula, optionally with topic.
    
    Args:
        topic: Topic to insert into hook (optional)
    
    Returns:
        Hook string
    """
    hook = random.choice(HOOK_FORMULAS)
    if topic and "{topic}" in hook:
        hook = hook.format(topic=topic)
    return hook


def get_random_pain_point() -> str:
    """Get a random pain point."""
    return random.choice(PAIN_POINTS)


def get_random_cta() -> str:
    """Get a random CTA."""
    return random.choice(CTAS)


def get_category_tags(category: str) -> List[str]:
    """Get tags for a specific category."""
    return CATEGORY_TAGS.get(category, CATEGORY_TAGS["Body"])


def get_scene_count() -> int:
    """Get the optimal number of scenes for retention."""
    return SCENES_PER_SCRIPT

# ============================================
# 13. RETENTION ANALYSIS FUNCTIONS
# ============================================

def analyze_retention_potential(script_data: Dict) -> Dict:
    """
    Analyzes script for retention potential.
    
    Returns:
        Dict with retention scores and suggestions
    """
    scenes = script_data.get('scenes', [])
    score = 0
    suggestions = []
    
    # Check scene count
    if len(scenes) == SCENES_PER_SCRIPT:
        score += 20
    else:
        suggestions.append(f"Optimal scene count is {SCENES_PER_SCRIPT}, currently {len(scenes)}")
    
    # Check for cliffhangers
    cliffhanger_count = 0
    for scene in scenes:
        caption = scene.get('caption', '')
        if any(word in caption.lower() for word in ['...', 'but', 'however', 'yet', 'still']):
            cliffhanger_count += 1
    
    cliffhanger_ratio = cliffhanger_count / len(scenes) if scenes else 0
    if cliffhanger_ratio >= 0.7:
        score += 30
    else:
        suggestions.append(f"Only {cliffhanger_ratio:.0%} scenes have cliffhangers - aim for 70%+")
    
    # Check "YOU" language
    you_count = 0
    for scene in scenes:
        caption = scene.get('caption', '')
        you_count += caption.lower().count('you')
    
    if you_count >= len(scenes) * 2:
        score += 25
    else:
        suggestions.append("Use more 'YOU' language for personal connection")
    
    # Check visual quality
    visual_quality = 0
    for scene in scenes:
        visual = scene.get('visual', '')
        if any(word in visual.lower() for word in ['cinematic', 'macro', 'close', 'dark', 'dramatic']):
            visual_quality += 1
    
    if visual_quality >= len(scenes) * 0.6:
        score += 25
    else:
        suggestions.append("Make visuals more CINEMATIC and DYNAMIC")
    
    return {
        'retention_score': min(100, score),
        'suggestions': suggestions,
        'cliffhanger_ratio': cliffhanger_ratio,
        'you_count': you_count,
        'visual_quality': visual_quality / len(scenes) if scenes else 0
    }

# ============================================
# 14. MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    # Test functionality
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("RETENTION-OPTIMIZED NICHE STRATEGY TEST")
    print("="*60)
    print()
    
    # Test topic selection
    print("1. Topic Selection:")
    for i in range(3):
        topic = get_random_topic()
        print(f"   - {topic}")
    print()
    
    # Test categorization
    test_topics = [
        "Your Brain Lies to You",
        "Your Heart Has Its Own Brain",
        "Why Fear Has a Physical Smell"
    ]
    print("2. Topic Categorization:")
    for topic in test_topics:
        category = get_topic_category(topic)
        print(f"   {topic} → {category}")
    print()
    
    # Test prompt generation
    print("3. Retention-Optimized Prompt Generation:")
    topic = "Why Your Brain Lies to You"
    prompt = get_script_prompt_for_niche(topic)
    print(f"   Generated prompt ({len(prompt)} chars)")
    print(f"   First 200 chars: {prompt[:200]}...")
    print()
    
    # Test transition hooks
    print("4. Transition Hooks:")
    transitions = get_transition_hooks(3)
    for hook in transitions:
        print(f"   - {hook}")
    print()
    
    # Test SEO tags
    print("5. SEO Tags:")
    tags = get_seo_tags("Brain Secrets", "Brain")
    print(f"   Tags: {', '.join(tags[:5])}...")
    print()
    
    # Test medical validation
    print("6. Medical Validation:")
    script = {
        "voiceover": "This can help diagnose your condition",
        "scenes": [{"caption": "Test caption"}]
    }
    result = validate_script_for_medical_accuracy(script)
    print(f"   Valid: {result['valid']}")
    print(f"   Flags: {result['flags']}")
    print()
    
    print("="*60)
    print("✅ RETENTION-OPTIMIZED MODULE READY!")
    print("="*60)
