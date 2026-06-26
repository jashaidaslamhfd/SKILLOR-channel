"""
tool_screenshot.py
Playwright se AI tool websites ka screenshot/clip leta hai
"""
import os
import subprocess
import logging
import asyncio
from playwright.async_api import async_playwright

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
            # Run async function
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self._capture_async(url, output_path, duration_sec, tmp_dir)
                )
                loop.close()
            except RuntimeError:
                result = asyncio.run(
                    self._capture_async(url, output_path, duration_sec, tmp_dir)
                )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Tool capture failed: {e}")
            return self._static_screenshot_fallback(url, output_path)
    
    async def _capture_async(self, url: str, output_path: str, duration_sec: int, tmp_dir: str) -> str:
        """Async version of capture"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport=self.viewport,
                    record_video_dir=tmp_dir,
                    record_video_size=self.viewport,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                try:
                    # Clean URL
                    clean_url = self._clean_url(url)
                    logger.info(f"🌐 Navigating to: {clean_url}")
                    
                    # Navigate to URL
                    await page.goto(clean_url, timeout=30000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    
                    # Smooth scroll
                    steps = duration_sec * 2
                    for i in range(steps):
                        await page.mouse.wheel(0, 300)
                        await page.wait_for_timeout(int(1000 / 2))
                    
                    video_path_obj = await page.video.path()
                    await context.close()
                    await browser.close()
                    
                    webm_path = video_path_obj if video_path_obj else None
                    
                except Exception as e:
                    logger.error(f"❌ Page loading failed: {e}")
                    await context.close()
                    await browser.close()
                    return await self._static_screenshot_async(url, output_path)
            
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
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL"""
        url = url.strip()
        
        # Remove spaces
        url = url.replace(" ", "")
        
        # Add https if no protocol
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        
        # Remove trailing slashes
        url = url.rstrip("/")
        
        return url
    
    async def _static_screenshot_async(self, url: str, output_path: str) -> str:
        """Async static screenshot fallback"""
        try:
            png_path = output_path.replace(".mp4", ".png")
            clean_url = self._clean_url(url)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport=self.viewport)
                
                try:
                    await page.goto(clean_url, timeout=20000, wait_until="domcontentloaded")
                    await page.screenshot(path=png_path)
                except Exception as e:
                    logger.error(f"❌ Screenshot fallback failed: {e}")
                    await browser.close()
                    return None
                
                await browser.close()
            
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
    
    def _static_screenshot_fallback(self, url: str, output_path: str) -> str:
        """Synchronous static screenshot fallback"""
        try:
            # Use asyncio to run async fallback
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._static_screenshot_async(url, output_path))
                loop.close()
                return result
            except RuntimeError:
                return asyncio.run(self._static_screenshot_async(url, output_path))
        except Exception as e:
            logger.error(f"❌ Fallback failed: {e}")
            return None


if __name__ == "__main__":
    # Test tool screenshot
    cap = ToolScreenshotCapture()
    clip = cap.capture_scroll_video("https://notion.ai", "output/clips/notion.mp4")
    print(f"Clip saved: {clip}")
