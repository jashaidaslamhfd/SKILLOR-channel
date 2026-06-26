"""
tiktok_uploader.py
TikTok ke liye OFFICIAL "Content Posting API" sabse reliable tareeqa hai
(developer account chahiye: https://developers.tiktok.com/).

Yeh file ek Selenium-based FALLBACK deti hai sirf testing/manual-assist ke liye.
⚠️ TikTok automation unka ToS torta hai aur account flag/ban ho sakta hai —
production use ke liye Content Posting API par migrate karna recommended hai.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TikTokUploader:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or os.getenv("TIKTOK_SESSION_ID")

    def upload(self, video_path: str, caption: str):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        try:
            driver.get("https://www.tiktok.com")
            driver.add_cookie({"name": "sessionid", "value": self.session_id, "domain": ".tiktok.com"})
            driver.get("https://www.tiktok.com/upload")
            time.sleep(5)

            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(os.path.abspath(video_path))
            time.sleep(10)  # processing wait

            caption_box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
            caption_box.send_keys(caption)
            time.sleep(2)

            post_button = driver.find_element(By.XPATH, "//button[contains(text(),'Post')]")
            post_button.click()
            time.sleep(5)
            print("✅ TikTok upload submit ho gaya (manually verify kar lein).")
        finally:
            driver.quit()
