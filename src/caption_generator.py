"""
caption_generator.py
Word boundaries se .srt caption file banata hai (Shorts style)
"""
import os
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def _format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp format"""
    td = timedelta(seconds=max(0, seconds))
    total_ms = int(td.total_seconds() * 1000)
    hrs, rem = divmod(total_ms, 3_600_000)
    mins, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"


class CaptionGenerator:
    def __init__(self, words_per_caption: int = 3, min_duration: float = 0.5):
        """Initialize Caption Generator"""
        self.words_per_caption = words_per_caption
        self.min_duration = min_duration
        logger.info(f"✅ CaptionGenerator initialized: {words_per_caption} words per caption")
    
    def build_srt(self, word_boundaries: list, output_path: str = "output/captions.srt") -> str:
        """Build SRT file from word boundaries"""
        if not word_boundaries:
            logger.warning("No word boundaries provided, creating empty captions")
            word_boundaries = [{"text": "No captions", "start": 0, "duration": 1}]
        
        # Group words
        groups = []
        for i in range(0, len(word_boundaries), self.words_per_caption):
            group = word_boundaries[i:i + self.words_per_caption]
            start = group[0]["start"]
            end = group[-1]["start"] + group[-1]["duration"]
            
            # Ensure minimum duration
            if end - start < self.min_duration:
                end = start + self.min_duration
            
            text = " ".join(w["text"] for w in group)
            groups.append({
                "start": start,
                "end": end,
                "text": text
            })
        
        # Write SRT
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        srt_lines = []
        for idx, group in enumerate(groups, start=1):
            srt_lines.append(str(idx))
            srt_lines.append(f"{_format_srt_time(group['start'])} --> {_format_srt_time(group['end'])}")
            srt_lines.append(group["text"])
            srt_lines.append("")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))
        
        logger.info(f"✅ Captions saved: {output_path} ({len(groups)} captions)")
        return output_path
    
    def build_word_timeline(self, word_boundaries: list) -> list:
        """Return raw word timeline for highlighting"""
        return [
            {
                "text": w["text"],
                "start": round(w["start"], 3),
                "end": round(w["start"] + w["duration"], 3)
            }
            for w in word_boundaries
        ]


if __name__ == "__main__":
    # Test caption generator
    test_boundaries = [
        {"text": "Salam", "start": 0.0, "duration": 0.3},
        {"text": "dosto", "start": 0.3, "duration": 0.2},
        {"text": "Aaj", "start": 0.5, "duration": 0.2},
    ]
    gen = CaptionGenerator()
    gen.build_srt(test_boundaries, "output/test_captions.srt")
