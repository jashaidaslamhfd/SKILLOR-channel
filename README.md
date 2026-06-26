# SKILLOR — YouTube Automation System

Channel **SKILLOR** ke liye full automation pipeline:
1. **Groq API** se Urdu script generate karta hai (AI tools / Tech topic par)
2. **Edge TTS** se Urdu voice (Asad voice) banata hai
3. Voice se **captions (.srt)** auto-sync karta hai (word-level timing)
4. **Pexels / Pixabay** se relevant stock clips download karta hai
5. Agar topic kisi **AI tool** ke baare mein ho, to **Playwright** us tool ki website kholta hai, screenshot/scroll-recording leta hai, aur usay clip mein convert karta hai
6. **FFmpeg** se sab kuch (voice + clips + captions) combine karke final video banata hai
7. **YouTube** (aur optionally **TikTok**) par auto-upload karta hai

---

## 📁 Folder Structure
```
skillor_automation/
├── config/
│   ├── settings.yaml          # saari settings (API keys, voice, channel info)
│   └── .env.example            # environment variables template
├── src/
│   ├── script_generator.py     # Groq se Urdu script
│   ├── tts_generator.py        # Edge TTS - voice + timestamps
│   ├── caption_generator.py    # .srt caption banata hai
│   ├── stock_footage.py        # Pexels/Pixabay se clips
│   ├── tool_screenshot.py      # Playwright - AI tool website ka clip
│   ├── video_assembler.py      # FFmpeg se final video assemble
│   ├── youtube_uploader.py     # YouTube Data API upload
│   ├── tiktok_uploader.py      # TikTok upload (Selenium based)
│   └── pipeline.py             # sab steps ko chalata hai (main orchestrator)
├── main.py                      # entry point — `python main.py "topic"`
├── requirements.txt
└── README.md
```

## ⚙️ Setup

```bash
cd skillor_automation
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium

cp config/.env.example config/.env
# .env file mein apni API keys daal dein
```

### Zaroori API Keys (.env mein)
| Key | Kahan se milegi | Free? |
|---|---|---|
| `GROQ_API_KEY` | https://console.groq.com | ✅ Free tier |
| `PEXELS_API_KEY` | https://www.pexels.com/api/ | ✅ Free |
| `PIXABAY_API_KEY` | https://pixabay.com/api/docs/ | ✅ Free |
| `YOUTUBE_CLIENT_SECRET_FILE` | Google Cloud Console → YouTube Data API v3 OAuth | ✅ Free |
| `TIKTOK_SESSION_ID` | Browser cookie (`sessionid`) login ke baad | — |

## 🚀 Run Karna

```bash
python main.py --topic "ChatGPT ka naya feature jo aap nahi jante" --upload yes
```

Yeh automatically:
- Groq se script likhega
- Edge TTS Urdu voice (`ur-PK-AsadNeural`) generate karega
- Captions banayega
- Topic ke hisaab se stock footage ya tool screenshot lega
- Final video `output/` folder mein save karega
- (agar `--upload yes`) YouTube + TikTok par upload karega

## ⚠️ Important Notes
- **TikTok/YouTube login automation** Selenium se rate-limit/ban ka risk leta hai — official **YouTube Data API** zyada reliable hai (is project mein already use ki gayi hai). TikTok ke liye official **Content Posting API** apply karna best practice hai; yahan Selenium fallback diya gaya hai sirf testing ke liye.
- Playwright tool-screenshot feature sirf **public, non-login websites** par chalayen — login wali sites par automation unki Terms of Service todh sakta hai.
- Pehli baar chalane par YouTube OAuth browser window khulegi — ek dafa login/permission dena hoga, token cache ho jayega.
