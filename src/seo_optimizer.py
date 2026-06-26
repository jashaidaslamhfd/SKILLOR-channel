"""
seo_optimizer.py - 2026 SEO Optimization
SEO optimization for SKILLOR videos - titles, descriptions, tags
"""
import random
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class SEOOptimizer:
    def __init__(self):
        self.channel_tags = ["#SKILLOR", "#UrduTech", "#AITools", "#PakistanTech"]
        
        self.category_tags = {
            "AI Tools": ["#ArtificialIntelligence", "#MachineLearning", "#DeepLearning"],
            "ChatGPT": ["#ChatGPT", "#OpenAI", "#GPT4"],
            "Tech News": ["#TechNews", "#Innovation", "#FutureTech"],
            "Productivity": ["#ProductivityHacks", "#WorkSmarter"],
            "Coding": ["#Programming", "#CodingLife", "#Developer"],
        }
        
        self.cta_templates = [
            "Channel SKILLOR ko follow karein aur AI ki duniya mein aagey badhein!",
            "SKILLOR ke saath AI seekhein aur apne career ko boost karein!",
            "Rozana AI tips ke liye SKILLOR ko subscribe karein!",
            "Technology ki duniya mein SKILLOR aapka guide hai!"
        ]
        
        self.power_words = ["Complete", "Easy", "Simple", "Professional", "New", "Ultimate", "Best", "Top"]
        
        logger.info("✅ SEOOptimizer initialized")
    
    def optimize_title_2026(self, title: str) -> str:
        """Optimize title for 2026 YouTube algorithm"""
        # Clean title
        title = title.strip()
        
        # Remove duplicate words
        words = title.split()
        seen = set()
        unique_words = []
        for word in words:
            if word.lower() not in seen:
                seen.add(word.lower())
                unique_words.append(word)
        title = " ".join(unique_words)
        
        # Add power word if missing
        if not any(pw.lower() in title.lower() for pw in self.power_words):
            title = f"{random.choice(self.power_words)} {title}"
        
        # Add year if missing
        if "2026" not in title and "2025" not in title:
            title = f"{title} 2026"
        
        # Add emoji (optional)
        emojis = ["🔥", "💡", "🚀", "✨"]
        if not any(emoji in title for emoji in emojis) and len(title) < 55:
            title = f"{random.choice(emojis)} {title}"
        
        # Limit to 60 chars
        if len(title) > 60:
            title = title[:57] + "..."
        
        logger.info(f"📌 Optimized Title: {title}")
        return title
    
    def generate_description_2026(self, script: Dict, tool_names: List[str]) -> str:
        """Generate SEO-optimized description"""
        tool_link = ""
        if tool_names:
            tool_name = tool_names[0]
            tool_link = f"https://{tool_name}" if not tool_name.startswith("http") else tool_name
        
        hashtags = self.generate_hashtags("Tech", tool_names)
        
        # Build description with sections
        description = f"""
{script.get('title', 'AI Tools Guide')}

📌 **Video Highlights:**
🎯 {script.get('hook', '')[:100]}
💡 {script.get('body', '')[:200]}...

🔗 **Useful Links:**
{self._generate_tool_links(tool_names)}

📝 **Key Points:**
{self._extract_key_points(script)}

🔔 **SKILLOR Community:**
📱 Instagram: @SKILLOR
🐦 Twitter/X: @SKILLOR
📘 Facebook: SKILLOR

{random.choice(self.cta_templates)}

🏷️ **Keywords:**
{self._generate_keyword_tags(script)}

#SKILLOR #UrduTech #AITools {' '.join(hashtags[:5])}
"""
        
        # Ensure min length for SEO
        while len(description) < 500:
            description += f"\nLearn more about {script.get('title', 'AI')} with SKILLOR."
        
        return description[:5000]  # YouTube max
    
    def _generate_tool_links(self, tool_names: List[str]) -> str:
        """Generate tool links"""
        if not tool_names:
            return "🌐 Visit SKILLOR for more AI tools"
        
        links = []
        for tool in tool_names[:3]:
            url = tool if tool.startswith("http") else f"https://{tool}"
            name = tool.split('.')[0].capitalize()
            links.append(f"• {name}: {url}")
        
        return "\n".join(links)
    
    def _extract_key_points(self, script: Dict) -> str:
        """Extract key points from script"""
        body = script.get("body", "")
        points = [p.strip() for p in body.split(". ") if len(p) > 10][:3]
        if not points:
            return "• AI tools tutorial\n• Complete guide\n• Urdu explanation"
        return "\n".join([f"• {p[:50]}..." for p in points])
    
    def _generate_keyword_tags(self, script: Dict) -> str:
        """Generate keyword tags"""
        title = script.get("title", "")
        words = title.split()[:5]
        return " ".join([w.replace("?", "").replace("!", "") for w in words if len(w) > 3])
    
    def generate_hashtags(self, category: str, tool_names: List[str]) -> List[str]:
        """Generate relevant hashtags"""
        hashtags = list(self.channel_tags)
        
        # Add tool hashtags
        for tool in tool_names[:2]:
            tool_clean = re.sub(r'[^a-zA-Z0-9]', '', tool.split('.')[0])
            if tool_clean:
                hashtags.append(f"#{tool_clean}")
        
        # Add category tags
        for cat, tags in self.category_tags.items():
            if cat.lower() in category.lower():
                hashtags.extend(tags[:2])
                break
        
        # Add trending tags
        trending = ["#Tech2026", "#AIForEveryone", "#DigitalPakistan"]
        hashtags.extend(random.sample(trending, 2))
        
        # Remove duplicates and limit
        hashtags = list(dict.fromkeys(hashtags))[:15]
        return hashtags


if __name__ == "__main__":
    seo = SEOOptimizer()
    title = seo.optimize_title_2026("ChatGPT ka naya feature")
    print(f"✅ Optimized: {title}")
