"""
caption_generator.py
Edge TTS ke word-boundary timestamps se .srt caption file banata hai,
chhote-chhote 3-4 lafz wale groups mein (Shorts style synced captions).
"""
from datetime import timedelta


def _format_srt_time(seconds: float) -> str:
    td = timedelta(seconds=max(0, seconds))
    total_ms = int(td.total_seconds() * 1000)
    hrs, rem = divmod(total_ms, 3_600_000)
    mins, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"


class CaptionGenerator:
    def __init__(self, words_per_caption: int = 3):
        self.words_per_caption = words_per_caption

    def build_srt(self, word_boundaries: list, output_path: str = "output/captions.srt") -> str:
        groups = [
            word_boundaries[i:i + self.words_per_caption]
            for i in range(0, len(word_boundaries), self.words_per_caption)
        ]

        srt_lines = []
        for idx, group in enumerate(groups, start=1):
            start = group[0]["start"]
            end = group[-1]["start"] + group[-1]["duration"]
            text = " ".join(w["text"] for w in group)

            srt_lines.append(str(idx))
            srt_lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
            srt_lines.append(text)
            srt_lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))

        return output_path

    def build_word_timeline(self, word_boundaries: list) -> list:
        """FFmpeg drawtext/ASS based highlight-style captions ke liye raw timeline."""
        return [
            {"text": w["text"], "start": round(w["start"], 3), "end": round(w["start"] + w["duration"], 3)}
            for w in word_boundaries
        ]
