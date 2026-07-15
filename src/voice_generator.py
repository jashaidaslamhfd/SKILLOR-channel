import os
import numpy as np
import soundfile as sf
import logging
import re
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PRIMARY ENGINE: Chatterbox (Resemble AI, MIT license - safe for a
# monetized channel).
#
# Why Chatterbox over Kokoro: Kokoro has no emotion/delivery control at all
# - every line comes out at the same flat intensity regardless of content,
# which is exactly why the channel's "dark mystery" voiceovers read as
# monotone. Chatterbox's `exaggeration` parameter is the first open-source
# control of its kind for this, so it's what actually fixes the tone
# instead of just changing which model renders the same flat delivery.
#
# Lazy-loaded on first use (not at import time) so a missing pip install or
# a failed model download doesn't crash the whole pipeline before it even
# starts - _get_chatterbox() catches that, and every call in this file
# falls back to Kokoro per-segment if Chatterbox is unavailable or a
# specific generation call fails. One bad Chatterbox call should never take
# a whole video down.
# ---------------------------------------------------------------------------
_chatterbox_model = None
_chatterbox_load_failed = False

# CORRECTED per Chatterbox's own docs: "higher exaggeration tends to speed
# up speech." The previous settings here (exaggeration=0.7, cfg_weight=0.35)
# were following Chatterbox's own "dramatic delivery" recipe, but that
# combination is documented to net out FASTER than default, not slower -
# which matches the "has emotion but talks too fast, loses the mystery
# vibe" feedback. Dialing exaggeration back down and cfg_weight back up
# keeps some expressiveness without the speedup side effect. Reliable
# pacing control now comes from CHATTERBOX_TEMPO below instead of fighting
# the model's internal speed/emotion coupling.
CHATTERBOX_EXAGGERATION = 0.6
CHATTERBOX_CFG_WEIGHT = 0.5
CHATTERBOX_TEMPERATURE = 0.8

# Chatterbox has no direct "speed" parameter like Kokoro does, so this
# applies an explicit pitch-preserving tempo change via ffmpeg after
# generation (ffmpeg's atempo filter) - this is what actually delivers a
# slow, deliberate "dark mystery" pace reliably, rather than relying on
# exaggeration/cfg_weight side effects. 0.85 = 15% slower, same pitch.
# Lower = slower/more ominous; 1.0 = no change. Valid ffmpeg atempo range
# per call is 0.5-2.0.
CHATTERBOX_TEMPO = 0.85

# Voice clone reference. Default is your own voice sample in assets.
# REQUIRE_CLONED_VOICE=true means: if cloned voice cannot be used, do NOT
# silently publish with another voice. Fail the pipeline instead.
VOICE_REFERENCE_PATH = os.environ.get("VOICE_REFERENCE_PATH", "assets/voice_reference.wav")
REQUIRE_CLONED_VOICE = os.environ.get("REQUIRE_CLONED_VOICE", "true").lower() == "true"


def _get_chatterbox():
    """Loads the Chatterbox model once and caches it. Returns None (and
    remembers not to retry) if loading fails for any reason - missing
    package, no internet for the first-run model download, out-of-memory
    on a CPU-only runner, etc."""
    global _chatterbox_model, _chatterbox_load_failed
    if _chatterbox_model is not None or _chatterbox_load_failed:
        return _chatterbox_model
    try:
        import torch
        from chatterbox.tts import ChatterboxTTS
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Chatterbox TTS model on {device} (first call only, then cached)...")
        _chatterbox_model = ChatterboxTTS.from_pretrained(device=device)
        logger.info("Chatterbox loaded successfully.")
    except Exception as e:
        logger.error(f"Chatterbox unavailable ({e}) - every segment will fall back to Kokoro.")
        _chatterbox_load_failed = True
        _chatterbox_model = None
    return _chatterbox_model


def _apply_tempo(audio: np.ndarray, sr: int, tempo: float) -> np.ndarray:
    """Pitch-preserving speed change via ffmpeg's atempo filter. Writes to a
    temp wav, runs ffmpeg, reads the result back. Returns the original
    audio unchanged if ffmpeg isn't available or the call fails, so a
    pacing tweak can never be the reason a whole segment fails."""
    if tempo == 1.0:
        return audio
    try:
        import subprocess
        import tempfile
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "in.wav")
            out_path = os.path.join(tmpdir, "out.wav")
            sf.write(in_path, audio, sr)
            result = subprocess.run(
                [ffmpeg_exe, "-y", "-i", in_path, "-filter:a", f"atempo={tempo}", out_path],
                capture_output=True, timeout=30,
            )
            if result.returncode != 0 or not os.path.exists(out_path):
                logger.warning(f"ffmpeg tempo adjustment failed, using original pace: {result.stderr[:200]}")
                return audio
            stretched, _ = sf.read(out_path, dtype="float32")
            return stretched
    except Exception as e:
        logger.warning(f"Tempo adjustment failed ({e}), using original pace")
        return audio


def _synthesize_chatterbox(text: str):
    """Returns (audio: np.ndarray float32, sample_rate: int)."""
    model = _get_chatterbox()
    if model is None:
        raise RuntimeError("Chatterbox model not loaded")

    kwargs = dict(
        exaggeration=CHATTERBOX_EXAGGERATION,
        cfg_weight=CHATTERBOX_CFG_WEIGHT,
        temperature=CHATTERBOX_TEMPERATURE,
    )

    if os.path.exists(VOICE_REFERENCE_PATH):
        kwargs["audio_prompt_path"] = VOICE_REFERENCE_PATH
        logger.info(f"Using cloned voice reference: {VOICE_REFERENCE_PATH}")
    elif REQUIRE_CLONED_VOICE:
        raise RuntimeError(
            f"Required cloned voice reference not found: {VOICE_REFERENCE_PATH}. "
            "Add your clean WAV file or set REQUIRE_CLONED_VOICE=false."
        )

    wav = model.generate(text, **kwargs)
    audio = wav.squeeze().detach().cpu().numpy().astype(np.float32)

    if np.isnan(audio).any():
        audio = np.nan_to_num(audio, 0.0)
    peak = np.abs(audio).max()
    if peak > 1.0:
        audio = audio / peak * 0.95

    audio = _apply_tempo(audio, model.sr, CHATTERBOX_TEMPO)

    return audio, model.sr


# ---------------------------------------------------------------------------
# FALLBACK ENGINE: Kokoro (Apache 2.0).
# When REQUIRE_CLONED_VOICE=true, fallback is disabled for production safety.
# ---------------------------------------------------------------------------
_kokoro_tts = None
_kokoro_load_failed = False


def _get_kokoro():
    """Lazy-loads Kokoro only when actually needed as a fallback."""
    global _kokoro_tts, _kokoro_load_failed
    if _kokoro_tts is not None or _kokoro_load_failed:
        return _kokoro_tts
    try:
        from kokoro import KPipeline
        logger.info("Loading Kokoro TTS model (fallback engine, first use only)...")
        _kokoro_tts = KPipeline(lang_code='f')  # 'f' = French
        logger.info("Kokoro loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Kokoro: {e}")
        _kokoro_load_failed = True
        _kokoro_tts = None
    return _kokoro_tts


KOKORO_SAMPLE_RATE = 24000
SILENCE_PAD_SEC = 0.25


def add_mystery_pauses(text: str) -> str:
    """Adds a beat of suspense after dark hooks/reveals for retention.

    Neither Kokoro nor Chatterbox reads SSML tags like '<break time="0.5s"/>'
    - both read plain text/punctuation, so a literal SSML tag would get
    spoken aloud as text. Real neural TTS models DO respect
    punctuation-driven pauses though, so we use an ellipsis (natural
    trailing-off pause) or a short standalone clause instead - actually
    audible, not spoken as text.
    """
    # French-first pause shaping.
    text = re.sub(r'\bmais\b', 'mais...', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpourtant\b', 'pourtant...', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvoici\b', 'voici...', text, flags=re.IGNORECASE)
    text = re.sub(r'\ben silence\b', 'en silence...', text, flags=re.IGNORECASE)

    # Already-present ".." -> stretch into a longer natural pause.
    text = re.sub(r'(?<!\.)\.\.(?!\.)', '...', text)

    return text


def _synthesize_kokoro(text: str, voice: str, speed: float):
    """Returns (audio: np.ndarray float32, sample_rate: int)."""
    kokoro = _get_kokoro()
    if not kokoro:
        raise RuntimeError("Kokoro TTS model not loaded. Check Kokoro installation.")

    generator = kokoro(text, voice=voice, speed=speed)
    chunks = []
    for gs, ps, audio in generator:
        if audio is not None:
            chunks.append(audio)

    if not chunks:
        raise RuntimeError(f"Kokoro ne audio generate nahi kiya for: {text[:50]}...")

    full_audio = np.concatenate(chunks)
    if np.isnan(full_audio).any():
        full_audio = np.nan_to_num(full_audio, 0.0)

    max_val = np.abs(full_audio).max()
    if max_val > 1.0:
        full_audio = full_audio / max_val * 0.95

    return full_audio, KOKORO_SAMPLE_RATE


def _synthesize(text: str, voice: str = "ff_siwis", speed: float = 0.95):
    """Chatterbox first for cloned expressive delivery.

    If REQUIRE_CLONED_VOICE=true, any Chatterbox/voice-reference failure
    raises an error instead of falling back to a different voice. This
    protects channel branding because the user requested only their cloned
    voice.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    text_with_pauses = add_mystery_pauses(text)

    try:
        audio, sr = _synthesize_chatterbox(text_with_pauses)
        return audio, sr, "chatterbox"
    except Exception as e:
        if REQUIRE_CLONED_VOICE:
            raise RuntimeError(f"Cloned voice generation failed and fallback voice is disabled: {e}")
        logger.warning(f"Chatterbox synth failed ({e}) - falling back to Kokoro for this segment.")
        audio, sr = _synthesize_kokoro(text_with_pauses, voice, speed)
        return audio, sr, "kokoro"


def generate_voice(
    text: str,
    voice: str = "ff_siwis",
    output_path: str = "output/voice.wav",
    speed: float = 0.95,
) -> str:
    """French cloned dark-science voice: deep, slow, mysterious."""
    try:
        logger.info(f"Generating DARK cloned voiceover (voice='{voice}', speed={speed})...")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        audio, sr, engine = _synthesize(text, voice, speed)
        sf.write(output_path, audio, sr)
        logger.info(f"Voice saved via {engine}: {output_path} ({len(audio)} samples, {len(audio)/sr:.2f}s)")
        return output_path
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        raise RuntimeError(f"Voice generation error: {e}")


def generate_voice_segments(
    scenes: List[dict],
    voice: str = "ff_siwis",  # only used if a segment falls back to Kokoro
    output_dir: str = "output/segments",
    speed: float = 0.95,     # only used if a segment falls back to Kokoro
) -> List[Dict]:
    """
    Each scene gets its own audio, generated via Chatterbox using the cloned
    voice reference. If REQUIRE_CLONED_VOICE=true, any failure stops the run.
    """
    os.makedirs(output_dir, exist_ok=True)
    segments = []
    engine_counts = {}

    for i, scene in enumerate(scenes):
        caption = scene.get('caption', '').strip() if isinstance(scene, dict) else str(scene)
        if not caption:
            caption = " "

        try:
            audio, sr, engine = _synthesize(caption, voice, speed)
        except Exception as e:
            if REQUIRE_CLONED_VOICE:
                raise RuntimeError(f"Segment {i+1} cloned voice generation failed: {e}")
            logger.error(f"Segment {i+1} TTS failed on both engines: {e} - inserting short silence instead")
            audio = np.zeros(int(KOKORO_SAMPLE_RATE * 1.5), dtype=np.float32)
            sr = KOKORO_SAMPLE_RATE
            engine = "silence"

        engine_counts[engine] = engine_counts.get(engine, 0) + 1
        path = os.path.join(output_dir, f"seg_{i}.wav")
        sf.write(path, audio, sr)
        duration = len(audio) / sr

        segments.append({
            "path": path,
            "duration": duration,
            "caption": caption,
            "tts_engine": engine,
        })
        logger.info(f"Segment {i+1}/{len(scenes)} via {engine}: {duration:.2f}s - \"{caption[:50]}...\"")

    total = sum(s['duration'] for s in segments)
    logger.info(f"Total DARK voiceover duration: {total:.2f}s | engines used: {engine_counts}")
    return segments
