"""
main.py
SKILLOR Automation - Main Entry Point

Usage:
    python main.py --topic "ChatGPT ka naya feature" --upload yes
    python main.py --mode scheduler
    python main.py --mode manual --count 3
"""
import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline import SkillorPipeline
from src.seo_optimizer import SEOOptimizer
from src.thumbnail_generator import ThumbnailGenerator
from src.config_loader import load_settings


def single_video_mode(topic: str, upload: bool = False):
    """Single video generation mode"""
    print(f"\n🎬 Generating video for: {topic}")
    
    pipeline = SkillorPipeline()
    result = pipeline.run(topic)
    
    # Get script
    script = result.get("script", {})
    tool_names = script.get("tool_names", [])
    
    # SEO Optimization
    seo = SEOOptimizer()
    optimized_title = seo.optimize_title(result["title"])
    description = seo.generate_description(script, tool_names)
    tags = seo.generate_hashtags("Tech", tool_names)
    
    print(f"\n📌 Optimized Title: {optimized_title}")
    print(f"📝 Description length: {len(description)} chars")
    
    # Generate thumbnail
    thumb_gen = ThumbnailGenerator()
    thumbnail_path = thumb_gen.generate(
        title=optimized_title,
        tool_screenshot_path=None,
        output_path="output/thumbnail.jpg"
    )
    print(f"🖼️ Thumbnail generated: {thumbnail_path}")
    
    # Upload if requested
    if upload:
        settings = load_settings()
        
        if settings.get("upload", {}).get("youtube", {}).get("enabled", False):
            from src.youtube_uploader import YouTubeUploader
            print("\n📤 YouTube par upload ho raha hai...")
            yt = YouTubeUploader()
            video_id = yt.upload(
                video_path=result["video_path"],
                title=optimized_title,
                description=description,
                tags=tags,
                privacy=settings["upload"]["youtube"].get("privacy", "public"),
                category_id=settings["upload"]["youtube"].get("category_id", "28"),
                thumbnail_path=thumbnail_path
            )
            print(f"✅ Video uploaded! ID: {video_id}")
        else:
            print("\nℹ️  YouTube upload disabled in settings")
    else:
        print("\nℹ️  Upload skip kar diya gaya. Video output/ folder mein maujood hai.")
    
    return result


def scheduler_mode():
    """Run the automated scheduler"""
    from scheduler import SKILLORAutomation
    automator = SKILLORAutomation()
    automator.run_daily_schedule()


def manual_mode(count: int = 1):
    """Manual batch mode"""
    from scheduler import SKILLORAutomation
    automator = SKILLORAutomation()
    automator.manual_run(count)


def main():
    parser = argparse.ArgumentParser(
        description="SKILLOR YouTube Automation - Daily 3 Videos"
    )
    
    parser.add_argument("--mode", choices=["single", "scheduler", "manual"], 
                       default="single", help="Run mode")
    parser.add_argument("--topic", help="Video topic (for single mode)")
    parser.add_argument("--upload", choices=["yes", "no"], default="no", 
                       help="Upload karna hai ya nahi")
    parser.add_argument("--count", type=int, default=1, 
                       help="Manual run: number of videos to generate")
    
    args = parser.parse_args()
    
    if args.mode == "scheduler":
        print("🚀 Starting SKILLOR Scheduler - 3 videos per day...")
        scheduler_mode()
        
    elif args.mode == "manual":
        print(f"🎯 Manual mode: Generating {args.count} video(s)...")
        manual_mode(args.count)
        
    else:  # single mode
        if not args.topic:
            print("❌ Please provide --topic for single mode")
            print("Example: python main.py --topic 'ChatGPT ka naya feature'")
            sys.exit(1)
        
        single_video_mode(args.topic, args.upload == "yes")


if __name__ == "__main__":
    main()
