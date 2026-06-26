"""
stock_footage.py
Pexels aur Pixabay APIs se topic-relevant stock video clips download karta hai.
"""
import os
import requests


class StockFootageFetcher:
    def __init__(self, pexels_key: str = None, pixabay_key: str = None):
        self.pexels_key = pexels_key or os.getenv("PEXELS_API_KEY")
        self.pixabay_key = pixabay_key or os.getenv("PIXABAY_API_KEY")

    def _search_pexels(self, query: str, per_page: int = 5):
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.pexels_key}
        params = {"query": query, "per_page": per_page, "orientation": "portrait"}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        videos = r.json().get("videos", [])
        results = []
        for v in videos:
            # best vertical-ish file dhoondo
            files = sorted(v["video_files"], key=lambda f: f.get("height", 0), reverse=True)
            if files:
                results.append(files[0]["link"])
        return results

    def _search_pixabay(self, query: str, per_page: int = 5):
        url = "https://pixabay.com/api/videos/"
        params = {"key": self.pixabay_key, "q": query, "per_page": per_page}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        results = []
        for h in hits:
            videos = h.get("videos", {})
            link = videos.get("large", {}).get("url") or videos.get("medium", {}).get("url")
            if link:
                results.append(link)
        return results

    def fetch(self, query: str, count: int = 5, save_dir: str = "output/clips") -> list:
        os.makedirs(save_dir, exist_ok=True)
        urls = []

        try:
            urls.extend(self._search_pexels(query, per_page=count))
        except Exception as e:
            print(f"[Pexels] search failed: {e}")

        if len(urls) < count:
            try:
                urls.extend(self._search_pixabay(query, per_page=count - len(urls)))
            except Exception as e:
                print(f"[Pixabay] search failed: {e}")

        saved_paths = []
        for i, url in enumerate(urls[:count]):
            path = os.path.join(save_dir, f"stock_{i}.mp4")
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                with open(path, "wb") as f:
                    f.write(resp.content)
                saved_paths.append(path)
            except Exception as e:
                print(f"Download failed for {url}: {e}")

        return saved_paths
