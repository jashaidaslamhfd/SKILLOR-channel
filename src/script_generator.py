"""
Script Generator Module for SKILLOR Pipeline
FULLY FIXED - JSON Cleaning + Native Tone + Retention Optimization
"""

import os
import json
import time
import logging
import re
from typing import Dict, List, Optional, Tuple
from groq import Groq, BadRequestError

# ============================================
# LOGGING CONFIGURATION
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CONSTANTS
# ============================================
MIN_SCENES = 8
MAX_SCENES = 12
MIN_WORDS = 130
MAX_WORDS = 170
MAX_RETRIES = 3
TEMPERATURE = 0.7
MAX_TOKENS = 2000

# ============================================
# 1. SYSTEM PROMPT (NATIVE TONE + RETENTION)
# ============================================

def _get_system_prompt() -> str:
    """
    2026 System Prompt with NATIVE ENGLISH TONE and RETENTION FOCUS.
    """
    return """Tu es un Stratège Réseaux Sociaux de tout premier plan pour 2026, spécialisé dans les YouTube Shorts en FRANÇAIS.

**LANGUE OBLIGATOIRE : Tout le contenu généré (title, hook, caption de chaque scène, cta, description) DOIT être écrit en FRANÇAIS naturel. N'écris JAMAIS en anglais.**

TON EXPERTISE :
- Créer des scripts VIRAUX avec un taux de rétention de 70%+
- Écrire en FRANÇAIS NATUREL et CONVERSATIONNEL (France)
- Des Hooks "Pattern Interrupt" qui arrêtent le scroll
- Un rythme psychologique qui garde les spectateurs engagés

**RÈGLES CRITIQUES - TON NATUREL :**
1. Écris comme un HUMAIN qui parle à un AMI - pas comme une IA
2. Utilise des CONTRACTIONS et un langage parlé naturel : "c'est", "tu vas", "ça"
3. Utilise des EXPRESSIONS IDIOMATIQUES : "ça va te scier", "ça fait flipper", "ça tombe sous le sens"
4. ÉVITE LES MOTS ROBOTIQUES : "ainsi", "par conséquent", "en effet", "de surcroît"
5. Utilise un LANGAGE COURANT : "honnêtement", "sérieusement", "carrément"
6. Reste NATUREL - lu à voix haute, ça doit sonner comme une vraie personne

**RÈGLES DE RÉTENTION (CRITIQUE) :**
1. **Hook Pattern Interrupt** : Les 3 premières secondes doivent être CHOQUANTES ou CONTRE-INTUITIVES
   - "Ton cœur te ment en ce moment même..."
   - "Ceci se produit dans ton cerveau chaque nuit..."

2. **La "règle des 3 secondes"** : Chaque scène doit avoir un MICRO-HOOK
   - Commence chaque scène avec de la tension
   - Termine chaque scène par un CLIFFHANGER
   - Exemple : "...mais ce n'est que la moitié de l'histoire"

3. **Langage "TU"** : Utilise une adresse personnelle directe
   - "Ton cerveau", "Ton cœur", "Tu ressens"
   - Crée une connexion émotionnelle

4. **Arc émotionnel** :
   - Hook (Curiosité/Choc) → Énoncer le problème → Révéler la solution → Boucler vers le hook

5. **STRUCTURE OBLIGATOIRE EN 4 PARTIES** :
   - PARTIE 1 - HOOK : Phrase d'ouverture choquante/contre-intuitive (première scène)
   - PARTIE 2 - PROBLÈME : Énonce clairement ce qui ne va pas / ce que le spectateur ignore
   - PARTIE 3 - SOLUTION : Révèle la réponse, la solution, ou la vérité derrière le problème
   - PARTIE 4 - BOUCLE : La dernière ligne doit faire écho aux mots ou images du hook,
     pour que la vidéo puisse se relancer en boucle de façon fluide (favorise le rewatch)

6. **Outro en boucle** : La fin doit naturellement ramener au début
   - Encourage à revoir la vidéo
   - La dernière caption doit faire écho à une phrase ou une image du hook

**FORMAT DE SORTIE :**
Retourne UNIQUEMENT du JSON valide avec cette structure exacte, tout le texte EN FRANÇAIS :
{
  "title": "Titre accrocheur EN FRANÇAIS (moins de 55 caractères)",
  "hook": "Le hook des 3 premières secondes EN FRANÇAIS (la partie la plus importante)",
  "scenes": [
    {
      "visual": "Description visuelle cinématographique (5-8 mots)",
      "caption": "Texte parlé percutant EN FRANÇAIS (15-20 mots)"
    }
  ],
  "cta": "Appel à l'action naturel EN FRANÇAIS",
  "description": "Description de la vidéo en 1-2 phrases, EN FRANÇAIS"
}

RAPPEL : Écris comme un HUMAIN, pas comme une IA. Sois NATUREL. Sois CONVERSATIONNEL. Concentre-toi sur la RÉTENTION. TOUT LE TEXTE DOIT ÊTRE EN FRANÇAIS.
"""


# ============================================
# 2. PROMPT GENERATION
# ============================================

def _default_prompt(topic: str) -> str:
    """
    Default prompt with NATIVE TONE and RETENTION enforcement.
    """
    return f"""
Crée un script viral À FORTE RÉTENTION de 45 secondes pour YouTube Shorts sur : "{topic}"

**TOUT LE CONTENU DOIT ÊTRE ÉCRIT EN FRANÇAIS. N'écris jamais en anglais.**

**CRITIQUE - TON FRANÇAIS NATUREL :**
- Écris comme un HUMAIN qui parle à un ami
- Utilise des tournures naturelles : "c'est", "tu vas", "ça"
- Utilise des expressions : "ça va te scier", "ça fait flipper", "ça tombe sous le sens"
- ÉVITE : "ainsi", "par conséquent", "en effet", "de surcroît"
- Doit sonner NATUREL à voix haute

**EXIGENCES DU SCRIPT :**

1. **HOOK** (3 premières secondes - CRITIQUE) :
   - Doit arrêter le scroll immédiatement
   - Utilise un ton conversationnel
   - Pattern interrupt ou déclaration choquante

2. **SCÈNES** ({MIN_SCENES}-{MAX_SCENES} scènes) :
   - Chaque scène : caption de 15-20 mots
   - Chaque scène : doit se terminer par un cliffhanger
   - Chaque scène : description visuelle cinématographique

3. **NOMBRE DE MOTS** (EXIGENCE STRICTE) :
   - Total : {MIN_WORDS}-{MAX_WORDS} mots
   - Compte tes mots AVANT de finaliser

4. **STRUCTURE (ARC OBLIGATOIRE EN 4 PARTIES) :**
   - Scène 1 : HOOK - ouverture choquante/contre-intuitive qui arrête le scroll
   - Scènes 2-4 : PROBLÈME - explique clairement ce qui ne va pas, ce que le spectateur ignore, monte la tension
   - Scènes 5-8 : SOLUTION - révèle la réponse/vérité/solution, résous la tension
   - Scène finale : BOUCLE - CTA qui fait écho à un mot, une phrase ou une image du hook
     de la Scène 1, pour que la fin ramène directement au début (replay fluide)

5. **TON** :
   - Sombre, mystérieux, factuel
   - Engageant, pas ennuyeux
   - NATUREL, CONVERSATIONNEL

**FORMAT DE SCÈNE :**
{{
  "visual": "Description cinématographique (macro, contraste élevé, éclairage dramatique)",
  "caption": "Texte percutant et engageant EN FRANÇAIS (se termine par un cliffhanger)"
}}

**Retourne UNIQUEMENT du JSON valide avec title, hook, scenes, cta, et description - tout en FRANÇAIS.**

**RAPPEL :** La rétention est TOUT. Écris comme un HUMAIN. Chaque seconde compte. TOUT DOIT ÊTRE EN FRANÇAIS.
"""


# ============================================
# 3. JSON CLEANING FUNCTION
# ============================================

def _clean_json_response(raw_reply: str) -> Dict:
    """
    Cleans and extracts JSON from LLM response.
    Handles markdown code blocks, extra text, and malformed JSON.
    """
    if not raw_reply:
        raise ValueError("Empty response from LLM")
    
    # Remove markdown code blocks
    raw_reply = re.sub(r'```json\s*', '', raw_reply)
    raw_reply = re.sub(r'```\s*', '', raw_reply)
    
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', raw_reply, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
    else:
        json_str = raw_reply
    
    # Clean common JSON issues
    json_str = json_str.strip()
    
    # Fix trailing commas
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # NOTE: We intentionally do NOT blanket-convert single quotes to double
    # quotes here. Groq's response_format={"type": "json_object"} already
    # guarantees valid double-quoted JSON, and the system prompt asks for
    # natural contractions ("don't", "you're"), which contain apostrophes.
    # Converting those apostrophes to '"' corrupts the JSON mid-string
    # (this was the root cause of the "Expecting ',' delimiter" errors).
    
    # Remove control characters
    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
    
    # Fix unescaped newlines in strings
    json_str = re.sub(r'(?<!\\)\n', ' ', json_str)
    
    # Try to parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed: {e}")
        logger.debug(f"Cleaned JSON: {json_str[:500]}...")
        
        # Fallback: Try to extract with regex
        fallback = {}
        
        # Extract title
        title_match = re.search(r'"title"\s*:\s*"([^"]+)"', json_str)
        if title_match:
            fallback['title'] = title_match.group(1)
        
        # Extract hook
        hook_match = re.search(r'"hook"\s*:\s*"([^"]+)"', json_str)
        if hook_match:
            fallback['hook'] = hook_match.group(1)
        
        # Extract scenes
        scenes_match = re.search(r'"scenes"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if scenes_match:
            scenes_str = scenes_match.group(1)
            scenes = []
            # Find all scene objects
            scene_blocks = re.finditer(r'\{[^{}]*\}', scenes_str, re.DOTALL)
            for block in scene_blocks:
                scene_str = block.group(0)
                visual_match = re.search(r'"visual"\s*:\s*"([^"]+)"', scene_str)
                caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', scene_str)
                if visual_match and caption_match:
                    scenes.append({
                        'visual': visual_match.group(1),
                        'caption': caption_match.group(1)
                    })
            if scenes:
                fallback['scenes'] = scenes
        
        # Extract CTA
        cta_match = re.search(r'"cta"\s*:\s*"([^"]+)"', json_str)
        if cta_match:
            fallback['cta'] = cta_match.group(1)
        
        # Extract description
        desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', json_str)
        if desc_match:
            fallback['description'] = desc_match.group(1)
        
        if fallback:
            logger.info("✅ Extracted data using regex fallback")
            return fallback
        
        raise ValueError(f"Could not parse JSON from response: {raw_reply[:200]}")


# ============================================
# 4. SCRIPT VALIDATION & NORMALIZATION
# ============================================

def _normalize_scenes(script_data: Dict) -> Dict:
    """
    Normalizes scene data from various formats.
    Ensures all required fields are present.
    """
    normalized = []
    
    for s in script_data.get('scenes', []):
        # Try different field names
        visual = s.get('visual') or s.get('description') or s.get('image') or ''
        caption = s.get('caption') or s.get('text') or s.get('speech') or ''
        
        # Clean and validate
        visual = visual.strip()
        caption = caption.strip()
        
        if visual and caption:
            normalized.append({
                "visual": visual,
                "caption": caption
            })
        elif caption and not visual:
            # If only caption exists, generate a generic visual
            normalized.append({
                "visual": f"Dark cinematic shot of {caption[:30]}...",
                "caption": caption
            })
    
    script_data['scenes'] = normalized
    script_data['voiceover'] = ' '.join(s['caption'] for s in normalized)
    
    return script_data


def _validate_script(script_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validates script for quality and completeness.
    
    Returns:
        (is_valid, issues_list)
    """
    issues = []
    
    # Check required fields
    required_fields = ['title', 'hook', 'scenes', 'cta']
    for field in required_fields:
        if not script_data.get(field):
            issues.append(f"Missing required field: {field}")
    
    # Check scenes
    scenes = script_data.get('scenes', [])
    if len(scenes) < MIN_SCENES:
        issues.append(f"Too few scenes: {len(scenes)} (minimum {MIN_SCENES})")
    elif len(scenes) > MAX_SCENES:
        issues.append(f"Too many scenes: {len(scenes)} (maximum {MAX_SCENES})")
    
    # Check word count
    voiceover = script_data.get('voiceover', '')
    word_count = len(voiceover.split())
    if word_count < MIN_WORDS - 10:
        issues.append(f"Too few words: {word_count} (minimum {MIN_WORDS})")
    elif word_count > MAX_WORDS + 10:
        issues.append(f"Too many words: {word_count} (maximum {MAX_WORDS})")
    
    # Check each scene
    for i, scene in enumerate(scenes):
        if not scene.get('visual'):
            issues.append(f"Scene {i+1} missing visual description")
        if not scene.get('caption'):
            issues.append(f"Scene {i+1} missing caption")
    
    return len(issues) == 0, issues


# ============================================
# 5. RETENTION ANALYSIS
# ============================================

def analyze_retention_potential(script_data: Dict) -> Dict:
    """
    Analyzes script for retention potential.
    Returns score (0-100) and suggestions.
    """
    scenes = script_data.get('scenes', [])
    score = 0
    suggestions = []
    
    # Check scene count
    if MIN_SCENES <= len(scenes) <= MAX_SCENES:
        score += 20
    else:
        suggestions.append(f"Optimal scene count: {MIN_SCENES}-{MAX_SCENES}, currently {len(scenes)}")
    
    # Check hook
    hook = script_data.get('hook', '')
    if hook:
        hook_words = len(hook.split())
        if 5 <= hook_words <= 15:
            score += 15
        else:
            suggestions.append("Hook should be 5-15 words for maximum impact")
        
        # Check for pattern interrupt (French + English fallback)
        if any(word in hook.lower() for word in [
            'ment', 'secret', 'vérité', 'jamais', 'toujours', 'vraiment',
            'lying', 'secret', 'truth', 'never', 'always', 'actually'
        ]):
            score += 10
    
    # Check "TU/TON/TA" language (French personal address)
    voiceover = script_data.get('voiceover', '')
    lowered_vo = voiceover.lower()
    you_count = sum(lowered_vo.count(w) for w in [' tu ', ' ton ', ' ta ', ' tes ', ' toi ', 'you'])
    if you_count >= len(scenes) * 1.5:
        score += 15
    else:
        suggestions.append("Utilise plus de langage 'TU/TON/TA' pour une connexion personnelle")
    
    # Check cliffhangers (French + English connectors)
    cliffhanger_count = 0
    for scene in scenes:
        caption = scene.get('caption', '')
        if any(word in caption.lower() for word in [
            '...', 'mais', 'pourtant', 'cependant', 'toutefois', 'sauf que',
            'but', 'however', 'yet', 'still', 'though'
        ]):
            cliffhanger_count += 1
    
    if cliffhanger_count >= len(scenes) * 0.7:
        score += 20
    else:
        suggestions.append(f"Seulement {cliffhanger_count}/{len(scenes)} scènes ont un cliffhanger - vise 70%+")
    
    # Check word count
    word_count = len(voiceover.split())
    if MIN_WORDS <= word_count <= MAX_WORDS:
        score += 20
    else:
        suggestions.append(f"Nombre de mots : {word_count} (cible : {MIN_WORDS}-{MAX_WORDS})")
    
    # Check for loopable outro (French + English CTA words)
    cta = script_data.get('cta', '')
    if any(word in cta.lower() for word in [
        'abonne', 'partage', 'suis', 'commente', 'follow', 'share', 'subscribe', 'comment'
    ]):
        score += 10
    
    return {
        'retention_score': min(100, score),
        'suggestions': suggestions,
        'scenes': len(scenes),
        'word_count': word_count,
        'you_count': you_count,
        'cliffhanger_ratio': cliffhanger_count / len(scenes) if scenes else 0,
        'is_viral_ready': score >= 80
    }


# ============================================
# 6. MAIN GENERATE FUNCTION
# ============================================

def generate_script(
    topic: str, 
    custom_prompt: Optional[str] = None, 
    max_retries: int = MAX_RETRIES
) -> Dict:
    """
    Generates a RETENTION-OPTIMIZED script using Groq LLM.
    
    Features:
    - JSON cleaning with regex fallback
    - Native French tone enforcement
    - Automatic validation and retry
    - Retention analysis
    
    Args:
        topic: Topic for the script
        custom_prompt: Optional custom prompt
        max_retries: Maximum retry attempts
    
    Returns:
        Script data dictionary
    
    Raises:
        RuntimeError: If generation fails after all retries
        ValueError: If GROQ_API_KEY is missing
    """
    # Check API key
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Please set it in environment variables.")
    
    # Initialize client
    client = Groq(api_key=api_key)
    
    # Prepare prompt
    prompt = custom_prompt or _default_prompt(topic)
    messages = [
        {"role": "system", "content": _get_system_prompt()},
        {"role": "user", "content": prompt}
    ]
    
    last_error = None
    best_script = None
    best_score = 0
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔄 Generating script (Attempt {attempt}/{max_retries})")
            
            # Call Groq API
            completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
            
            raw_reply = completion.choices[0].message.content
            
            # Clean JSON
            script_data = _clean_json_response(raw_reply)
            
            # Normalize scenes
            script_data = _normalize_scenes(script_data)
            
            # Add metadata
            script_data['topic'] = topic
            script_data['generated_at'] = time.time()
            script_data['attempt'] = attempt
            
            # Validate
            is_valid, issues = _validate_script(script_data)
            
            if is_valid:
                # Analyze retention
                retention = analyze_retention_potential(script_data)
                script_data['retention_analysis'] = retention
                
                score = retention['retention_score']
                
                # Track best script
                if score > best_score:
                    best_script = script_data
                    best_score = score
                
                if score >= 80:
                    logger.info(f"✅ Excellent script! Retention score: {score}/100")
                    logger.info(f"📊 {len(script_data['scenes'])} scenes, {len(script_data['voiceover'].split())} words")
                    return script_data
                else:
                    logger.warning(f"⚠️ Good but could be better (Score: {score}/100)")
                    # Add corrective feedback
                    messages.append({"role": "assistant", "content": raw_reply})
                    messages.append({"role": "user", "content": (
                        f"The script is good but retention could be improved. "
                        f"Current score: {score}/100. Issues: {', '.join(retention['suggestions'][:3])}. "
                        f"Rewrite the script with these improvements while keeping the topic '{topic}'. "
                        f"Return ONLY valid JSON with the same structure."
                    )})
            else:
                logger.warning(f"⚠️ Validation issues: {', '.join(issues[:3])}")
                messages.append({"role": "assistant", "content": raw_reply})
                messages.append({"role": "user", "content": (
                    f"The script has validation issues: {', '.join(issues[:3])}. "
                    f"Rewrite it to fix these issues. Keep the same topic '{topic}'. "
                    f"Return ONLY valid JSON with the same structure."
                )})
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            messages.append({"role": "user", "content": (
                "The previous response was not valid JSON. "
                "Please return ONLY valid JSON with this exact structure: "
                '{"title": "...", "hook": "...", "scenes": [{"visual": "...", "caption": "..."}], "cta": "..."}'
            )})
            
        except BadRequestError as e:
            logger.error(f"❌ Groq API error: {e}")
            last_error = e
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                break
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            last_error = e
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
    
    # If we have a best script, return it
    if best_script:
        logger.warning(f"⚠️ Using best available script (Score: {best_score}/100)")
        return best_script
    
    # Complete failure
    raise RuntimeError(
        f"❌ Script generation failed after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


# ============================================
# 7. BATCH GENERATION
# ============================================

def generate_multiple_scripts(
    topics: List[str],
    max_retries: int = MAX_RETRIES,
    delay: float = 2.0
) -> List[Dict]:
    """
    Generates scripts for multiple topics.
    
    Args:
        topics: List of topics
        max_retries: Retries per script
        delay: Delay between generations
    
    Returns:
        List of script data dictionaries
    """
    scripts = []
    failed = []
    
    for i, topic in enumerate(topics):
        logger.info(f"📝 Generating script {i+1}/{len(topics)}: {topic}")
        
        try:
            script = generate_script(topic, max_retries=max_retries)
            scripts.append(script)
            logger.info(f"✅ Script {i+1} generated successfully")
        except Exception as e:
            logger.error(f"❌ Script {i+1} failed: {e}")
            failed.append({'topic': topic, 'error': str(e)})
        
        if i < len(topics) - 1:
            time.sleep(delay)
    
    logger.info(f"📊 Generated {len(scripts)}/{len(topics)} scripts successfully")
    if failed:
        logger.warning(f"⚠️ Failed scripts: {len(failed)}")
    
    return scripts, failed


# ============================================
# 8. SCRIPT EXPORT
# ============================================

def export_script(script_data: Dict, output_path: str = "output/script.json") -> str:
    """
    Exports script data to JSON file.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 Script exported to: {output_path}")
    return output_path


# ============================================
# 9. MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("="*70)
    print("SCRIPT GENERATOR - FULLY FIXED (JSON Cleaning + Native Tone)")
    print("="*70)
    print()
    
    # Test single generation
    test_topic = "Why Your Brain Lies to You"
    print(f"🧪 Testing with topic: {test_topic}")
    print("-" * 70)
    
    try:
        script = generate_script(test_topic)
        
        print("✅ Script generated successfully!")
        print()
        print(f"📌 TITLE: {script.get('title')}")
        print(f"🎯 HOOK: {script.get('hook')}")
        print(f"📊 SCENES: {len(script.get('scenes', []))}")
        print(f"📝 WORDS: {len(script.get('voiceover', '').split())}")
        print(f"📢 CTA: {script.get('cta')}")
        
        if 'retention_analysis' in script:
            analysis = script['retention_analysis']
            print()
            print("📈 RETENTION ANALYSIS:")
            print(f"   Score: {analysis.get('retention_score')}/100")
            print(f"   Viral Ready: {analysis.get('is_viral_ready')}")
            if analysis.get('suggestions'):
                print("   Suggestions:")
                for suggestion in analysis['suggestions'][:3]:
                    print(f"     - {suggestion}")
        
        print()
        print("📄 FIRST SCENE PREVIEW:")
        scenes = script.get('scenes', [])
        if scenes:
            print(f"   Visual: {scenes[0].get('visual')}")
            print(f"   Caption: {scenes[0].get('caption')}")
        
        print()
        print("-" * 70)
        print("✅ Script generator is ready for production!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
