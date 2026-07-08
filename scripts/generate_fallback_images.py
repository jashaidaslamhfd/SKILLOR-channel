"""
generate_fallback_images.py

One-time helper to bulk-generate ~500 UNIQUE AI images for the
assets/fallback_images/ pool (DARK BODY & BRAIN MYSTERY niche).

Run from the repo root:
    python scripts/generate_fallback_images.py
"""

import os
import sys
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from image_providers import PROVIDER_REGISTRY, available_providers, RateLimitError

OUTPUT_DIR = "assets/fallback_images"
TARGET_COUNT = 500

# NEW: DARK BODY & BRAIN SCIENCE BUILDING BLOCKS
SUBJECTS = [
    "human veins and circulatory system", "human brain scan", "bone marrow making blood cells",
    "human heart anatomy", "nervous system neurons", "human DNA strand",
    "stomach and gut brain connection", "human lungs breathing",
    "microscopic blood cells", "human skeleton", "brain synapses firing",
    "human organs dark background", "spinal cord", "eye anatomy closeup",
    "human muscles", "cell division", "medical 3d render of human body",
    "brain waves eeg", "human skin layers", "intestines and digestion",
]

SETTINGS = [
    "on dark background with blue glow", "in a medical lab with dramatic lighting",
    "with cinematic lighting and fog", "on black background, scientific",
    "in a hospital with neon lights", "3d render, dark sci-fi style",
    "microscopic view with dramatic shadows", "anatomical illustration dark theme",
    "floating in dark space with particles", "x-ray style dark background",
]

STYLES = [
    "photorealistic, 3d anatomy, dark lighting, high detail",
    "medical illustration, dark blue and red tones, cinematic",
    "scientific render, dramatic lighting, ultra detailed",
    "dark moody, neon accents, photorealistic anatomy",
    "cinematic, black background, glowing veins",
    "realistic human anatomy, dark hospital lighting",
]

def build_prompt():
    subject = random.choice(SUBJECTS)
    setting = random.choice(SETTINGS)
    style = random.choice(STYLES)
    scene_text = f"{subject} {setting}, {style}"
    return scene_text.replace(" ", "_"), scene_text

def already_have():
    if not os.path.isdir(OUTPUT_DIR):
        return 0
    return len([f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))])

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    count = already_have()
    print(f"Starting with {count} images already in {OUTPUT_DIR}")

    providers = available_providers()
    if not providers:
        print("❌ No providers available")
        return

    print(f"Using {len(providers)} available provider(s): " + ", ".join(p["name"] for p in providers))

    provider_idx = 0
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 40

    while count < TARGET_COUNT:
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            print(f"\nStopping: {MAX_CONSECUTIVE_FAILURES} failures in a row. Re-run to resume from {count}/{TARGET_COUNT}")
            break

        provider = providers[provider_idx % len(providers)]
        provider_idx += 1

        prompt, scene_text = build_prompt()
        seed = random.randint(1, 999)

        try:
            image_bytes, ext = provider["generate"](prompt, seed, scene_text)
        except RateLimitError as e:
            print(f"  ⚠️ {provider['name']} rate-limited: {e}")
            consecutive_failures += 1
            continue
        except Exception as e:
            print(f"  ❌ {provider['name']} failed: {e}")
            consecutive_failures += 1
            continue

        fname = f"darkbody_{count:04d}_{seed}.{ext}" # NAME BHI CHANGE
        dest = os.path.join(OUTPUT_DIR, fname)
        with open(dest, "wb") as f:
            f.write(image_bytes)
        count += 1
        consecutive_failures = 0
        print(f"  [{count}/{TARGET_COUNT}] saved {fname} via {provider['name']}")

        time.sleep(1)

    print(f"\nDone. Total unique DARK BODY images: {count}")

if __name__ == "__main__":
    main()
