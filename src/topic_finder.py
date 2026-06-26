"""
topic_finder.py
Auto-find trending tech/AI topics for SKILLOR channel
"""
import random
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TopicFinder:
    def __init__(self):
        self.categories = [
            "AI Tools", "ChatGPT", "Machine Learning", "Tech News",
            "Productivity", "Coding", "Digital Marketing", "Cybersecurity",
            "Data Science", "Cloud Computing", "Web Development"
        ]
        
        # Curated trending topics for SKILLOR
        self.trending_pool = [
            # AI Tools
            {"topic": "ChatGPT vs DeepSeek - Kaunsa Best?", "category": "AI Tools"},
            {"topic": "AI se website kaise banayein 5 minute mein", "category": "AI Tools"},
            {"topic": "Top 5 AI Tools for Video Editing 2026", "category": "AI Tools"},
            {"topic": "Canva AI - Professional designs in seconds", "category": "AI Tools"},
            {"topic": "Best FREE AI tools for students", "category": "AI Tools"},
            {"topic": "AI art generators - Midjourney vs DALL-E", "category": "AI Tools"},
            {"topic": "AI se passive income kaise kamayein", "category": "AI Tools"},
            {"topic": "DeepSeek - New AI from China", "category": "AI Tools"},
            {"topic": "AI coding assistants - GitHub Copilot vs Cursor", "category": "AI Tools"},
            {"topic": "Notion AI - Complete guide in Urdu", "category": "AI Tools"},
            {"topic": "AI video generators - YouTube automation", "category": "AI Tools"},
            {"topic": "Perplexity AI kya hai aur kaise use karein", "category": "AI Tools"},
            
            # ChatGPT
            {"topic": "ChatGPT ka naya feature jo aap nahi jante", "category": "ChatGPT"},
            {"topic": "ChatGPT plugins kaise use karein", "category": "ChatGPT"},
            {"topic": "ChatGPT vs DeepSeek - Comparison", "category": "ChatGPT"},
            {"topic": "ChatGPT prompts for better results", "category": "ChatGPT"},
            
            # Tech News
            {"topic": "Artificial Intelligence in Pakistan - Future Jobs", "category": "Tech News"},
            {"topic": "Google AI vs Microsoft AI - Comparison", "category": "Tech News"},
            {"topic": "Machine Learning roadmap 2026", "category": "Data Science"},
            {"topic": "AI trends 2026 - What's coming", "category": "Tech News"},
            
            # Productivity
            {"topic": "AI se resume kaise banayein 2 minute mein", "category": "Productivity"},
            {"topic": "Free AI tools jo Pakistan mein famous ho rahe hain", "category": "AI Tools"},
            {"topic": "Midjourney se professional images kaise banayein", "category": "AI Tools"},
            {"topic": "Canva AI se video editing kaise karein", "category": "AI Tools"},
        ]
        
        logger.info(f"✅ TopicFinder initialized with {len(self.trending_pool)} topics")
    
    def get_trending_topics(self, count: int = 10) -> List[Dict]:
        """Get trending topics"""
        # Shuffle and select
        shuffled = random.sample(self.trending_pool, min(count, len(self.trending_pool)))
        
        topics = []
        for i, item in enumerate(shuffled):
            topics.append({
                "id": i + 1,
                "title": item["topic"],
                "category": item["category"],
                "trending_score": random.randint(70, 100),
                "source": "SKILLOR_curated"
            })
        
        logger.info(f"📌 Selected {len(topics)} topics")
        return topics
    
    def get_ai_tool_topics(self) -> List[str]:
        """Get AI tool specific topics"""
        tools = [
            "ChatGPT", "DeepSeek", "Midjourney", "Canva AI", 
            "Perplexity AI", "Notion AI", "Claude AI", "Gemini",
            "DALL-E 3", "Stable Diffusion", "GitHub Copilot",
            "Cursor AI", "Adobe Firefly", "Runway ML"
        ]
        
        topics = []
        for tool in tools:
            angle = random.choice([
                f"{tool} se professional kaam kaise karein",
                f"{tool} - Complete beginner guide",
                f"{tool} vs competitors - Comparison",
                f"{tool} new features you don't know",
                f"{tool} - Best AI tool for {random.choice(['design','coding','writing','video'])}"
            ])
            topics.append(angle)
        
        return topics


if __name__ == "__main__":
    finder = TopicFinder()
    topics = finder.get_trending_topics(5)
    for t in topics:
        print(f"📌 {t['title']} ({t['category']})")
