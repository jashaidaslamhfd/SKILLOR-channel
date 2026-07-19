"""SEO français, pensé pour la découverte sur YouTube France et la francophonie."""
import re
from typing import Dict, List
TITLE_MAX_LEN=70; TITLE_MAX_WORDS=7; DESCRIPTION_MAX_LEN=5000; PINNED_COMMENT_MAX_LEN=200
PLAYLISTS_BY_CATEGORY={"Cerveau":"Cerveau & mémoire","Corps":"Réflexes du corps","Sommeil":"Sommeil expliqué","Science":"Science du quotidien"}
STOP={"le","la","les","un","une","de","du","des","et","ou","pourquoi","comment","dans","sur","à","au","aux","ce","cette","ces","votre","vous"}
def _words(v): return re.findall(r"[\wÀ-ÿŒœ'-]+",v or "",flags=re.UNICODE)
def _title(v,fallback="La science du quotidien"):
    return " ".join(_words(v)[:TITLE_MAX_WORDS])[:TITLE_MAX_LEN].strip() or fallback
def _category(topic):
    x=topic.lower()
    if any(w in x for w in ("sommeil","rêve","réveil")): return "Sommeil"
    if any(w in x for w in ("cerveau","mémoire","déjà-vu","chanson")): return "Cerveau"
    if any(w in x for w in ("corps","coeur","cœur","yeux","ventre","main","muscle","peau")): return "Corps"
    return "Science"
def _keywords(topic): return [w.lower() for w in _words(topic) if len(w)>3 and w.lower() not in STOP][:5]
def generate_seo_package(topic: str, script_data: Dict) -> Dict:
    title=_title(script_data.get("title") or topic)
    category=_category(topic); keys=_keywords(topic)
    title_options=list(dict.fromkeys([title, _title(f"Pourquoi {topic}"), _title(f"{topic} expliqué"), _title(f"La science de {topic}")]))[:4]
    hook=script_data.get("hook","").strip(); desc=script_data.get("description","").strip(); cta=script_data.get("cta","Abonnez-vous pour plus de science simple.").strip()
    hashtags=["#shorts","#science","#scienceduquotidien"]+["#"+re.sub(r"[^\w]","",k) for k in keys[:3]]
    hashtags=list(dict.fromkeys(hashtags))
    description=f"{desc}\n\n{hook}\n\n{cta}\n\n"+" ".join(hashtags)
    return {"title_options":title_options,"title":title,"chosen_title":title,"description":description[:DESCRIPTION_MAX_LEN],"tags":list(dict.fromkeys(keys+["science", "corps humain", "cerveau", "faits scientifiques", "français"])),"hashtags":hashtags,"thumbnail_text":(script_data.get("thumbnail_text") or title).upper()[:35],"pinned_comment":"Quel phénomène du corps aimeriez-vous voir expliqué ensuite ?","playlist_suggestion":PLAYLISTS_BY_CATEGORY[category],"seo_score":{"scores":{"overall_seo_score":85},"category":category}}

def generate_description(script_data: Dict, tags: List[str] | None = None) -> str:
    """Description unique, en français, utilisée par l'upload YouTube."""
    package = generate_seo_package(script_data.get("topic") or script_data.get("title", "science"), script_data)
    extra = ["#" + re.sub(r"[^\w]", "", str(t)) for t in (tags or [])[:3] if t]
    return (package["description"] + "\n" + " ".join(extra)).strip()[:DESCRIPTION_MAX_LEN]
