"""
main.py
SKILLOR automation pipeline ka entry point.

Usage:
    python main.py --topic "ChatGPT ka naya feature" --upload yes
    python main.py --topic "5 AI tools jo aapka kaam asaan kar dein" --upload no
"""
import argparse
from src.pipeline import SkillorPipeline, load_settings


def main():
    parser = argparse.ArgumentParser(description="SKILLOR YouTube Automation")
    parser.add_argument("--topic", required=True, help="Video ka topic (Urdu/English mix mein likhein)")
    parser.add_argument("--upload", choices=["yes", "no"], default="no", help="Upload karna hai ya sirf video banani hai")
    args = parser.parse_args()

    pipeline = SkillorPipeline()
    result = pipeline.run(args.topic)

    if args.upload == "yes":
        settings = load_settings()

        if settings["upload"]["youtube"]["enabled"]:
            from src.youtube_uploader import YouTubeUploader
            print("\n📤 YouTube par upload ho raha hai...")
            yt = YouTubeUploader()
            yt.upload(
                video_path=result["video_path"],
                title=result["title"],
                description=result["description"],
                privacy=settings["upload"]["youtube"]["privacy"],
                category_id=settings["upload"]["youtube"]["category_id"],
            )

        if settings["upload"]["tiktok"]["enabled"]:
            from src.tiktok_uploader import TikTokUploader
            print("\n📤 TikTok par upload ho raha hai...")
            tk = TikTokUploader()
            tk.upload(video_path=result["video_path"], caption=result["title"])
    else:
        print("\nℹ️  Upload skip kar diya gaya. Video output/ folder mein maujood hai.")


if __name__ == "__main__":
    main()
