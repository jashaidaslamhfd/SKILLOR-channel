# SKILLOR — YouTube Automation System

**SKILLOR** channel ke liye full automation pipeline jo daily 3 videos upload karta hai.

## Features
- 🤖 Auto topic selection (trending tech/AI)
- 🎙️ Urdu voiceover (Asad Neural - Edge TTS)
- 📝 Auto captions with word-level timing
- 🎬 Stock footage + tool website screenshots
- 🎞️ 9:16 vertical videos (40-55 sec)
- 🔍 Full SEO optimization
- 🖼️ Auto thumbnail generation
- 📤 YouTube auto-upload (3 videos/day)

## Setup

```bash
# Clone repo
git clone <repo-url>
cd skillor_automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Setup config
cp config/.env.example config/.env
# Edit .env with your API keys
