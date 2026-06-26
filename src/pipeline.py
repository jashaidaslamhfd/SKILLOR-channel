"""
pipeline.py - FIXED
"""
import os
import sys
import yaml
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.script_generator import ScriptGenerator
from src.tts_generator import TTSGenerator
from src.caption_generator import CaptionGenerator
from src.stock_footage import StockFootageFetcher
from src.tool_screenshot import ToolScreenshotCapture
from src.video_assembler import VideoAssembler
from src.config_loader import load_settings, load_env

logger = logging.getLogger(__name__)

# Load environment
load_env()


class SkillorPipeline:
    def __init__(self, settings_path: str = "config/settings.yaml"):
        """Initialize pipeline with all components"""
        self.settings = load_settings(settings_path)
        
        # Get API keys
        import os
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            print("⚠️ GROQ_API_KEY not found, using fallback script generator")
        
        # Initialize components with error handling
        try:
            self.script_gen = ScriptGenerator(
                api_key=groq_key,
                model=os.getenv("GROQ_MODEL", self.settings["script"].get("model", "llama-3.3-70b-versatile"))
            )
        except Exception as e:
            print(f"⚠️ ScriptGenerator initialization failed: {e}")
            # Create a dummy script generator
            self.script_gen = None
        
        self.tts_gen = TTSGenerator(
            voice=os.getenv("TTS_VOICE", self.settings["tts"]["voice"]),
            rate=self.settings["tts"].get("rate", "+0%"),
            pitch=self.settings["tts"].get("pitch", "+0Hz"),
        )
        
        self.caption_gen = CaptionGenerator(words_per_caption=3)
        
        self.footage_fetcher = StockFootageFetcher(
            pexels_key=os.getenv("PEXELS_API_KEY"),
            pixabay_key=os.getenv("PIXABAY_API_KEY")
        )
        
        self.tool_capture = ToolScreenshotCapture(
            viewport=tuple(self.settings["video"]["resolution"])
        )
        
        self.assembler = VideoAssembler(
            resolution=tuple(self.settings["video"]["resolution"]),
            fps=self.settings["video"]["fps"],
        )
        
        logger.info("✅ Pipeline initialized successfully")
    
    def run(self, topic: str, output_dir: str = "output") -> dict:
        """Run the complete pipeline for a single topic"""
        os.makedirs(output_dir, exist_ok=True)
        clips_dir = os.path.join(output_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)
        
        print(f"\n🧠 [1/5] Generating script for: '{topic}'")
        
        # Generate script (with fallback)
        if self.script_gen:
            try:
                script = self.script_gen.generate(topic)
            except Exception as e:
                print(f"⚠️ Script generation failed: {e}")
                script = self._create_fallback_script(topic)
        else:
            script = self._create_fallback_script(topic)
        
        print(f"   Title: {script['title']}")
        
        print("🎙️  [2/5] Generating Urdu voice...")
        audio_path = os.path.join(output_dir, "voice.mp3")
        word_boundaries = self.tts_gen.generate(script["full_text"], audio_path)
        
        print("📝 [3/5] Generating captions...")
        srt_path = self.caption_gen.build_srt(
            word_boundaries, 
            os.path.join(output_dir, "captions.srt")
        )
        
        print("🎬 [4/5] Collecting visuals...")
        clip_paths = []
        
        if script.get("tool_names") and self.settings["tool_screenshot"]["enabled"]:
            max_tools = self.settings["tool_screenshot"].get("max_tools_per_video", 2)
            for tool_name in script["tool_names"][:max_tools]:
                url = tool_name if tool_name.startswith("http") else f"https://{tool_name}"
                clip_path = os.path.join(clips_dir, f"tool_{tool_name.replace('.', '_')}.mp4")
                clip = self.tool_capture.capture_scroll_video(
                    url,
                    clip_path,
                    duration_sec=self.settings["tool_screenshot"]["capture_duration_sec"],
                )
                if clip:
                    clip_paths.append(clip)
        
        remaining = self.settings["stock_footage"]["clips_per_video"] - len(clip_paths)
        if remaining > 0:
            stock_clips = self.footage_fetcher.fetch(
                query=topic, 
                count=remaining, 
                save_dir=clips_dir
            )
            clip_paths.extend(stock_clips)
        
        if not clip_paths:
            raise RuntimeError("❌ No clips found! Check API keys.")
        
        # Get audio duration
        try:
            from mutagen.mp3 import MP3
            audio_duration = MP3(audio_path).info.length
        except:
            audio_duration = 30
        
        print("🎞️  [5/5] Assembling final video...")
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
            "script": script,
        }
    
    def _create_fallback_script(self, topic: str) -> dict:
        """Create fallback script"""
        tool_names = []
        tools = ["chatgpt", "midjourney", "canva", "deepseek", "perplexity"]
        for tool in tools:
            if tool in topic.lower():
                tool_names.append(f"{tool}.com")
                break
        
        return {
            "title": topic[:60],
            "hook": f"Assalam-o-Alaikum! Aaj ki baat hai {topic}",
            "body": f"Ya video {topic} ke baare mein hai. SKILLOR par AI tools seekhein!",
            "cta": "SKILLOR ko follow karein!",
            "tool_names": tool_names,
            "full_text": f"Assalam-o-Alaikum! Aaj ki baat hai {topic}. Ya video {topic} ke baare mein hai. SKILLOR par AI tools seekhein! SKILLOR ko follow karein!"
        }


if __name__ == "__main__":
    pipeline = SkillorPipeline()
    result = pipeline.run("Midjourney se professional images kaise banayein")
    print(f"\n✅ Result: {result['title']}")
