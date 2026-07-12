import os
import logging
import time
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from niche_strategy import _make_seo_title
from seo_generator import generate_description

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5

# ---------------------------------------------------------------------------
# IMPORTANT: YouTube video uploads require OAuth 2.0 USER credentials, not a
# service-account key. Credentials are read from THREE separate secrets/env
# vars: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REFRESH_TOKEN.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# YOUTUBE "MADE FOR KIDS" (COPPA)
# This channel's content is dark/mystery body-science facts aimed at adults
# (18+), so MADE_FOR_KIDS defaults to False. If your niche or audience
# changes again, re-verify this setting - COPPA fines are no joke.
# ---------------------------------------------------------------------------
MADE_FOR_KIDS = os.environ.get("YT_MADE_FOR_KIDS", "false").lower() == "true"


def _build_youtube_description(script_data: dict, tags: list) -> str:
    """CTR-optimized YouTube description. Delegates to
    seo_generator.generate_description() so upload and the SEO-package
    preview (script_data['description'] set in main.py) can never drift
    out of sync - this used to be a separate copy of the same logic."""
    return generate_description(script_data, tags)


def _upload_youtube(video_path, thumb_path, script_data, tags):
    """Returns (success: bool, video_id: str|None)."""
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    missing = [
        name for name, val in {
            "GOOGLE_CLIENT_ID": google_client_id,
            "GOOGLE_CLIENT_SECRET": google_client_secret,
            "REFRESH_TOKEN": refresh_token,
        }.items() if not val
    ]
    if missing:
        logger.error(f"YouTube upload skipped - missing secrets: {missing}")
        return False, None

    title = script_data.get('title', 'Untitled')
    enhanced_title = _make_seo_title(title, script_data.get('topic', title))
    desc = _build_youtube_description(script_data, tags)

    # NOTE: captions.insert (SRT upload) and commentThreads.insert (posting
    # the pinned_comment from seo_generator) both need the broader
    # youtube.force-ssl scope, not just youtube.upload. Listing it here
    # doesn't grant it by itself - your REFRESH_TOKEN has to have actually
    # been issued with consent for this scope, or those two calls below
    # will fail with a 403 and get skipped (logged as a warning, not fatal -
    # the video upload itself only needs youtube.upload and is unaffected).
    creds = google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=google_client_id,
        client_secret=google_client_secret,
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
        ],
    )
    yt = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title': enhanced_title[:100],
            'description': desc[:5000],
            'categoryId': '28',
            # FIX: was a fixed hardcoded list on every single video - now
            # topic/category-aware tags from niche_strategy.generate_seo_tags,
            # which also helps SEO reach and avoids duplicate-metadata spam risk.
            'tags': tags,
            'defaultLanguage': 'fr',
            'defaultAudioLanguage': 'fr',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': MADE_FOR_KIDS,
        }
    }

    logger.info("Uploading to YouTube...")
    yt_video_id = None
    youtube_success = False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = yt.videos().insert(
                part="snippet,status",
                body=body,
                media_body=MediaFileUpload(video_path, chunksize=1024 * 1024, resumable=True)
            )
            res = req.execute()
            yt_video_id = res.get('id')
            logger.info(f"YouTube upload successful: https://youtu.be/{yt_video_id}")
            youtube_success = True

            if thumb_path and os.path.exists(thumb_path):
                try:
                    yt.thumbnails().set(
                        videoId=yt_video_id,
                        media_body=MediaFileUpload(thumb_path)
                    ).execute()
                    logger.info("Thumbnail uploaded successfully")
                except Exception as thumb_error:
                    logger.warning(f"Thumbnail upload failed: {thumb_error}")

            # Optional: real closed-caption track from seo/shorts modules'
            # SRT export (main.py sets script_data['srt_path']). Best-effort
            # only - see scope note above.
            srt_path = script_data.get('srt_path')
            if srt_path and os.path.exists(srt_path):
                try:
                    yt.captions().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "videoId": yt_video_id,
                                "language": "fr",
                                "name": "Français",
                                "isDraft": False,
                            }
                        },
                        media_body=MediaFileUpload(srt_path, mimetype="application/octet-stream"),
                    ).execute()
                    logger.info("Captions uploaded successfully")
                except Exception as captions_error:
                    logger.warning(
                        f"Captions upload failed (needs youtube.force-ssl scope on REFRESH_TOKEN): {captions_error}"
                    )

            # Optional: post the pinned_comment from seo_generator as the
            # first top-level comment. NOTE: this only posts the comment -
            # the YouTube Data API has no public endpoint to actually pin a
            # comment, so pinning it still needs one manual click in Studio.
            pinned_comment = script_data.get('pinned_comment')
            if pinned_comment:
                try:
                    yt.commentThreads().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "videoId": yt_video_id,
                                "topLevelComment": {
                                    "snippet": {"textOriginal": pinned_comment}
                                },
                            }
                        },
                    ).execute()
                    logger.info("Seed comment posted (pin it manually in YouTube Studio for best effect)")
                except Exception as comment_error:
                    logger.warning(
                        f"Seed comment post failed (needs youtube.force-ssl scope on REFRESH_TOKEN): {comment_error}"
                    )
            break

        except HttpError as e:
            if e.resp.status in [429, 500, 502, 503]:
                logger.warning(f"YouTube API error {e.resp.status} (attempt {attempt}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))
                continue
            else:
                logger.error(f"YouTube upload failed: {e}")
                break
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            break

    return youtube_success, yt_video_id


def upload_all(video_path, thumb_path, script_data):
    """Upload video to YouTube only (Facebook/Reels upload removed - YouTube-only pipeline)."""

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not script_data or 'title' not in script_data:
        raise ValueError("Invalid script data - missing title")

    title = script_data.get('title', 'Sans titre')
    # Tags come from script_data (set by main.py via niche_strategy.generate_seo_tags).
    # Fallback below only fires if that ever comes back empty - matches the
    # current dark-facts niche, not the old parenting-channel tags.
    tags = script_data.get('tags') or ['faits', 'shorts', 'science', 'faitssombres', 'faitscorps']

    logger.info(f"Starting upload process for: {title}")
    logger.info(f"selfDeclaredMadeForKids = {MADE_FOR_KIDS} (verify this is correct for your content!)")
    logger.info(f"SEO tags for this video: {tags}")

    youtube_success, yt_video_id = _upload_youtube(video_path, thumb_path, script_data, tags)

    logger.info(f"YouTube Upload: {'SUCCESS' if youtube_success else 'FAILED/SKIPPED'}")
    if yt_video_id:
        logger.info(f"  URL: https://youtu.be/{yt_video_id}")

    if not youtube_success:
        raise RuntimeError("YouTube upload failed")

    return {
        "youtube_success": youtube_success,
        "youtube_video_id": yt_video_id,
    }
