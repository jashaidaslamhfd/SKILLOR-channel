"""
Quick Urdu voice-cloning test.

Poori pipeline chalane se pehle sirf ek Urdu line test karo taake pata chale
Chatterbox (Hindi language_id ke sath) aapki cloned voice mein Urdu theek
bolta hai ya nahi.

USAGE:
    export VOICE_REFERENCE_PATH=assets/my_voice_sample.wav
    python test_urdu_voice.py

Output: test_output/urdu_test.wav - ise sun kar quality check karo.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

os.environ.setdefault("TTS_ENGINE", "chatterbox")
os.environ.setdefault("CHATTERBOX_LANGUAGE", "hi")  # Urdu ka koi official code nahi - Hindi closest hai

from voice_generator import generate_voice  # noqa: E402

TEST_TEXT = "السلام علیکم دوستو، آج ہم بات کریں گے ایک زبردست AI ٹول کے بارے میں جو آپ کا کام بہت آسان بنا دے گا۔"

if __name__ == "__main__":
    ref = os.environ.get("VOICE_REFERENCE_PATH", "").strip()
    if not ref or not os.path.exists(ref):
        print(f"❌ VOICE_REFERENCE_PATH set nahi hai ya file nahi mili: '{ref}'")
        print("   Pehle: export VOICE_REFERENCE_PATH=assets/my_voice_sample.wav")
        sys.exit(1)

    print(f"Testing with reference voice: {ref}")
    print(f"Language: {os.environ['CHATTERBOX_LANGUAGE']}")
    print(f"Text: {TEST_TEXT}")
    print("Generating... (pehli baar model download hoga, thora time lagega)")

    out_path = generate_voice(TEST_TEXT, output_path="test_output/urdu_test.wav")

    print(f"\n✅ Ready: {out_path}")
    print("Ise sun kar decide karo: Urdu sahi/samajh mein aane wali bol rahi hai,")
    print("ya awaaz ajeeb/ghalat pronounce ho rahi hai. Agar theek lage to bulk")
    print("pipeline (python src/main.py) chalao, warna mujhe batao taake hum")
    print("dusra Urdu-specific TTS (ahmedHanzala/urdu-tts) wire karein.")
