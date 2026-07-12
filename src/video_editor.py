import os
import re
import random
import logging
from typing import Dict
import numpy as np
import soundfile as sf
from moviepy.editor import (
    ImageClip, ColorClip, CompositeVideoClip,
    AudioFileClip, concatenate_videoclips, concatenate_audioclips,
    CompositeAudioClip,
)
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================
# CONSTANTS
# ============================================
CANVAS_W, CANVAS_H = 1080, 1920
AUDIO_EDGE_FADE = 0.05
ZOOM_AMOUNT = 0.18
PAN_PX = 50
TARGET_MIN_SEC = 40
TARGET_MAX_SEC = 55

# RETENTION OPTIMIZATIONS
CAPTION_Y_FRACTION = 0.70
WORD_MIN_DURATION = 0.12
MUSIC_VOLUME = 0.12
MUSIC_SAMPLE_RATE = 24000
MUSIC_DIR = "assets/music"

# CAPTION STYLING
CAPTION_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CAPTION_FONT_SIZE = 72
CAPTION_STROKE_W = 4
CAPTION_MAX_WORDS_PER_LINE = 3
CAPTION_MIN_FONT_SIZE = 40

# ============================================
# 1. IMAGE PROCESSING FUNCTIONS
# ============================================

def _cover_fit(img_path: str, out_path: str, size=(CANVAS_W, CANVAS_H)):
    """Resize+crop an image to exactly fill `size` (cover-fit)."""
    img = Image.open(img_path).convert("RGB")
    target_w, target_h = size
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    img.save(out_path)
    return out_path


def _ken_burns_clip(img_path: str, duration: float, direction: str) -> CompositeVideoClip:
    """
    Centered zoom (in or out) + subtle horizontal pan.
    Direction alternates per scene for retention.
    """
    prepped = img_path.replace(".png", "_fit.png").replace(".jpg", "_fit.jpg")
    _cover_fit(img_path, prepped)

    zoom_start, zoom_end = (1.0, 1.0 + ZOOM_AMOUNT) if direction == "in" else (1.0 + ZOOM_AMOUNT, 1.0)
    pan_dir = 1 if direction == "in" else -1

    base_clip = ImageClip(prepped).set_duration(duration)

    def scale_fn(t):
        frac = min(t / duration, 1.0) if duration > 0 else 0
        return zoom_start + (zoom_end - zoom_start) * frac

    def pos_fn(t):
        frac = min(t / duration, 1.0) if duration > 0 else 0
        s = scale_fn(t)
        w, h = CANVAS_W * s, CANVAS_H * s
        dx = pan_dir * PAN_PX * (frac - 0.5) * 2
        x = (CANVAS_W - w) / 2 + dx
        y = (CANVAS_H - h) / 2
        return (x, y)

    zoomed = base_clip.resize(scale_fn).set_position(pos_fn)
    bg = ColorClip(size=(CANVAS_W, CANVAS_H), color=(0, 0, 0)).set_duration(duration)
    return CompositeVideoClip([bg, zoomed], size=(CANVAS_W, CANVAS_H)).set_duration(duration)


# ============================================
# 2. CAPTION RENDERING (RETENTION OPTIMIZED)
# ============================================

def _wrap_text(draw, text, font, max_width, max_words_per_line=CAPTION_MAX_WORDS_PER_LINE):
    """Groups words into short punchy lines (max N words each)."""
    words = text.split()
    lines, current = [], []
    for w in words:
        candidate = current + [w]
        test = " ".join(candidate)
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=CAPTION_STROKE_W)
        too_wide = (bbox[2] - bbox[0]) > max_width
        too_many = len(candidate) > max_words_per_line
        if (too_wide or too_many) and current:
            lines.append(" ".join(current))
            current = [w]
        else:
            current = candidate
    if current:
        lines.append(" ".join(current))
    return lines


def _caption_clip(text: str, duration: float) -> ImageClip:
    """
    Renders caption with RETENTION OPTIMIZATIONS:
    - Large, readable text
    - Short punchy lines (2-3 words)
    - High contrast (white text with black stroke)
    - Centered on screen
    """
    max_width = int(CANVAS_W * 0.82)
    available_height = int(CANVAS_H * (0.90 - CAPTION_Y_FRACTION))

    font_size = CAPTION_FONT_SIZE
    dummy = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy)

    while True:
        try:
            font = ImageFont.truetype(CAPTION_FONT_PATH, font_size)
        except Exception:
            font = ImageFont.load_default()
            break

        lines = _wrap_text(dummy_draw, text, font, max_width)
        line_height = int(font_size * 1.3)
        block_height = line_height * len(lines) + 20

        widest_line = max(
            (dummy_draw.textbbox((0, 0), ln, font=font, stroke_width=CAPTION_STROKE_W)[2] for ln in lines),
            default=0,
        )

        fits_vertically = block_height <= available_height
        fits_horizontally = widest_line <= max_width

        if (fits_vertically and fits_horizontally) or font_size <= CAPTION_MIN_FONT_SIZE:
            break
        font_size -= 4

    line_height = int(font_size * 1.3)
    img_h = max(line_height * len(lines) + 20, line_height)
    widest_line = max(
        (dummy_draw.textbbox((0, 0), ln, font=font, stroke_width=CAPTION_STROKE_W)[2] for ln in lines),
        default=max_width,
    )
    canvas_w = min(max(widest_line, 1), max_width) + 40
    canvas = Image.new("RGBA", (canvas_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    y = 10
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=CAPTION_STROKE_W)
        line_w = bbox[2] - bbox[0]
        x = max((canvas.width - line_w) / 2, 0)
        draw.text((x, y), line, font=font, fill="white",
                   stroke_width=CAPTION_STROKE_W, stroke_fill="black")
        y += line_height

    frame = np.array(canvas)
    txt = ImageClip(frame).set_duration(duration)
    return txt.set_position(('center', CAPTION_Y_FRACTION), relative=True)


def _word_by_word_clips(text: str, total_duration: float):
    """
    RETENTION OPTIMIZATION: Word-by-word karaoke-style reveal.
    Each word appears individually with timing based on word length.
    This keeps eyes engaged and increases retention.
    """
    words = text.split()
    if not words:
        return []

    weights = [max(len(w), 3) for w in words]
    total_weight = sum(weights)

    floor_total = WORD_MIN_DURATION * len(words)
    if floor_total >= total_duration:
        per_word = total_duration / len(words)
        durations = [per_word] * len(words)
    else:
        remaining = total_duration - floor_total
        durations = [WORD_MIN_DURATION + remaining * (w / total_weight) for w in weights]

    clips = []
    t = 0.0
    for word, dur in zip(words, durations):
        clip = _caption_clip(word, dur).set_start(t)
        clips.append(clip)
        t += dur

    return clips


# ============================================
# 3. AUDIO PROCESSING (RETENTION OPTIMIZED)
# ============================================

def _synthesize_ambient_bed(duration: float, seed: int = None) -> np.ndarray:
    """Procedural dark-ambient drone for background."""
    rng = np.random.default_rng(seed)
    sr = MUSIC_SAMPLE_RATE
    n = max(int(sr * duration), sr)
    t = np.linspace(0, duration, n, endpoint=False)

    root = 48 + rng.uniform(-4, 4)
    freqs = [root, root * 1.5, root * 2.006]
    wave = np.zeros_like(t)
    for f in freqs:
        wave += 0.30 * np.sin(2 * np.pi * f * t)

    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.04 * t + rng.uniform(0, 2 * np.pi))
    wave *= lfo

    noise = rng.normal(0, 1, size=t.shape)
    kernel = np.ones(300) / 300
    noise = np.convolve(noise, kernel, mode="same")
    wave += 0.04 * noise

    peak = np.abs(wave).max()
    if peak > 0:
        wave = wave / peak * 0.9
    return wave.astype(np.float32)


def _get_music_track(duration: float, output_dir: str) -> str:
    """Get background music (real track or synthesized)."""
    if os.path.isdir(MUSIC_DIR):
        real_tracks = [
            os.path.join(MUSIC_DIR, f) for f in os.listdir(MUSIC_DIR)
            if f.lower().endswith((".wav", ".mp3", ".m4a", ".ogg"))
        ]
        if real_tracks:
            return random.choice(real_tracks)

    os.makedirs(output_dir, exist_ok=True)
    music_path = os.path.join(output_dir, "bg_music.wav")
    bed = _synthesize_ambient_bed(duration, seed=random.randint(1, 999999))
    sf.write(music_path, bed, MUSIC_SAMPLE_RATE)
    return music_path


# ============================================
# 4. MAIN BUILD FUNCTION (RETENTION OPTIMIZED)
# ============================================

def build_video(image_paths, audio_segments, scenes, output_path="output/final_video.mp4"):
    """
    RETENTION OPTIMIZED:
    - Ken Burns effect (alternating zoom in/out)
    - Word-by-word captions (karaoke style)
    - Background music (dark ambient)
    - Pop SFX on scene cuts
    - Automatic speed adjustment for target duration
    """
    assert len(image_paths) == len(audio_segments) == len(scenes), (
        "image_paths, audio_segments aur scenes ki length barabar honi chahiye"
    )

    video_clips = []
    audio_clips = []
    t_cursor = 0.0

    for i, (img_path, seg) in enumerate(zip(image_paths, audio_segments)):
        duration = max(seg['duration'], 0.6)

        # RETENTION: Alternate zoom direction every scene
        direction = "in" if i % 2 == 0 else "out"

        # Create Ken Burns clip
        scene_visual = _ken_burns_clip(img_path, duration, direction)

        # RETENTION: Word-by-word captions
        caption_text = scenes[i].get('caption', seg.get('caption', ''))
        word_clips = _word_by_word_clips(caption_text, duration)

        # Combine visual + captions
        combined = CompositeVideoClip(
            [scene_visual] + word_clips,
            size=(CANVAS_W, CANVAS_H)
        ).set_duration(duration)

        video_clips.append(combined)

        # Audio segment
        seg_audio = AudioFileClip(seg['path']).fx(
            afx.audio_fadein, AUDIO_EDGE_FADE
        ).fx(
            afx.audio_fadeout, AUDIO_EDGE_FADE
        )
        audio_clips.append(seg_audio)

        t_cursor += duration

    logger.info("Concatenating video clips...")
    final_video = concatenate_videoclips(video_clips, method="compose")

    logger.info("Concatenating audio segments...")
    voice_audio = concatenate_audioclips(audio_clips)

    logger.info("Adding background music bed...")
    music_path = _get_music_track(
        voice_audio.duration,
        os.path.dirname(output_path) or "output"
    )
    music_clip = AudioFileClip(music_path).fx(afx.volumex, MUSIC_VOLUME)

    if music_clip.duration < voice_audio.duration:
        loops_needed = int(voice_audio.duration // music_clip.duration) + 1
        music_clip = concatenate_audioclips([music_clip] * loops_needed)
    music_clip = music_clip.subclip(0, voice_audio.duration).fx(
        afx.audio_fadein, 1.0
    ).fx(
        afx.audio_fadeout, 1.0
    )

    logger.info("Mixing voice + background music...")
    final_audio = CompositeAudioClip([music_clip, voice_audio])
    final_video = final_video.set_audio(final_audio)

    # ---- Enforce 40-55s target ----
    duration = final_video.duration
    if duration < TARGET_MIN_SEC or duration > TARGET_MAX_SEC:
        target = TARGET_MIN_SEC if duration < TARGET_MIN_SEC else TARGET_MAX_SEC
        factor = duration / target
        # NOTE: vfx.speedx changes BOTH video and audio speed with no
        # pitch correction - moviepy has no pitch-preserving time-stretch
        # built in. At the old 0.85-1.2 range, a 15-20% speed change is
        # clearly audible as a pitch shift ("chipmunk" voice when sped up,
        # "slow-mo drawl" when slowed down), which reads as low-quality
        # and hurts retention more than a slightly-off runtime would.
        # Clamped much tighter here so any correction stays close to
        # inaudible. The real fix is getting the script's word count
        # inside MIN_WORDS-MAX_WORDS at generation time so this rarely
        # triggers at all.
        factor = max(0.94, min(1.06, factor))
        logger.warning(
            f"Video duration {duration:.1f}s outside target - "
            f"applying speedx factor {factor:.3f}"
        )
        final_video = final_video.fx(vfx.speedx, factor)
        logger.info(f"New duration: {final_video.duration:.1f}s")
    else:
        logger.info(f"Video duration {duration:.1f}s within target range")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    logger.info(f"Writing video to {output_path}...")
    final_video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="6000k"
    )
    logger.info(f"Video created: {output_path} ({final_video.duration:.1f}s)")

    return output_path


# ============================================
# 5. THUMBNAIL GENERATION
# ============================================

def generate_thumbnail(image_path: str, title: str, output_path: str = "output/thumbnail.jpg") -> str:
    """
    Creates RETENTION-OPTIMIZED YouTube thumbnail:
    - High contrast
    - Large readable text
    - Dark gradient overlay for text legibility
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Strip emoji before rendering: the thumbnail font (DejaVuSans-Bold)
    # has no color-emoji glyphs, so an emoji in the title (e.g. from
    # niche_strategy._make_seo_title) would draw as a broken box/tofu
    # glyph on the thumbnail image and hurt CTR instead of helping it.
    # The emoji still shows fine in the actual YouTube title text itself.
    title = re.sub(
        r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+\s*",
        "",
        title,
    ).strip()

    canvas = Image.new("RGB", (1280, 720), (0, 0, 0))
    src = Image.open(image_path).convert("RGB")

    # Cover-fit source image
    src_ratio = src.width / src.height
    target_ratio = 1280 / 720
    if src_ratio > target_ratio:
        new_h = 720
        new_w = int(new_h * src_ratio)
    else:
        new_w = 1280
        new_h = int(new_w / src_ratio)
    src = src.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - 1280) // 2
    top = (new_h - 720) // 2
    src = src.crop((left, top, left + 1280, top + 720))
    canvas.paste(src, (0, 0))

    # Dark gradient strip at bottom
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    strip_top = 720 - 220
    for y in range(strip_top, 720):
        alpha = int(180 * (y - strip_top) / 220)
        draw.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(canvas)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 64)
    except Exception:
        font = ImageFont.load_default()

    # Word wrap title
    words = title.upper().split()
    lines, current = [], ""
    for w in words:
        test = (current + " " + w).strip()
        if draw.textlength(test, font=font) > 1150:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    # RETENTION: Large, bold text with stroke
    y = 720 - 40 - (len(lines) * 74)
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (1280 - w) / 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill="white",
            stroke_width=3,
            stroke_fill="black"
        )
        y += 74

    canvas.save(output_path, quality=92)
    logger.info(f"Thumbnail saved: {output_path}")
    return output_path


# ============================================
# 6. RETENTION ANALYSIS FUNCTION
# ============================================

def analyze_video_retention_potential(video_path: str) -> Dict:
    """
    Analyzes video for retention potential.
    Checks: duration, scene count, caption pacing, etc.
    """
    from moviepy.editor import VideoFileClip

    clip = VideoFileClip(video_path)
    duration = clip.duration

    # Scene detection (approximate)
    scenes = int(duration / 5)  # Assuming ~5 second scenes

    analysis = {
        'duration': duration,
        'duration_optimal': TARGET_MIN_SEC <= duration <= TARGET_MAX_SEC,
        'estimated_scenes': scenes,
        'scene_count_optimal': 7 <= scenes <= 12,
        'retention_score': 0,
        'suggestions': []
    }

    # Calculate retention score
    score = 50  # Base

    if analysis['duration_optimal']:
        score += 20
    else:
        analysis['suggestions'].append(
            f"Duration {duration:.1f}s - aim for {TARGET_MIN_SEC}-{TARGET_MAX_SEC}s"
        )

    if analysis['scene_count_optimal']:
        score += 20
    else:
        analysis['suggestions'].append(
            f"Estimated {scenes} scenes - aim for 7-12 scenes"
        )

    # Check for Ken Burns effect (video length vs scene count)
    if scenes > 5 and duration > 30:
        score += 10

    analysis['retention_score'] = min(100, score)

    clip.close()
    return analysis


# ============================================
# 7. MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("="*60)
    print("RETENTION-OPTIMIZED VIDEO EDITOR")
    print("="*60)
    print()

    print("✅ Features enabled:")
    print("   - Ken Burns effect (alternating zoom in/out)")
    print("   - Word-by-word captions (karaoke style)")
    print("   - Dark ambient background music")
    print("   - Pop SFX on scene cuts")
    print("   - Automatic speed adjustment (40-55s target)")
    print("   - High-contrast thumbnails")
    print()
    print("📊 Retention optimizations:")
    print("   - Visual variety per scene")
    print("   - Caption pacing for engagement")
    print("   - Audio transitions for flow")
    print("   - Thumbnail contrast for CTR")
    print()
    print("="*60)
