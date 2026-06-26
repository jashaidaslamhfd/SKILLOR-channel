"""
pipeline.py
Pura SKILLOR automation pipeline ek jagah orchestrate karta hai:
script -> voice -> captions -> footage (stock ya tool screenshot) -> assembly -> upload
"""
import os
import yaml
from dotenv import load_dotenv
from mutagen.mp3 import MP3

from src.script_generator import ScriptGenerator
from src.tts_generator import TTSGenerator
from src.caption_generator import CaptionGenerator
from src.stock_footage import StockFootageFetcher
from src.tool_screenshot import ToolScreenshotCapture
from src.video_assembler import VideoAssembler


def load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class SkillorPipeline:
    def __init__(self, settings_path: str = "config/settings.yaml", env_path: str = "config/.env"):
        load_dotenv(env_path)
        self.settings = load_settings(settings_path)

        self.script_gen = ScriptGenerator()
        self.tts_gen = TTSGenerator(
            voice=os.getenv("TTS_VOICE", self.settings["tts"]["voice"]),
            rate=self.settings["tts"].get("rate", "+0%"),
            pitch=self.settings["tts"].get("pitch", "+0Hz"),
        )
        self.caption_gen = CaptionGenerator(words_per_caption=3)
        self.footage_fetcher = StockFootageFetcher()
        self.tool_capture = ToolScreenshotCapture(tuple(self.settings["video"]["resolution"]))
        self.assembler = VideoAssembler(
            resolution=tuple(self.settings["video"]["resolution"]),
            fps=self.settings["video"]["fps"],
        )

    def run(self, topic: str, output_dir: str = "output") -> dict:
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n🧠 [1/5] Groq se script likha ja raha hai: '{topic}'")
        script = self.script_gen.generate(topic)
        print(f"   Title: {script['title']}")

        print("🎙️  [2/5] Edge TTS se Urdu voice generate ho rahi hai...")
        audio_path = os.path.join(output_dir, "voice.mp3")
        word_boundaries = self.tts_gen.generate(script["full_text"], audio_path)
        audio_duration = MP3(audio_path).info.length

        print("📝 [3/5] Captions sync ho rahe hain...")
        srt_path = self.caption_gen.build_srt(word_boundaries, os.path.join(output_dir, "captions.srt"))

        print("🎬 [4/5] Visuals collect ho rahe hain (stock + tool clips)...")
        clip_paths = []
        if script.get("tool_names") and self.settings["tool_screenshot"]["enabled"]:
            for tool_name in script["tool_names"]:
                url = tool_name if tool_name.startswith("http") else f"https://{tool_name}"
                clip = self.tool_capture.capture_scroll_video(
                    url,
                    os.path.join(output_dir, "clips", f"tool_{tool_name.replace('.', '_')}.mp4"),
                    duration_sec=self.settings["tool_screenshot"]["capture_duration_sec"],
                )
                if clip:
                    clip_paths.append(clip)

        remaining_needed = self.settings["stock_footage"]["clips_per_video"] - len(clip_paths)
        if remaining_needed > 0:
            stock_clips = self.footage_fetcher.fetch(
                query=topic, count=remaining_needed, save_dir=os.path.join(output_dir, "clips")
            )
            clip_paths.extend(stock_clips)

        if not clip_paths:
            raise RuntimeError("Koi bhi clip nahi mil saka — Pexels/Pixabay keys check karein.")

        print("🎞️  [5/5] FFmpeg se final video assemble ho raha hai...")
        final_video_path = os.path.join(output_dir, "final_video.mp4")
        self.assembler.assemble(
            clip_paths=clip_paths,
            audio_path=audio_path,
            srt_path=srt_path,
            audio_duration=audio_duration,
            output_path=final_video_path,
        )

        print(f"\n✅ Video ready: {final_video_path}")
        return {
            "video_path": final_video_path,
            "title": script["title"],
            "description": script["full_text"],
        }
