"""
tiktok_uploader.py
TikTok upload - 2026 Algorithm Optimized

2026 TikTok SEO Strategy:
- Use trending audio (always)
- First 3 seconds hook
- 5-15 hashtags (mix of broad + niche)
- Caption: 150-300 characters
- Use keywords in caption
- Post at peak times
- Use effects and filters
- Optimize thumbnail (first frame)
"""
import os
import time
import logging
import re
import random
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class TikTokUploader:
    def __init__(self, session_id: str = None, username: str = None, password: str = None):
        """
        Initialize TikTok Uploader - 2026 SEO Optimized
        
        Option 1: Use session_id cookie (preferred)
        Option 2: Use username/password (less reliable)
        """
        self.session_id = session_id or os.getenv("TIKTOK_SESSION_ID")
        self.username = username or os.getenv("TIKTOK_USERNAME")
        self.password = password or os.getenv("TIKTOK_PASSWORD")
        
        # 2026 TikTok SEO Config
        self.seo_config = {
            "caption_max_length": 300,
            "caption_optimal_length": 200,
            "hashtag_count": "5-10",
            "keywords_in_caption": True,
            "trending_audio": True,
            "upload_times": ["10:00", "14:00", "18:00", "21:00"],  # PST
            "max_duration": 60,
            "min_duration": 15,
            "use_effects": True,
            "call_to_action": True,
        }
        
        if not self.session_id and not (self.username and self.password):
            logger.warning("⚠️ No TikTok credentials provided. Upload may fail.")
        
        logger.info("✅ TikTokUploader initialized with 2026 SEO config")
    
    def optimize_caption_2026(self, title: str, script: dict, hashtags: list = None) -> str:
        """
        2026 TikTok Caption Optimization:
        - First 3 words: Hook
        - 150-300 characters
        - Keywords in first 40 chars
        - 3-5 hashtags
        - Call to action
        - Emojis (2-3 max)
        """
        # Extract hook
        hook = script.get("hook", title)[:50]
        
        # Extract keywords
        keywords = self._extract_tiktok_keywords(title, script)
        keyword_str = " ".join(keywords[:3])
        
        # Generate hashtags
        if not hashtags:
            hashtags = self._generate_tiktok_hashtags_2026(title, [])
        
        # CTA
        cta_options = [
            "Follow SKILLOR for daily AI tips! 🚀",
            "Learn AI with SKILLOR! Subscribe now 🔥",
            "Tech learning made easy with SKILLOR 💡",
            "SKILLOR - Your AI guide in Urdu ✨"
        ]
        cta = random.choice(cta_options)
        
        # Build caption
        caption = f"{hook} {keyword_str}\n\n{cta}\n"
        
        # Add question for engagement
        questions = [
            "Kya aap ye tool use kar rahe hain? 💭",
            "Kya aap ne ye feature try kiya? 🤔",
            "Aap ka favorite AI tool konsa hai? 👇",
            "Comment mein batayein! ✍️"
        ]
        caption += f"{random.choice(questions)}\n\n"
        
        # Add hashtags
        hashtag_str = " ".join(hashtags[:7])  # 5-7 hashtags optimal
        caption += hashtag_str
        
        # Ensure length
        if len(caption) > 300:
            caption = caption[:297] + "..."
        elif len(caption) < 150:
            # Add more context
            caption = f"{hook} {script.get('body', '')[:50]}... {cta}\n\n{hashtag_str}"
        
        logger.info(f"📝 Optimized Caption: {caption[:50]}... ({len(caption)} chars)")
        return caption
    
    def _extract_tiktok_keywords(self, title: str, script: dict) -> list:
        """Extract keywords for TikTok SEO"""
        keywords = []
        
        # From title
        title_words = title.lower().split()
        for word in title_words:
            if len(word) > 3 and word not in ["with", "from", "that", "this", "your", "2026"]:
                keywords.append(word.replace("?", "").replace("!", ""))
        
        # From script hook
        hook = script.get("hook", "")
        hook_words = hook.lower().split()[:10]
        for word in hook_words:
            if len(word) > 3 and word not in keywords:
                keywords.append(word.replace("?", "").replace("!", ""))
        
        return list(dict.fromkeys(keywords))[:5]
    
    def _generate_tiktok_hashtags_2026(self, title: str, tool_names: list = None) -> list:
        """
        2026 TikTok Hashtag Strategy:
        - 3 broad hashtags (high volume)
        - 3 specific hashtags (niche)
        - 2 trending hashtags (current)
        """
        hashtags = []
        
        # Broad hashtags
        broad = ["#AI", "#Tech", "#Urdu", "#Pakistan", "#SKILLOR"]
        hashtags.extend(random.sample(broad, min(3, len(broad))))
        
        # Tool specific
        if tool_names:
            for tool in tool_names[:2]:
                tool_clean = re.sub(r'[^a-zA-Z0-9]', '', tool.split('.')[0])
                if tool_clean:
                    hashtags.append(f"#{tool_clean}")
        
        # Topic specific
        title_words = title.lower().split()[:3]
        for word in title_words:
            if len(word) > 3 and word not in ["2026", "with", "from"]:
                hashtags.append(f"#{word.capitalize()}")
        
        # Trending 2026 hashtags
        trending = ["#TechTrends2026", "#AIForEveryone", "#DigitalPakistan", "#LearnAI"]
        hashtags.extend(random.sample(trending, min(2, len(trending))))
        
        # Remove duplicates and limit
        hashtags = list(dict.fromkeys(hashtags))[:10]
        return hashtags
    
    def get_optimal_upload_time(self) -> str:
        """Get optimal TikTok upload time"""
        # Pakistan peak times: 10 AM, 2 PM, 6 PM, 9 PM
        times = ["10:00", "14:00", "18:00", "21:00"]
        return random.choice(times)
    
    def upload(self, video_path: str, title: str, script: dict = None,
               hashtags: list = None, privacy: str = "public", 
               retry_count: int = 3) -> bool:
        """
        Upload video to TikTok with 2026 SEO optimization
        
        Args:
            video_path: Path to video file
            title: Video title (for caption generation)
            script: Script dict for caption optimization
            hashtags: List of hashtags (auto-generated if None)
            privacy: public, private, friends
            retry_count: Number of retry attempts
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(video_path):
            logger.error(f"❌ Video not found: {video_path}")
            return False
        
        # Generate SEO optimized caption
        caption = self.optimize_caption_2026(title, script or {}, hashtags)
        
        logger.info(f"📤 TikTok upload prepared:")
        logger.info(f"   Video: {os.path.basename(video_path)}")
        logger.info(f"   Caption: {caption[:50]}...")
        logger.info(f"   Privacy: {privacy}")
        
        # Try to upload with retries
        for attempt in range(retry_count):
            try:
                logger.info(f"📤 Attempt {attempt + 1}/{retry_count}...")
                
                if self._upload_with_selenium(video_path, caption, privacy):
                    logger.info("✅ TikTok upload successful!")
                    return True
                else:
                    logger.warning(f"⚠️ Upload attempt {attempt + 1} failed")
                    time.sleep(5 * (attempt + 1))
                    
            except Exception as e:
                logger.error(f"❌ Upload error: {e}")
                time.sleep(5 * (attempt + 1))
        
        logger.error("❌ All TikTok upload attempts failed")
        return False
    
    def _upload_with_selenium(self, video_path: str, caption: str, privacy: str = "public") -> bool:
        """Upload using Selenium WebDriver with 2026 optimization"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            logger.error("❌ Selenium not installed! Install: pip install selenium webdriver-manager")
            return False
        
        driver = None
        try:
            # Setup Chrome options with anti-detection
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Use session_id if available
            if self.session_id:
                logger.info("Using session_id for login")
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), 
                    options=options
                )
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Go to TikTok and set cookie
                driver.get("https://www.tiktok.com")
                time.sleep(3)
                
                driver.add_cookie({
                    "name": "sessionid",
                    "value": self.session_id,
                    "domain": ".tiktok.com"
                })
                
                logger.info("Session cookie set")
                time.sleep(2)
                driver.refresh()
                time.sleep(3)
            
            elif self.username and self.password:
                logger.info("Using username/password for login")
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), 
                    options=options
                )
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self._login_manual(driver)
            else:
                logger.error("❌ No TikTok credentials provided!")
                return False
            
            # Navigate to upload page
            driver.get("https://www.tiktok.com/upload")
            time.sleep(5)
            
            # Find file input and upload video
            try:
                file_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                file_input.send_keys(os.path.abspath(video_path))
                logger.info("Video file selected")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ File input not found: {e}")
                return False
            
            # Wait for upload to complete (with progress check)
            upload_complete = False
            wait_time = 45
            
            for i in range(wait_time):
                time.sleep(1)
                try:
                    # Check if processing is complete
                    processing_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Processing')]")
                    if not processing_elements:
                        # Check for caption box (indicates upload complete)
                        caption_boxes = driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
                        if caption_boxes:
                            upload_complete = True
                            logger.info("Upload complete, adding caption...")
                            break
                except:
                    pass
            
            if not upload_complete:
                logger.warning("⚠️ Upload may not be complete, continuing...")
            
            # Add SEO optimized caption
            try:
                # Find caption box
                caption_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                )
                caption_box.click()
                caption_box.clear()
                
                # Type caption with natural delay
                for char in caption:
                    caption_box.send_keys(char)
                    time.sleep(random.uniform(0.02, 0.08))
                
                logger.info(f"Caption added: {caption[:50]}...")
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Caption input not found: {e}")
                return False
            
            # Add trending audio (if available)
            try:
                audio_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Add sound')]")
                audio_button.click()
                time.sleep(2)
                
                # Select trending audio (first one)
                trending_audio = driver.find_elements(By.XPATH, "//div[contains(@class, 'sound-item')]")[0]
                trending_audio.click()
                time.sleep(2)
                logger.info("✅ Trending audio selected!")
            except:
                logger.warning("⚠️ Could not add trending audio")
            
            # Set privacy
            if privacy != "public":
                try:
                    privacy_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Who can view')]")
                    privacy_button.click()
                    time.sleep(1)
                    
                    privacy_option = driver.find_element(By.XPATH, f"//span[contains(text(), '{privacy.capitalize()}')]")
                    privacy_option.click()
                    time.sleep(1)
                except:
                    logger.warning("⚠️ Could not set privacy")
            
            # Post
            try:
                post_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Post')]"))
                )
                post_button
