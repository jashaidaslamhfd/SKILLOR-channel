"""
stock_footage.py
Pexels aur Pixabay APIs se topic-relevant stock clips download karta hai
"""
import os
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StockFootageFetcher:
    def __init__(self, pexels_key: str = None, pixabay_key: str = None):
        """Initialize with API keys"""
        self.pexels_key = pexels_key or os.getenv("PEXELS_API_KEY")
        self.pixabay_key = pixabay_key or os.getenv("PIXABAY_API_KEY")
        
        if not self.pexels_key and not self.pixabay_key:
            logger.warning("No stock footage API keys provided!")
    
    def _search_pexels(self, query: str, per_page: int = 5) -> list:
        """Search Pexels for video clips"""
        if not self.pexels_key:
            return []
        
        try:
            url = "https://api.pexels.com/videos/search"
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "portrait"
            }
            
            r = requests.get(url, headers=headers, params=params, timeout=15)
            r.raise_for_status()
            
            videos = r.json().get("videos", [])
            results = []
            
            for v in videos:
                # Get highest quality vertical file
                files = sorted(
                    v.get("video_files", []),
                    key=lambda f: f.get("height", 0),
                    reverse=True
                )
                if files:
                    results.append(files[0]["link"])
            
            logger.info(f"✅ Found {len(results)} clips from Pexels")
            return results
            
        except Exception as e:
            logger.error(f"❌ Pexels search failed: {e}")
            return []
    
    def _search_pixabay(self, query: str, per_page: int = 5) -> list:
        """Search Pixabay for video clips"""
        if not self.pixabay_key:
            return []
        
        try:
            url = "https://pixabay.com/api/videos/"
            params = {
                "key": self.pixabay_key,
                "q": query,
                "per_page": per_page
            }
            
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            
            hits = r.json().get("hits", [])
            results = []
            
            for h in hits:
                videos = h.get("videos", {})
                # Try different quality levels
                for quality in ["large", "medium", "small"]:
                    video = videos.get(quality, {})
                    link = video.get("url")
                    if link:
                        results.append(link)
                        break
            
            logger.info(f"✅ Found {len(results)} clips from Pixabay")
            return results
            
        except Exception as e:
            logger.error(f"❌ Pixabay search failed: {e}")
            return []
    
    def fetch(self, query: str, count: int = 5, save_dir: str = "output/clips") -> list:
        """Fetch and download stock clips"""
        os.makedirs(save_dir, exist_ok=True)
        
        # Try Pexels first
        urls = self._search_pexels(query, per_page=count)
        
        # If not enough, try Pixabay
        if len(urls) < count:
            remaining = count - len(urls)
            pixabay_urls = self._search_pixabay(query, per_page=remaining)
            urls.extend(pixabay_urls)
        
        # Download files
        saved_paths = []
        for i, url in enumerate(urls[:count]):
            try:
                path = os.path.join(save_dir, f"stock_{i}.mp4")
                
                # Download with stream
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                with open(path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                saved_paths.append(path)
                logger.info(f"✅ Downloaded: {path}")
                
            except Exception as e:
                logger.error(f"❌ Download failed for {url}: {e}")
        
        return saved_paths


if __name__ == "__main__":
    # Test stock footage
    from dotenv import load_dotenv
    load_dotenv("config/.env")
    
    fetcher = StockFootageFetcher()
    clips = fetcher.fetch("AI technology", count=3, save_dir="output/test_clips")
    print(f"Downloaded {len(clips)} clips")
