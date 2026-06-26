"""
main.py
SKILLOR automation pipeline ka entry point with scheduler support
"""
import argparse
import sys
from src.pipeline import SkillorPipeline, load_settings
from src.seo_optimizer import SEOOptimizer
from src.thumbnail_generator import ThumbnailGenerator
import os

def single_video_mode(topic: str, upload: bool = False):
    """Single video generation mode"""
    print(f"\n🎬 Generating video for: {topic}")
    
    pipeline = SkillorPipeline()
    result = pipeline.run(topic)
    
    # Get script for SEO
    script = result.get("script", {})
    tool_names = script.get("tool_names", [])
    
    # Optimize SEO
    seo = SEOOptimizer()
    optimized_title = seo.optimize_title(result["title"])
    description = seo.generate_description(script, tool_names)
    
    print(f"\n📌 Optimized Title: {optimized_title}")
    print(f"📝 Description length: {len(description)} chars")
    
    # Generate thumbnail
    thumb_gen = ThumbnailGenerator()
    thumbnail_path = thumb_gen.generate(
        title=optimized_title,
        output_path="output/thumbnail.jpg"
    )
    print(f"🖼️ Thumbnail generated: {thumbnail_path}")
    
    # Upload if requested
    if upload:
        settings = load_settings()
        
        if settings["upload"]["youtube"]["enabled"]:
            from src.youtube_uploader import YouTubeUploader
            print("\n📤 YouTube par upload ho raha hai...")
            yt = YouTubeUploader()
            video_id = yt.upload(
                video_path=result["video_path"],
                title=optimized_title,
                description=description,
                tags=seo.generate_hashtags("Tech", tool_names),
                privacy=settings["upload"]["youtube"]["privacy"],
                category_id=settings["upload"]["youtube"]["category_id"],
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

def main():
    parser = argparse.ArgumentParser(
        description="SKILLOR YouTube Automation - Daily 3 Videos"
    )
    
    # Mode selection
    parser.add_argument("--mode", choices=["single", "scheduler", "manual"], 
                       default="single", help="Run mode")
    
    # Single video mode
    parser.add_argument("--topic", help="Video topic (for single mode)")
    parser.add_argument("--upload", choices=["yes", "no"], default="no", 
                       help="Upload karna hai ya nahi")
    
    # Manual mode
    parser.add_argument("--count", type=int, default=1, 
                       help="Manual run: number of videos to generate")
    
    args = parser.parse_args()
    
    if args.mode == "scheduler":
        print("🚀 Starting SKILLOR Scheduler - 3 videos per day...")
        scheduler_mode()
        
    elif args.mode == "manual":
        from scheduler import SKILLORAutomation
        automator = SKILLORAutomation()
        automator.manual_run(args.count)
        
    else:  # single mode
        if not args.topic:
            print("❌ Please provide --topic for single mode")
            sys.exit(1)
        
        single_video_mode(args.topic, args.upload == "yes")

if __name__ == "__main__":
    main()
