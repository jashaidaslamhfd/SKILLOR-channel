"""
pipeline.py - UPDATED with better tool name handling
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
        
        # Initialize components
        self.script_gen = ScriptGenerator(
            api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv("GROQ_MODEL", self.settings["script"].get("model", "llama-3.3-70b-versatile"))
        )
        
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
    
    def _clean_tool_name(self, tool_name: str) -> str:
        """Clean and validate tool name"""
        # Remove spaces
        tool_name = tool_name.strip().replace(" ", "")
        
        # Remove "AI" suffix if present
        tool_name = tool_name.replace("AI", "")
        
        # Add .com if no extension
        if "." not in tool_name:
            tool_name = f"{tool_name}.com"
        
        return tool_name.lower()
    
    def run(self, topic: str, output_dir: str = "output") -> dict:
        """Run the complete pipeline for a single topic"""
        os.makedirs(output_dir, exist_ok=True)
        clips_dir = os.path.join(output_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)
        
        print(f"\n🧠 [1/5] Generating script for: '{topic}'")
        script = self.script_gen.generate(topic)
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
        
        # Tool screenshots
        if script.get("tool_names") and self.settings["tool_screenshot"]["enabled"]:
            max_tools = self.settings["tool_screenshot"].get("max_tools_per_video", 2)
            for tool_name in script["tool_names"][:max_tools]:
                # Clean the tool name
                clean_tool = self._clean_tool_name(tool_name)
                url = clean_tool if clean_tool.startswith("http") else f"https://{clean_tool}"
                
                clip_path = os.path.join(clips_dir, f"tool_{clean_tool.replace('.', '_')}.mp4")
                
                print(f"   📸 Capturing tool: {clean_tool}")
                clip = self.tool_capture.capture_scroll_video(
                    url,
                    clip_path,
                    duration_sec=self.settings["tool_screenshot"]["capture_duration_sec"],
                )
                if clip and os.path.exists(clip):
                    clip_paths.append(clip)
                    print(f"   ✅ Tool clip captured")
        
        # Stock footage
        remaining = self.settings["stock_footage"]["clips_per_video"] - len(clip_paths)
        if remaining > 0:
            print(f"   🎬 Fetching {remaining} stock clips...")
            stock_clips = self.footage_fetcher.fetch(
                query=topic, 
                count=remaining, 
                save_dir=clips_dir
            )
            clip_paths.extend(stock_clips)
            print(f"   ✅ {len(stock_clips)} stock clips fetched")
        
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


if __name__ == "__main__":
    pipeline = SkillorPipeline()
    result = pipeline.run("Notion AI kya hai aur kaise use karein")
    print(f"\n✅ Result: {result['title']}")
