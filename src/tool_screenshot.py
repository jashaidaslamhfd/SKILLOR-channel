"""
tool_screenshot.py
Playwright se AI tool websites ka screenshot/clip leta hai
"""
import os
import subprocess
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class ToolScreenshotCapture:
    def __init__(self, viewport=(1080, 1920)):
        """Initialize with viewport settings"""
        self.viewport = {"width": viewport[0], "height": viewport[1]}
        logger.info(f"✅ ToolScreenshot initialized with viewport: {viewport}")
    
    def capture_scroll_video(self, url: str, output_path: str = "output/clips/tool_clip.mp4",
                              duration_sec: int = 6, fps: int = 30) -> str:
        """Capture scrolling video of a website"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tmp_dir = os.path.join(os.path.dirname(output_path), "_tmp_recording")
        os.makedirs(tmp_dir, exist_ok=True)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport=self.viewport,
                    record_video_dir=tmp_dir,
                    record_video_size=self.viewport,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                
                try:
                    # Navigate to URL
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    
                    # Smooth scroll
                    steps = duration_sec * 2
                    for i in range(steps):
                        page.mouse.wheel(0, 300)
                        page.wait_for_timeout(int(1000 / 2))
                    
                    video_path_obj = page.video
                    context.close()
                    browser.close()
                    
                    # Get webm file
                    webm_path = video_path_obj.path() if video_path_obj else None
                    
                except Exception as e:
                    logger.error(f"❌ Page loading failed: {e}")
                    context.close()
                    browser.close()
                    return self._static_screenshot_fallback(url, output_path)
            
            if not webm_path or not os.path.exists(webm_path):
                logger.warning("Recording failed, using fallback")
                return self._static_screenshot_fallback(url, output_path)
            
            # Convert webm to mp4
            subprocess.run([
                "ffmpeg", "-y", "-i", webm_path, "-t", str(duration_sec),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", 
                "-vf", f"scale={self.viewport['width']}:{self.viewport['height']}",
                output_path
            ], check=False, capture_output=True)
            
            if os.path.exists(output_path):
                logger.info(f"✅ Tool clip saved: {output_path}")
                return output_path
            else:
                return self._static_screenshot_fallback(url, output_path)
                
        except Exception as e:
            logger.error(f"❌ Tool capture failed: {e}")
            return self._static_screenshot_fallback(url, output_path)
    
    def _static_screenshot_fallback(self, url: str, output_path: str) -> str:
        """Create a static screenshot video if capture fails"""
        try:
            png_path = output_path.replace(".mp4", ".png")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport=self.viewport)
                
                try:
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")
                    page.screenshot(path=png_path)
                except Exception as e:
                    logger.error(f"❌ Screenshot fallback failed: {e}")
                    browser.close()
                    return None
                
                browser.close()
            
            if os.path.exists(png_path):
                # Create video from static image
                subprocess.run([
                    "ffmpeg", "-y", "-loop", "1", "-i", png_path, "-t", "5",
                    "-vf", f"scale={self.viewport['width']}:{self.viewport['height']},zoompan=z='min(zoom+0.0015,1.2)':d=125",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path
                ], check=False, capture_output=True)
                
                if os.path.exists(output_path):
                    logger.info(f"✅ Static fallback clip saved: {output_path}")
                    return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fallback failed: {e}")
            return None


if __name__ == "__main__":
    # Test tool screenshot
    cap = ToolScreenshotCapture()
    clip = cap.capture_scroll_video("https://chatgpt.com", "output/clips/chatgpt.mp4")
    print(f"Clip saved: {clip}")
