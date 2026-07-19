import os
import random
import hashlib
import threading
import requests
import logging

from image_providers import available_providers, RateLimitError
from media_validator import validate_scene_image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FALLBACK CHAIN (in order):
#   1) AI generation (Pollinations/HuggingFace/Gemini/Craiyon/etc via
#      image_providers.PROVIDER_REGISTRY) - PRIMARY. This is the only layer
#      that actually renders the exact scene ("dark cinematic anatomy shot",
#      etc.) instead of grabbing whatever unrelated image already exists
#      somewhere on the web, so it's what keeps visuals matching the script's
#      tone and keeps every video's imagery unique (not shared with other
#      creators - avoids "reused content" suppression on Shorts/Reels).
#   2) Local pre-generated pool (assets/fallback_images/, built ahead of time
#      by scripts/generate_fallback_images.py) - still on-niche AI art, just
#      not rendered fresh for this exact scene. Used when every live AI
#      provider is rate-limited.
#   3) Pexels / Pixabay live stock photos - generic, and shared with
#      thousands of other channels, so this only kicks in if 1 and 2 both
#      fail entirely.
#   4) Playwright screenshot of a random top search result - absolute last
#      resort. This does NOT produce a themed visual (it's literally
#      whatever webpage layout/ads/nav-bar happens to be on the page), so it
#      only exists to guarantee *something* gets saved rather than crashing
#      the whole video; it should essentially never fire in normal operation.
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 30
_fallback_lock = threading.Lock()

DARK_STYLE_SUFFIX = (
    "clean cinematic documentary lighting, realistic human detail, sharp focus, "
    "crisp high-resolution detail, natural color, professional camera quality, "
    "vertical composition, no text, no watermark, not blurry, not dull"
)

FALLBACK_POOL_DIR = "assets/fallback_images"


def _save_bytes(content: bytes, index: int, ext: str = "jpg") -> str:
    os.makedirs("output", exist_ok=True)
    path = f"output/scene_{index}.{ext}"
    with open(path, "wb") as f:
        f.write(content)
    return path


def _build_prompt(scene_text: str) -> str:
    """Combines the script's own scene description with a fixed dark/moody
    style suffix, so every AI-generated image stays on-brand for the
    dark-mystery-science niche instead of a generic photo of the subject."""
    base = (scene_text or "mystery science").strip()
    return f"{base}, {DARK_STYLE_SUFFIX}"


def _layer_ai_providers(index, scene_text, provider_names=None):
    """Try every configured AI image provider in order (Pollinations first,
    since it needs no API key, then whichever keyed providers are
    available). Each provider gets one attempt per call; the caller
    (`_generate_one`) is what advances to the next fallback layer if every
    provider here fails."""
    providers = available_providers()
    if provider_names is not None:
        providers = [provider for provider in providers if provider["name"] in set(provider_names)]
    if not providers:
        requested = ", ".join(provider_names or []) or "configured"
        raise RuntimeError(f"No {requested} AI image providers available (check API keys / network)")

    prompt_text = _build_prompt(scene_text)
    prompt = prompt_text.replace(" ", "_").replace(",", "")
    seed = random.randint(1, 999999)

    last_err = None
    for provider in providers:
        try:
            image_bytes, ext = provider["generate"](prompt, seed, prompt_text)
            if not image_bytes or len(image_bytes) < 2000:
                raise RuntimeError(f"{provider['name']}: empty/too-small response")
            path = _save_bytes(image_bytes, index, ext=ext)
            logger.info(f"Scene {index}: AI image via {provider['name']}")
            return path
        except RateLimitError as e:
            logger.warning(f"Scene {index}: {provider['name']} rate-limited, trying next provider: {e}")
            last_err = e
            continue
        except Exception as e:
            logger.warning(f"Scene {index}: {provider['name']} failed, trying next provider: {e}")
            last_err = e
            continue

    raise RuntimeError(f"All AI providers failed for scene {index}: {last_err}")


def _layer_local_pool(index, used_fallbacks: set):
    """Pulls a random not-yet-used image from the pre-generated on-niche
    pool (assets/fallback_images/), built by scripts/generate_fallback_images.py.
    Still matches the channel's dark-mystery look even though it's not
    rendered specifically for this scene."""
    if not os.path.isdir(FALLBACK_POOL_DIR):
        raise RuntimeError(f"No local fallback pool at {FALLBACK_POOL_DIR}")

    candidates = [
        os.path.join(FALLBACK_POOL_DIR, f)
        for f in os.listdir(FALLBACK_POOL_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    if not candidates:
        raise RuntimeError(f"Local fallback pool at {FALLBACK_POOL_DIR} is empty")

    with _fallback_lock:
        unused = [c for c in candidates if c not in used_fallbacks]
        pick = random.choice(unused) if unused else random.choice(candidates)
        used_fallbacks.add(pick)

    ext = pick.rsplit(".", 1)[-1]
    with open(pick, "rb") as f:
        content = f.read()
    return _save_bytes(content, index, ext=ext)


def _layer1_playwright_screenshot(index, scene_text):
    """Video script ke scene text se relevant website dhoondo (search engine
    ke pehle result se), us page ko khol kar screenshot le lo - wahi screenshot
    is scene ka visual clip ban jata hai. LAST RESORT ONLY - see chain notes
    above; a raw webpage screenshot doesn't match the channel's visual style."""
    from playwright.sync_api import sync_playwright

    query = (scene_text or "mystery science").strip()[:100]
    screenshot_bytes = None

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        try:
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            page.set_default_timeout(20000)

            # DuckDuckGo ka HTML-only endpoint - no JS needed, easy to scrape,
            # aur bina API key ke kaam karta hai.
            page.goto(f"https://html.duckduckgo.com/html/?q={query}", wait_until="domcontentloaded")
            link = page.query_selector("a.result__a")
            if not link:
                raise RuntimeError("Playwright: search result nahi mila")
            target_url = link.get_attribute("href")
            if not target_url:
                raise RuntimeError("Playwright: search result ka href empty tha")

            page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)  # cookie banners/lazy images settle hone dein
            screenshot_bytes = page.screenshot(type="png")
        finally:
            browser.close()

    if not screenshot_bytes or len(screenshot_bytes) < 2000:
        raise RuntimeError("Playwright: screenshot khaali/chota tha")
    return _save_bytes(screenshot_bytes, index, ext="png")


def _stock_photo_request(index, scene_text, source: str, used_fallbacks: set):
    query = (scene_text or "mystery science").strip()[:80]
    if source == "pexels":
        key = os.environ.get("PEXELS_API_KEY")
        if not key:
            raise RuntimeError("PEXELS_API_KEY not set - skipping live Pexels layer")
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 15, "orientation": "portrait"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Pexels bad response: {resp.status_code}")
        photos = resp.json().get("photos", [])
        if not photos:
            raise RuntimeError(f"Pexels: no results for '{query}'")
        img_urls = [
            p["src"].get("portrait") or p["src"].get("large2x")
            or p["src"].get("original") or p["src"]["large"]
            for p in photos
        ]

    elif source == "pixabay":
        key = os.environ.get("PIXABAY_API_KEY")
        if not key:
            raise RuntimeError("PIXABAY_API_KEY not set - skipping live Pixabay layer")
        resp = requests.get(
            "https://pixabay.com/api/",
            params={"key": key, "q": query, "image_type": "photo",
                    "orientation": "vertical", "per_page": 15, "safesearch": "true"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Pixabay bad response: {resp.status_code}")
        hits = resp.json().get("hits", [])
        if not hits:
            raise RuntimeError(f"Pixabay: no results for '{query}'")
        img_urls = [h.get("largeImageURL") or h.get("webformatURL") for h in hits]
    else:
        raise ValueError(f"Unknown stock source: {source}")

    with _fallback_lock:
        for url in img_urls:
            if url in used_fallbacks:
                continue
            used_fallbacks.add(url)
            break
        else:
            url = img_urls[0]
    img_resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    if img_resp.status_code != 200 or len(img_resp.content) < 2000:
        raise RuntimeError(f"{source}: failed to download chosen image")
    return _save_bytes(img_resp.content, index)


def _stock_video_request(index, scene_text, source: str, used_fallbacks: set):
    """Download a licensed stock B-roll clip for a scene when available."""
    query = (scene_text or "human body science").strip()[:80]
    if source == "pexels":
        key = os.environ.get("PEXELS_API_KEY")
        if not key:
            raise RuntimeError("PEXELS_API_KEY not set - skipping Pexels video")
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 12, "orientation": "portrait"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Pexels video bad response: {response.status_code}")
        videos = response.json().get("videos", [])
        urls = []
        for video in videos:
            files = video.get("video_files", [])
            # Prefer MP4 clips that are large enough to survive a 9:16 crop.
            candidates = [f for f in files if f.get("file_type") == "video/mp4" and f.get("link")]
            if candidates:
                chosen = max(candidates, key=lambda f: f.get("width", 0) * f.get("height", 0))
                urls.append(chosen["link"])
    elif source == "pixabay":
        key = os.environ.get("PIXABAY_API_KEY")
        if not key:
            raise RuntimeError("PIXABAY_API_KEY not set - skipping Pixabay video")
        response = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": key, "q": query, "per_page": 20, "safesearch": "true"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Pixabay video bad response: {response.status_code}")
        urls = []
        for hit in response.json().get("hits", []):
            variants = hit.get("videos", {})
            chosen = variants.get("large") or variants.get("medium") or variants.get("small")
            if chosen and chosen.get("url"):
                urls.append(chosen["url"])
    else:
        raise ValueError(f"Unknown stock-video source: {source}")

    if not urls:
        raise RuntimeError(f"{source}: no usable B-roll video for '{query}'")
    with _fallback_lock:
        url = next((item for item in urls if item not in used_fallbacks), urls[0])
        used_fallbacks.add(url)
    download = requests.get(url, timeout=60)
    if download.status_code != 200 or len(download.content) < 100_000:
        raise RuntimeError(f"{source}: video download failed or was too small")
    return _save_bytes(download.content, index, ext="mp4"), "video"


def _layer_pexels_video(index, scene_text, used_fallbacks: set):
    return _stock_video_request(index, scene_text, "pexels", used_fallbacks)


def _layer_pixabay_video(index, scene_text, used_fallbacks: set):
    return _stock_video_request(index, scene_text, "pixabay", used_fallbacks)


def _layer2_pexels_live(index, scene_text, used_fallbacks: set):
    return _stock_photo_request(index, scene_text, "pexels", used_fallbacks)


def _layer3_pixabay_live(index, scene_text, used_fallbacks: set):
    return _stock_photo_request(index, scene_text, "pixabay", used_fallbacks)


def _scene_text(scene) -> str:
    if isinstance(scene, dict):
        return scene.get('visual') or scene.get('description') or scene.get('scene') or scene.get('caption') or ''
    return str(scene)


def _generate_one(index, scene, used_hashes: set, used_fallbacks: set):
    scene_text = _scene_text(scene)

    layers = [
        # First use licensed stock B-roll (Pexels, then Pixabay) for genuine motion.
        # If no suitable clip exists, generate a unique AI Horde visual before
        # any other image source, reducing repeated-stock-image dependence.
        ("Pexels-video-first",    lambda: _layer_pexels_video(index, scene_text, used_fallbacks)),
        ("Pixabay-video-second",  lambda: _layer_pixabay_video(index, scene_text, used_fallbacks)),
        ("AI-Horde-image",        lambda: _layer_ai_providers(index, scene_text, ["AI-Horde"])),
        ("Other-AI-image",        lambda: _layer_ai_providers(index, scene_text, [
            "Pollinations-flux", "Pollinations-turbo", "HuggingFace", "Gemini",
            "DeepAI", "ModelsLab", "Replicate",
        ])),
        ("Local-fallback-pool",   lambda: _layer_local_pool(index, used_fallbacks)),
        ("Pexels-image",          lambda: _layer2_pexels_live(index, scene_text, used_fallbacks)),
        ("Pixabay-image",         lambda: _layer3_pixabay_live(index, scene_text, used_fallbacks)),
        *(([("Playwright-screenshot", lambda: _layer1_playwright_screenshot(index, scene_text))]
            if os.environ.get("ENABLE_SCREENSHOT_FALLBACK", "false").lower() == "true" else [])),
    ]

    for name, fn in layers:
        try:
            result = fn()
            path, media_type = result if isinstance(result, tuple) else (result, "image")
            if media_type == "image":
                validate_scene_image(path)
            elif not os.path.isfile(path) or os.path.getsize(path) < 100_000:
                raise RuntimeError(f"{name}: invalid or too-small video clip")
            with open(path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            if file_hash in used_hashes:
                raise RuntimeError(f"{name}: duplicate media; trying next source")
            used_hashes.add(file_hash)

            logger.info(f"Scene {index}: {media_type} generated via {name} -> {path}")
            return {"index": index, "path": path, "source": name, "media_type": media_type}
        except Exception as e:
            logger.error(f"Scene {index}: {name} failed: {e}")
            continue

    raise RuntimeError(f"Scene {index}: All generation layers failed.")


# Public alias — main.py imports this name.
generate_scene_image = _generate_one
