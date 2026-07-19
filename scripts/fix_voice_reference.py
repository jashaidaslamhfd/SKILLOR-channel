"""
scripts/fix_voice_reference.py

One-time helper to prepare assets/voice_reference.wav for Chatterbox voice
cloning.

WHY THIS EXISTS
Chatterbox clones best from a SHORT, MONO, clean single-speaker reference
(~10-20 seconds). The original recording here was 61s, stereo, 48kHz, which
makes cloning unreliable / lower quality. This script:
  1. Backs up the original once (voice_reference_original.wav)
  2. Converts stereo -> mono
  3. Resamples 48kHz -> 24kHz (Chatterbox's internal rate)
  4. Auto-picks the loudest continuous 16s window (best clear-speech segment)
  5. Peak-normalizes to 0.95 and writes 16-bit PCM

Run once:  python scripts/fix_voice_reference.py
"""

import os
import numpy as np
import soundfile as sf

SRC = "assets/voice_reference.wav"
BACKUP = "assets/voice_reference_original.wav"
TARGET_SR = 24000
TARGET_SECONDS = 16.0


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"Not found: {SRC}")

    # 1) Back up the original ONCE (never overwrite an existing backup).
    if not os.path.exists(BACKUP):
        import shutil
        shutil.copy(SRC, BACKUP)
        print(f"Backed up original -> {BACKUP}")

    data, sr = sf.read(BACKUP if os.path.exists(BACKUP) else SRC)
    print(f"Original: {data.shape}, {sr} Hz")

    # 2) stereo -> mono
    mono = data.mean(axis=1) if data.ndim == 2 else data

    # 3) resample -> 24kHz (simple linear interpolation, dependency-free)
    if sr != TARGET_SR:
        n_new = int(len(mono) * TARGET_SR / sr)
        x_old = np.linspace(0, 1, len(mono), endpoint=False)
        x_new = np.linspace(0, 1, n_new, endpoint=False)
        mono = np.interp(x_new, x_old, mono).astype(np.float32)
        sr = TARGET_SR

    # 4) pick the loudest continuous TARGET_SECONDS window (best speech chunk)
    win = int(TARGET_SECONDS * sr)
    if len(mono) > win:
        step = int(sr * 0.5)
        best_i, best_rms = 0, -1.0
        for i in range(0, len(mono) - win, step):
            seg = mono[i:i + win]
            rms = float(np.sqrt(np.mean(seg ** 2)))
            if rms > best_rms:
                best_rms, best_i = rms, i
        clip = mono[best_i:best_i + win]
        print(f"Picked window @ {round(best_i / sr, 1)}s (rms {round(best_rms, 4)})")
    else:
        clip = mono

    # 5) peak-normalize and write 16-bit PCM mono
    peak = float(np.abs(clip).max())
    if peak > 0:
        clip = (clip / peak * 0.95).astype(np.float32)

    sf.write(SRC, clip, sr, subtype="PCM_16")
    info = sf.info(SRC)
    print(f"Wrote {SRC}: {round(info.duration, 1)}s, {info.channels}ch, {info.samplerate}Hz")


if __name__ == "__main__":
    main()
