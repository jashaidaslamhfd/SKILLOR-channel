"""
script_generator.py
Groq API se Urdu script generate karta hai SKILLOR channel ke liye
"""
import os
import json
import re
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv("config/.env")

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tum ek professional YouTube Shorts script writer ho, channel ka naam "SKILLOR" hai.
Channel ka niche: Tech aur AI Tools. Audience: Pakistan aur India ke log.
Script hamesha simple, rawan Urdu mein likho (zaroorat ho to thoda Roman Urdu mix kar sakte ho), bilkul casual aur energetic tone mein jaisay koi dost samjha raha ho.

Rules:
- Pehli line ek strong "hook" honi chahiye (3-5 second attention grabber).
- Total script 45-60 second ke video ke liye ho (tareeban 130-170 alfaaz).
- Agar topic kisi specific AI tool (jese ChatGPT, Midjourney, Canva AI, etc) ke baare mein hai, tool ka naam clearly mention karo.
- End mein ek chhota CTA ho: "SKILLOR ko follow karein".
- Output STRICTLY JSON format mein do, kisi aur text ke bina:

{
  "title": "video ka catchy title (Urdu/Roman Urdu mix, max 60 chars)",
  "hook": "pehli 1-2 lines",
  "body": "baqi pura script (hook ke baad)",
  "cta": "end line",
  "tool_names": ["agar koi specific AI tool/website mention hui ho to uska exact name, jese 'chatgpt.com' ya 'midjourney.com'; warna empty list"]
}
"""


class ScriptGenerator:
    def __init__(self, api_key: str = None, model: str = None):
        """Initialize ScriptGenerator with Groq API"""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GROQ_API_KEY not found! Please set in .env file")
        
        # Try to import Groq with error handling
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except TypeError as e:
            # Fallback for older versions
            logger.warning(f"Groq initialization error: {e}, trying fallback...")
            try:
                # For older groq versions
                import groq
                self.client = groq.Client(api_key=self.api_key)
            except:
                # Ultimate fallback - use requests directly
                self.client = None
                logger.warning("Using requests fallback for Groq API")
        
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        logger.info(f"✅ ScriptGenerator initialized with model: {self.model}")
    
    def generate(self, topic: str) -> dict:
        """Generate script for given topic"""
        try:
            if self.client:
                # Use Groq client
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Topic: {topic}\n\nIs topic par script likho."},
                    ],
                    temperature=0.8,
                    max_tokens=800,
                )
                
                raw = completion.choices[0].message.content.strip()
            else:
                # Fallback: Use requests directly
                raw = self._generate_with_requests(topic)
            
            # Remove markdown code fences
            raw = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()
            raw = re.sub(r"^```|```$", "", raw, flags=re.MULTILINE).strip()
            
            # Try to parse JSON
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(f"JSON parse failed, using fallback: {raw[:100]}...")
                data = self._create_fallback_script(topic, raw)
            
            # Ensure required fields
            data.setdefault("tool_names", [])
            data.setdefault("cta", "SKILLOR ko follow karein!")
            
            # Create full text
            data["full_text"] = f"{data.get('hook', '')} {data.get('body', '')} {data.get('cta', '')}".strip()
            
            # Extract tool names if not present
            if not data.get("tool_names"):
                data["tool_names"] = self._extract_tool_names(data.get("body", ""))
            
            logger.info(f"✅ Script generated: {data.get('title', topic)}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Script generation failed: {e}")
            return self._create_fallback_script(topic, str(e))
    
    def _generate_with_requests(self, topic: str) -> str:
        """Fallback: Use requests directly to call Groq API"""
        import requests
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Topic: {topic}\n\nIs topic par script likho."},
            ],
            "temperature": 0.8,
            "max_tokens": 800,
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    def _extract_tool_names(self, text: str) -> list:
        """Extract tool names from script text"""
        tools = ["chatgpt", "midjourney", "canva", "perplexity", "notion", 
                 "deepseek", "claude", "gemini", "copilot", "cursor"]
        
        found = []
        for tool in tools:
            if tool.lower() in text.lower():
                found.append(f"{tool}.com")
        
        return list(dict.fromkeys(found))[:2]  # Max 2 tools
    
    def _create_fallback_script(self, topic: str, error_msg: str = "") -> dict:
        """Create fallback script if API fails"""
        # Extract tool name from topic
        tool_names = self._extract_tool_names(topic)
        
        return {
            "title": topic[:60],
            "hook": f"Assalam-o-Alaikum! Aaj ki baat hai {topic}",
            "body": f"Ya video {topic} ke baare mein hai. AI tools ki duniya mein SKILLOR aapka guide hai!",
            "cta": "SKILLOR ko follow karein!",
            "tool_names": tool_names,
            "full_text": f"Assalam-o-Alaikum! Aaj ki baat hai {topic}. Ya video {topic} ke baare mein hai. AI tools ki duniya mein SKILLOR aapka guide hai! SKILLOR ko follow karein!"
        }


if __name__ == "__main__":
    # Test script generator
    gen = ScriptGenerator()
    result = gen.generate("Midjourney se professional images kaise banayein")
    print(json.dumps(result, indent=2, ensure_ascii=False))
