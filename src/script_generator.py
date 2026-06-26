"""
script_generator.py
Groq API ka use karke SKILLOR channel ke liye Urdu script generate karta hai.
Output: dict with {title, hook, body, cta, tool_names (list, agar koi AI tool mention hua ho)}
"""
import os
import json
import re
from groq import Groq

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
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def generate(self, topic: str) -> dict:
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

        # Kabhi kabhi model ```json fences laga deta hai, unhe hata dete hain
        raw = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # fallback: agar JSON parse fail ho jaye to plain text wrap kar do
            data = {
                "title": topic[:60],
                "hook": raw[:120],
                "body": raw,
                "cta": "SKILLOR ko follow karein!",
                "tool_names": [],
            }

        data.setdefault("tool_names", [])
        data["full_text"] = f"{data.get('hook','')} {data.get('body','')} {data.get('cta','')}".strip()
        return data


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("config/.env")
    gen = ScriptGenerator()
    result = gen.generate("ChatGPT ka naya feature jo aap nahi jante")
    print(json.dumps(result, indent=2, ensure_ascii=False))
