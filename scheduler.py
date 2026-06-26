"""
scheduler.py
SKILLOR Automation Scheduler - Daily 3 videos auto-upload

Usage:
    python scheduler.py                    # Auto-schedule
    python scheduler.py --manual --count 3 # Manual batch
"""
import schedule
import time
import os
import sys
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.topic_finder import TopicFinder
from src.pipeline import SkillorPipeline
from src.seo_optimizer import SEOOptimizer
from src.thumbnail_generator import ThumbnailGenerator
from src.youtube_uploader import YouTubeUploader
from src.config_loader import load_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('skillor_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SKILLORAutomation:
    def __init__(self):
        self.settings = load_settings()
        self.topic_finder = TopicFinder()
        self.pipeline = SkillorPipeline()
        self.seo_optimizer = SEOOptimizer()
        self.thumbnail_gen = ThumbnailGenerator()
        
        # Upload times from settings
        self.upload_times = self.settings.get("scheduler", {}).get(
            "upload_times", ["10:00", "14:00", "18:00"]
        )
        self.videos_per_day = len(self.upload_times)
        
        logger.info(f"📅 Configured upload times: {', '.join(self.upload_times)}")
        logger.info(f"📹 Videos per day: {self.videos_per_day}")
    
    def generate_and_upload(self):
        """Generate one video and upload"""
        try:
            logger.info("🎬 Starting new video generation...")
            
            # Step 1: Get trending topic
            topics = self.topic_finder.get_trending_topics(count=1)
            if not topics:
                logger.error("❌ No topics found!")
                return None
            
            topic_data = topics[0]
            topic = topic_data["title"]
            logger.info(f"📌 Selected topic: {topic}")
            
            # Step 2: Run pipeline
            result = self.pipeline.run(topic)
            
            # Step 3: Get script data
            script = result.get("script", {})
            tool_names = script.get("tool_names", [])
            
            # Step 4: SEO Optimization
            optimized_title = self.seo_optimizer.optimize_title(result["title"])
            description = self.seo_optimizer.generate_description(script, tool_names)
            tags = self.seo_optimizer.generate_hashtags("Tech", tool_names)
            
            logger.info(f"📌 Optimized Title: {optimized_title}")
            
            # Step 5: Generate thumbnail
            thumbnail_path = self._generate_thumbnail(optimized_title, tool_names)
            
            # Step 6: Upload to YouTube
            if self.settings.get("upload", {}).get("youtube", {}).get("enabled", True):
                uploader = YouTubeUploader()
                video_id = uploader.upload(
                    video_path=result["video_path"],
                    title=optimized_title,
                    description=description,
                    tags=tags,
                    privacy="public",
                    thumbnail_path=thumbnail_path
                )
                
                logger.info(f"✅ Video uploaded! ID: {video_id}")
                self._log_upload(video_id, optimized_title, topic)
                return video_id
            else:
                logger.warning("⚠️ YouTube upload is disabled in settings")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to generate video: {e}")
            return None
    
    def _generate_thumbnail(self, title: str, tool_names: list):
        """Generate thumbnail"""
        try:
            # Try to use tool screenshot if available
            tool_screenshot = None
            if tool_names:
                tool_path = os.path.join("output", "clips", 
                           f"tool_{tool_names[0].replace('.', '_')}.png")
                if os.path.exists(tool_path):
                    tool_screenshot = tool_path
            
            return self.thumbnail_gen.generate(
                title=title,
                tool_screenshot_path=tool_screenshot,
                output_path="output/thumbnail.jpg"
            )
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None
    
    def _log_upload(self, video_id: str, title: str, topic: str):
        """Log uploaded videos for tracking"""
        log_file = "upload_log.txt"
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} | {video_id} | {title} | {topic}\n")
    
    def run_daily_schedule(self):
        """Run the daily upload schedule"""
        logger.info("🚀 Starting SKILLOR Automation Scheduler...")
        logger.info(f"📅 Daily upload times: {', '.join(self.upload_times)}")
        logger.info(f"📹 Videos per day: {self.videos_per_day}")
        logger.info("✅ Scheduler is running. Press Ctrl+C to stop.")
        
        # Schedule uploads
        for time_str in self.upload_times:
            schedule.every().day.at(time_str).do(self.generate_and_upload)
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            logger.info("👋 Scheduler stopped by user")
    
    def manual_run(self, count: int = 1):
        """Manual run for testing"""
        logger.info(f"🎯 Manual run: Generating {count} video(s)...")
        
        for i in range(count):
            logger.info(f"\n📹 Video {i+1}/{count}")
            self.generate_and_upload()
            if i < count - 1:
                time.sleep(10)  # Delay between videos


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SKILLOR Automation Scheduler")
    parser.add_argument("--manual", action="store_true", help="Run manually")
    parser.add_argument("--count", type=int, default=1, help="Number of videos")
    args = parser.parse_args()
    
    automator = SKILLORAutomation()
    
    if args.manual:
        automator.manual_run(args.count)
    else:
        automator.run_daily_schedule()
