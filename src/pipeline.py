"""
pipeline.py
SKILLOR Automation Pipeline - Complete video generation workflow
"""
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.script_generator import ScriptGenerator
from src.tts_generator import TTSGenerator
from src.caption_generator import CaptionGenerator
from src.stock_footage import StockFootageFetcher
from src.tool_screenshot import ToolScreenshotCapture
from src.video_assembler import VideoAssembler

# Setup logging
logger = logging.getLogger(__name__)


def load_settings(path: str = "config/settings.yaml") -> dict:
    """Load settings from YAML file"""
    config_path = Path(__file__).parent.parent / path
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class SkillorPipeline:
    def __init__(self, settings_path: str = "config/settings.yaml"):
        """Initialize pipeline with all components"""
        self.settings = load_settings(settings_path)
        
        # Get API keys from environment
        import os
        from dotenv import load_dotenv
        load_dotenv("config/.env")
        
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
    
    def run(self, topic: str, output_dir: str = "output") -> dict:
        """Run the complete pipeline for a single topic"""
        os.makedirs(output_dir, exist_ok=True)
        clips_dir = os.path.join(output_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)
        
        logger.info(f"🎬 Starting pipeline for: {topic}")
        
        try:
            # Step 1: Generate script
            print(f"\n🧠 [1/5] Generating script for: '{topic}'")
            script = self.script_gen.generate(topic)
            print(f"   Title: {script['title']}")
            logger.info(f"Script generated: {script['title']}")
            
            # Step 2: Generate TTS
            print("🎙️  [2/5] Generating Urdu voice...")
            audio_path = os.path.join(output_dir, "voice.mp3")
            word_boundaries = self.tts_gen.generate(script["full_text"], audio_path)
            
            if not word_boundaries or len(word_boundaries) == 0:
                logger.warning("No word boundaries generated, creating fallback")
                word_boundaries = self._create_fallback_boundaries(script["full_text"])
            
            # Get audio duration
            try:
                from mutagen.mp3 import MP3
                audio_duration = MP3(audio_path).info.length
            except:
                audio_duration = 30  # Fallback duration
                logger.warning(f"Could not read audio duration, using {audio_duration}s")
            
            # Step 3: Generate captions
            print("📝 [3/5] Generating captions...")
            srt_path = self.caption_gen.build_srt(
                word_boundaries, 
                os.path.join(output_dir, "captions.srt")
            )
            
            # Step 4: Collect visuals
            print("🎬 [4/5] Collecting visuals...")
            clip_paths = []
            
            # Tool screenshots
            if script.get("tool_names") and self.settings["tool_screenshot"]["enabled"]:
                max_tools = self.settings["tool_screenshot"].get("max_tools_per_video", 2)
                for tool_name in script["tool_names"][:max_tools]:
                    url = tool_name if tool_name.startswith("http") else f"https://{tool_name}"
                    clip_path = os.path.join(clips_dir, f"tool_{tool_name.replace('.', '_')}.mp4")
                    
                    logger.info(f"Capturing tool: {tool_name}")
                    clip = self.tool_capture.capture_scroll_video(
                        url,
                        clip_path,
                        duration_sec=self.settings["tool_screenshot"]["capture_duration_sec"],
                    )
                    if clip and os.path.exists(clip):
                        clip_paths.append(clip)
                        logger.info(f"✅ Tool clip captured: {clip}")
            
            # Stock footage
            remaining = self.settings["stock_footage"]["clips_per_video"] - len(clip_paths)
            if remaining > 0:
                logger.info(f"Fetching {remaining} stock clips...")
                stock_clips = self.footage_fetcher.fetch(
                    query=topic, 
                    count=remaining, 
                    save_dir=clips_dir
                )
                clip_paths.extend(stock_clips)
                logger.info(f"✅ {len(stock_clips)} stock clips fetched")
            
            if not clip_paths:
                raise RuntimeError("❌ No clips found! Check API keys and internet connection.")
            
            # Step 5: Assemble video
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
            logger.info(f"✅ Video assembled: {final_video_path}")
            
            return {
                "video_path": final_video_path,
                "title": script["title"],
                "script": script,
                "audio_duration": audio_duration,
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise
    
    def _create_fallback_boundaries(self, text: str) -> list:
        """Create fallback word boundaries if TTS fails"""
        words = text.split()
        duration_per_word = 0.3
        boundaries = []
        
        for i, word in enumerate(words):
            boundaries.append({
                "text": word,
                "start": i * duration_per_word,
                "duration": duration_per_word
            })
        
        return boundaries


if __name__ == "__main__":
    # Test pipeline
    pipeline = SkillorPipeline()
    result = pipeline.run("ChatGPT ka naya feature")
    print(f"\n✅ Result: {result['title']}")
