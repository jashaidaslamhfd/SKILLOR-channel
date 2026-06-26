"""
tool_screenshot.py
Agar script mein kisi specific AI tool (website) ka zikr ho, to Playwright us tool
ki PUBLIC website kholta hai, ek smooth scroll recording leta hai aur usay video clip
mein convert karta hai (taake editing mein use ho sake).

Note: Yeh sirf publicly accessible pages par chalayen. Login-protected ya
private dashboards automate na karein — yeh terms of service todh sakta hai.
"""
import os
import time
import subprocess
from playwright.sync_api import sync_playwright


class ToolScreenshotCapture:
    def __init__(self, viewport=(1080, 1920)):
        self.viewport = {"width": viewport[0], "height": viewport[1]}

    def capture_scroll_video(self, url: str, output_path: str = "output/clips/tool_clip.mp4",
                              duration_sec: int = 6, fps: int = 30):
        """
        Playwright ki built-in video recording feature use karta hai.
        Page open karke smooth scroll karta hai, phir webm -> mp4 convert karta hai.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tmp_dir = os.path.join(os.path.dirname(output_path), "_tmp_recording")
        os.makedirs(tmp_dir, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                viewport=self.viewport,
                record_video_dir=tmp_dir,
                record_video_size=self.viewport,
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"[ToolScreenshot] Could not load {url}: {e}")
                context.close()
                browser.close()
                return None

            page.wait_for_timeout(1000)

            # smooth scroll animation taake recording dynamic dikhe
            steps = duration_sec * 2
            for i in range(steps):
                page.mouse.wheel(0, 300)
                page.wait_for_timeout(int(1000 / 2))

            video_path_obj = page.video
            context.close()
            browser.close()

            # actual saved webm file dhoondo
            webm_path = video_path_obj.path() if video_path_obj else None

        if not webm_path or not os.path.exists(webm_path):
            print("[ToolScreenshot] recording failed, falling back to static screenshot")
            return self._static_screenshot_fallback(url, output_path)

        # webm -> mp4 convert (FFmpeg)
        subprocess.run(
            ["ffmpeg", "-y", "-i", webm_path, "-t", str(duration_sec),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path],
            check=False,
        )
        return output_path

    def _static_screenshot_fallback(self, url: str, output_path: str):
        """Agar video recording fail ho jaye, ek static screenshot se looping clip banao."""
        png_path = output_path.replace(".mp4", ".png")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport=self.viewport)
            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                page.screenshot(path=png_path)
            except Exception as e:
                print(f"[ToolScreenshot] fallback also failed: {e}")
                browser.close()
                return None
            browser.close()

        subprocess.run(
            ["ffmpeg", "-y", "-loop", "1", "-i", png_path, "-t", "5",
             "-vf", "zoompan=z='min(zoom+0.0015,1.2)':d=125",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path],
            check=False,
        )
        return output_path


if __name__ == "__main__":
    cap = ToolScreenshotCapture()
    cap.capture_scroll_video("https://chatgpt.com", "output/clips/tool_clip.mp4", duration_sec=6)
