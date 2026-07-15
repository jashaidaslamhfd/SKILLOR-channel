import os
import sys
import json
import logging
from collections import Counter
from datetime import datetime, timezone
import time
import traceback

# Add current directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import modules with error handling
try:
    from script_generator import generate_script
    from image_generator import _generate_one as generate_images
    from voice_generator import generate_voice_segments
    from video_editor import build_video, generate_thumbnail
    from uploader import upload_all
    from niche_strategy import (
        get_script_prompt_for_niche, get_random_topic, get_topic_category,
        generate_seo_tags, validate_script_for_medical_accuracy, auto_add_disclaimer,
    )
    from quality_checker import QualityChecker
    from scheduler import USAPeakTimeScheduler
    from anti_spam import AntiSpamSystem
    from seo_generator import generate_seo_package
    from shorts_enhancer import build_shorts_report, generate_srt
    from seo_analytics import predict_ctr, score_thumbnail, rank_hashtags, generate_ab_variants, get_historical_insights
    from french_quality_gate import validate_publication_quality
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error("Make sure all required modules are in the same directory")
    sys.exit(1)

# Constants
MAX_SCRIPT_ATTEMPTS = 3
MAX_IMAGE_RETRIES = 3
FALLBACK_ABORT_RATIO = float(os.environ.get("FALLBACK_ABORT_RATIO", "0.5"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
ALLOW_QUALITY_OVERRIDE = os.environ.get("ALLOW_QUALITY_OVERRIDE", "false").lower() == "true"


class SKILLORPipeline:
    def __init__(self):
        """Initialize pipeline with all components"""
        logger.info("Initializing SKILLOR Pipeline...")

        try:
            self.quality_checker = QualityChecker()
            self.scheduler = USAPeakTimeScheduler()
            self.anti_spam = AntiSpamSystem()
            self.video_history = self._load_video_history()
            logger.info(f"Loaded {len(self.video_history)} videos from history")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise

    def _load_video_history(self) -> list:
        """Load video history from file"""
        history_file = "output/video_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("History file corrupted, creating new one")
                return []
            except Exception as e:
                logger.warning(f"Could not load history: {e}")
                return []
        return []

    def _save_video_history(self, video_data: dict):
        """Save video history to file"""
        try:
            os.makedirs("output", exist_ok=True)
            self.video_history.append(video_data)

            # Keep only last 50 videos
            if len(self.video_history) > 50:
                self.video_history = self.video_history[-50:]

            with open("output/video_history.json", 'w') as f:
                json.dump(self.video_history, f, indent=2)

            logger.info(f"Saved video to history: {video_data.get('title', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to save video history: {e}")

    def _get_recent_topics(self, n: int = 20) -> list:
        """Get recent topics to avoid repetition"""
        return [v.get('topic') for v in self.video_history[-n:] if v.get('topic')]

    def _generate_and_check_once(self, topic: str) -> dict:
        """Generate script once and check quality"""
        try:
            # Get category and prompt
            category = get_topic_category(topic)
            specialized_prompt = get_script_prompt_for_niche(topic)

            # Generate script
            logger.info(f"Generating script for topic: {topic}")
            script_data = generate_script(topic, custom_prompt=specialized_prompt)

            if not script_data:
                raise ValueError("Script generation returned empty data")

            # Medical accuracy check
            med_check = validate_script_for_medical_accuracy(script_data)
            if not med_check.get('valid', False):
                logger.warning("Medical accuracy check failed, adding disclaimer")
                script_data = auto_add_disclaimer(script_data)

            # Quality check
            quality_result = self.quality_checker.check_script_quality(script_data)
            if not quality_result:
                quality_result = {'approved': False, 'scores': {'overall_quality': 0}}

            # Spam check
            spam_result = self.anti_spam.check_for_spam_risks(script_data, self.video_history)

            # Generate SEO tags
            tags = generate_seo_tags(topic, category, script_data.get('title', ''))

            # Add metadata
            script_data['topic'] = topic
            script_data['category'] = category
            script_data['quality_scores'] = quality_result.get('scores', {})
            script_data['spam_risk'] = spam_result.get('spam_risk_level', 'UNKNOWN')
            script_data['tags'] = tags

            # Check if script has scenes
            if not script_data.get('scenes') or len(script_data['scenes']) < 3:
                raise ValueError("Script has insufficient scenes")

            return {
                "script_data": script_data,
                "quality_approved": quality_result.get('approved', False),
                "quality_score": quality_result.get('scores', {}).get('overall_quality', 0),
                "spam_ok": spam_result.get('spam_risk_level', 'UNKNOWN') not in ['CRITICAL', 'HIGH'],
                "spam_level": spam_result.get('spam_risk_level', 'UNKNOWN'),
            }

        except Exception as e:
            logger.error(f"Error in _generate_and_check_once: {e}")
            raise

    def generate_with_niche_strategy(self, topic: str = None) -> dict:
        """Generate script with retry logic"""
        fixed_topic = topic
        recent_topics = self._get_recent_topics()
        best_attempt = None
        last_error = None

        for attempt in range(1, MAX_SCRIPT_ATTEMPTS + 1):
            try:
                current_topic = fixed_topic or get_random_topic(exclude=recent_topics)
                logger.info(f"Attempt {attempt}/{MAX_SCRIPT_ATTEMPTS} for topic: {current_topic}")

                result = self._generate_and_check_once(current_topic)

                # Keep best attempt
                if best_attempt is None or result['quality_score'] > best_attempt['quality_score']:
                    best_attempt = result
                    logger.info(f"New best score: {result['quality_score']}")

                # Return if quality is good
                if result['quality_approved'] and result['spam_ok']:
                    logger.info(f"Quality approved! Score: {result['quality_score']}")
                    return result['script_data']

            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt} failed: {e}")
                continue

        # If all attempts failed but we have a best attempt
        if best_attempt:
            logger.warning(f"Using best attempt with score: {best_attempt['quality_score']}")
            return best_attempt['script_data']

        # Complete failure
        raise RuntimeError(
            f"All {MAX_SCRIPT_ATTEMPTS} script-generation attempts failed. "
            f"Last error: {last_error}"
        )

    def _generate_images_with_retry(self, script_data: dict) -> tuple:
        """Generate images with retry logic"""
        image_paths = []
        image_sources = []
        used_hashes = set()
        used_fallbacks = set()

        total_scenes = len(script_data['scenes'])
        logger.info(f"Generating images for {total_scenes} scenes...")

        for i, scene in enumerate(script_data['scenes']):
            success = False

            for retry in range(MAX_IMAGE_RETRIES):
                try:
                    logger.info(f"Scene {i+1}/{total_scenes} - Attempt {retry+1}")
                    res = generate_images(i, scene, used_hashes, used_fallbacks)

                    if res and res.get('path') and os.path.exists(res['path']):
                        image_paths.append(res['path'])
                        image_sources.append(res.get('source', 'unknown'))
                        success = True
                        break

                except Exception as e:
                    logger.warning(f"Image generation failed (attempt {retry+1}): {e}")
                    time.sleep(2)

            if not success:
                # generate_images() already tries every real fallback layer internally:
                # AI providers, local pool, Pexels, Pixabay, and finally Playwright screenshot.
                logger.error(
                    f"All {MAX_IMAGE_RETRIES} attempts "
                    f"(each trying every fallback layer) failed for scene {i+1}"
                )
                raise RuntimeError(
                    f"Failed to generate image for scene {i+1}: "
                    f"every provider and fallback layer failed"
                )

        if len(image_paths) != total_scenes:
            raise RuntimeError(f"Generated {len(image_paths)} images for {total_scenes} scenes")

        return image_paths, image_sources

    def run_pipeline(self, topic: str = None) -> dict:
        """Main pipeline execution"""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("🚀 STARTING SKILLOR - FRENCH DARK BODY SCIENCE SHORTS PIPELINE")
        logger.info("=" * 60)

        try:
            # Phase 0: Check posting interval
            if self.video_history:
                last_posted_at = self.video_history[-1].get('posted_at')
                if last_posted_at:
                    try:
                        last_dt = datetime.fromisoformat(last_posted_at)
                        if not self.scheduler.validate_posting_interval(last_dt):
                            logger.warning("⚠️ Posting sooner than recommended 2h gap - monitor spam flags")
                    except Exception as e:
                        logger.warning(f"Could not validate posting interval: {e}")

            # Phase 1: Script Generation
            logger.info("\n📝 PHASE 1: SCRIPT GENERATION")
            script_data = self.generate_with_niche_strategy(topic)
            logger.info(f"✅ Script generated: {script_data.get('title', 'Untitled')}")

            # Phase 1b: SEO Generation
            logger.info("\n🔍 PHASE 1b: SEO GENERATION")
            try:
                seo_topic = script_data.get('topic', topic)
                seo_package = generate_seo_package(seo_topic, script_data)

                script_data['title'] = seo_package.get('chosen_title', script_data.get('title', 'Untitled'))
                script_data['title_options'] = seo_package.get('title_options', [])
                script_data['description'] = seo_package.get('description', '')
                script_data['tags'] = seo_package.get('tags', [])
                script_data['hashtags'] = seo_package.get('hashtags', [])
                script_data['pinned_comment'] = seo_package.get('pinned_comment', '')
                script_data['playlist_suggestion'] = seo_package.get('playlist_suggestion', '')
                script_data['seo_score'] = seo_package.get('seo_score', {})

                seo_overall = script_data['seo_score'].get('scores', {}).get('overall_seo_score', 0)
                logger.info(f"✅ SEO score: {seo_overall}/100")

                if seo_overall < 50:
                    logger.warning("⚠️ SEO score low - review before publishing")

            except Exception as e:
                logger.warning(f"SEO generation failed, continuing: {e}")

            # CTR Prediction
            try:
                ctr_result = predict_ctr(script_data)
                script_data['ctr_prediction'] = ctr_result

                ranked_hashtags = rank_hashtags(script_data.get('hashtags', []))
                script_data['hashtags_ranked'] = ranked_hashtags

                title_options = script_data.get('title_options', [])
                if title_options:
                    ab_variants = generate_ab_variants(script_data, title_options)
                    script_data['ab_variants'] = ab_variants
                    logger.info("✅ A/B title/description variants generated")

                insights = get_historical_insights()
                if insights.get('insights'):
                    script_data['historical_insights'] = insights
                    logger.info(f"📊 Historical insights: {len(insights['insights'])} pattern(s) found")

            except Exception as e:
                logger.warning(f"CTR prediction failed: {e}")

            # Phase 1c: French Quality + Policy Gate
            logger.info("\n🇫🇷 PHASE 1c: FRENCH QUALITY / POLICY GATE")
            quality_ok, french_quality_report = validate_publication_quality(script_data)
            script_data['french_quality_report'] = french_quality_report

            if french_quality_report.get('warnings'):
                for warning in french_quality_report['warnings']:
                    logger.warning(f"⚠️ Quality warning: {warning}")

            if not quality_ok and not ALLOW_QUALITY_OVERRIDE:
                try:
                    os.makedirs("output", exist_ok=True)
                    with open("output/blocked_script_package.json", "w", encoding="utf-8") as f:
                        json.dump(script_data, f, indent=2, ensure_ascii=False)
                    logger.error("Saved blocked package for review: output/blocked_script_package.json")
                except Exception as save_error:
                    logger.warning(f"Could not save blocked package: {save_error}")

                raise RuntimeError(
                    "French quality gate blocked this video before generation/upload: "
                    + "; ".join(french_quality_report.get('issues', []))
                )

            if not quality_ok and ALLOW_QUALITY_OVERRIDE:
                logger.warning("⚠️ Quality gate failed but ALLOW_QUALITY_OVERRIDE=true; continuing")

            # Phase 2: Image Generation
            logger.info("\n🎨 PHASE 2: IMAGE GENERATION")
            image_paths, image_sources = self._generate_images_with_retry(script_data)
            logger.info(f"✅ Generated {len(image_paths)} images")

            # Quality Gate: Check fallback ratio
            source_counts = Counter(image_sources)
            fallback_count = sum(c for src, c in source_counts.items() if src != "AI-provider")
            fallback_ratio = fallback_count / len(image_paths) if image_paths else 1.0

            logger.info(f"📊 Image sources: {dict(source_counts)}")
            logger.info(f"📊 Fallback ratio: {fallback_ratio:.1%}")

            if fallback_ratio > FALLBACK_ABORT_RATIO:
                raise RuntimeError(
                    f"Quality gate failed: {fallback_count}/{len(image_paths)} images ({fallback_ratio:.1%}) "
                    f"are fallbacks (threshold: {FALLBACK_ABORT_RATIO:.1%})"
                )

            # Phase 3: Voice Generation
            logger.info("\n🔊 PHASE 3: VOICE GENERATION")
            try:
                audio_segments = generate_voice_segments(
                    script_data['scenes'],
                    voice="ff_siwis",
                    speed=0.95
                )
                logger.info(f"✅ Generated {len(audio_segments)} audio segments")
            except Exception as e:
                logger.error(f"Voice generation failed: {e}")
                raise

            # Phase 3b: Shorts Enhancements
            logger.info("\n📝 PHASE 3b: SHORTS ENHANCEMENTS")
            try:
                shorts_report = build_shorts_report(
                    script_data,
                    audio_segments,
                    script_data.get('tags', [])
                )
                script_data['shorts_report'] = shorts_report

                if shorts_report.get('caption_pacing', {}).get('all_readable') is False:
                    for issue in shorts_report.get('caption_pacing', {}).get('issues', []):
                        logger.warning(f"⚠️ Caption pacing: {issue}")

                hook_score = shorts_report.get('hook_detail', {}).get('score', 0)
                if hook_score < 70:
                    logger.warning(f"⚠️ Hook score: {hook_score}/100 - needs improvement")

            except Exception as e:
                logger.warning(f"Shorts enhancements failed: {e}")

            # Generate SRT
            try:
                os.makedirs("output", exist_ok=True)
                srt_path = "output/captions.srt"
                generate_srt(script_data['scenes'], audio_segments, output_path=srt_path)
                script_data['srt_path'] = srt_path
                logger.info(f"✅ SRT generated: {srt_path}")
            except Exception as e:
                logger.warning(f"SRT generation failed: {e}")

            # Phase 4: Build Video
            logger.info("\n🎬 PHASE 4: BUILD VIDEO")
            try:
                final_video = build_video(image_paths, audio_segments, script_data['scenes'])
                thumb_path = generate_thumbnail(image_paths[0], script_data['title'])
                logger.info(f"✅ Video built: {final_video}")
                logger.info(f"✅ Thumbnail built: {thumb_path}")
            except Exception as e:
                logger.error(f"Video build failed: {e}")
                raise

            # Thumbnail SEO Score
            try:
                thumbnail_score = score_thumbnail(thumb_path, script_data['title'])
                script_data['thumbnail_score'] = thumbnail_score

                thumb_overall = thumbnail_score.get('overall_thumbnail_score', 0)
                logger.info(f"✅ Thumbnail score: {thumb_overall}/100")

                if thumb_overall < 60:
                    logger.warning("⚠️ Thumbnail score low - check contrast/readability")

            except Exception as e:
                logger.warning(f"Thumbnail scoring failed: {e}")

            # Phase 5: Upload
            logger.info("\n📤 PHASE 5: UPLOAD")
            if DRY_RUN:
                logger.info("DRY_RUN=true - upload skipped after building final video")
                upload_result = {
                    'youtube_success': False,
                    'youtube_video_id': None,
                    'dry_run': True
                }
            else:
                try:
                    upload_result = upload_all(final_video, thumb_path, script_data)
                    logger.info(f"✅ Upload successful: {upload_result}")
                except Exception as e:
                    logger.error(f"Upload failed: {e}")
                    # Don't raise, but save what we can.
                    upload_result = {
                        'youtube_success': False,
                        'youtube_video_id': None,
                        'error': str(e)
                    }

            # Save history
            self._save_video_history({
                'title': script_data.get('title', 'Untitled'),
                'topic': script_data.get('topic'),
                'voiceover': script_data.get('voiceover', '')[:500],
                'posted_at': datetime.now(timezone.utc).isoformat(),
                'youtube_video_id': upload_result.get('youtube_video_id'),
                'seo_score': script_data.get('seo_score', {}).get('scores', {}).get('overall_seo_score'),
                'predicted_ctr': script_data.get('ctr_prediction', {}).get('ctr_prediction'),
            })

            # Save full package for review/debugging.
            try:
                os.makedirs("output", exist_ok=True)
                with open("output/last_script_package.json", "w", encoding="utf-8") as f:
                    json.dump(script_data, f, indent=2, ensure_ascii=False)
                logger.info("Saved full script/SEO/quality package: output/last_script_package.json")
            except Exception as e:
                logger.warning(f"Could not save script package: {e}")

            elapsed = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"✅ PIPELINE COMPLETE in {elapsed:.1f}s")
            logger.info(f"📹 Video: {script_data.get('title')}")
            logger.info("=" * 60)

            return {
                'success': True,
                'title': script_data.get('title'),
                'video_path': final_video,
                'thumbnail_path': thumb_path,
                'upload_result': upload_result,
                'elapsed_time': elapsed
            }

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error("=" * 60)
            logger.error(f"❌ PIPELINE FAILED after {elapsed:.1f}s")
            logger.error(f"Error: {e}")
            logger.error(traceback.format_exc())
            logger.error("=" * 60)
            raise

    def run_daily_batch(self, num_videos: int = 3):
        """Run multiple videos in batch"""
        logger.info(f"Starting daily batch: {num_videos} videos")
        succeeded = 0
        failed = 0

        for i in range(num_videos):
            try:
                logger.info(f"\n{'=' * 40}")
                logger.info(f"VIDEO {i+1}/{num_videos}")
                logger.info(f"{'=' * 40}")

                self.run_pipeline()
                succeeded += 1

                # Wait between videos
                if i < num_videos - 1:
                    wait_time = 300  # 5 minutes
                    logger.info(f"Waiting {wait_time}s before next video...")
                    time.sleep(wait_time)

            except Exception as e:
                failed += 1
                logger.error(f"Video {i+1} failed: {e}")
                continue

        logger.info(f"Batch complete: {succeeded} succeeded, {failed} failed out of {num_videos}")


def main():
    """Main entry point"""
    try:
        pipeline = SKILLORPipeline()
        topic = os.environ.get("VIDEO_TOPIC")

        if topic:
            logger.info(f"Using specific topic: {topic}")
            pipeline.run_pipeline(topic=topic)
        else:
            batch_mode = os.environ.get("BATCH_MODE", "false").lower() == "true"
            if batch_mode:
                num_videos = int(os.environ.get("BATCH_COUNT", "3"))
                pipeline.run_daily_batch(num_videos)
            else:
                pipeline.run_pipeline()

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
