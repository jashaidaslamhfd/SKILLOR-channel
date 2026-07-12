# YouTube Shorts Automation - Usage Guide

## Quick Start

### 1. Setup
```bash
python setup.py
```

### 2. Configure API Keys
Edit `.env` file with your API keys:
```bash
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
HF_API_KEY=your_huggingface_key
YT_CLIENT_SECRET='{...}'
FB_ACCESS_TOKEN=your_facebook_token
FB_PAGE_ID=your_facebook_page_id
```

### 3. Run Pipeline

#### Single Video (Default Topic)
```bash
python src/main.py
```

#### Single Video (Custom Topic)
```bash
python src/main.py --topic "Why Babies Need to Crawl Before Walking"
```

#### Daily Batch (3 Videos at Peak Times)
```bash
python src/main.py --batch 3
```

#### Custom Batch Size
```bash
python src/main.py --batch 5
```

---

## Pipeline Phases

### Phase 1: Specialized Content Generation
- Selects topic from Brain & Body Science database
- Generates hook-optimized script
- Quality checking (hook, engagement, pacing)
- Anti-spam analysis
- Medical accuracy validation

### Phase 2: Image Generation
- Google Gemini (Priority 1)
- Hugging Face FLUX.1 (Fallback)
- Placeholder images (Last resort)

### Phase 3: Voice Generation
- Kokoro TTS (American English)
- Audio normalization
- Quality validation

### Phase 4: Video Composition
- Image + Audio sync
- Caption overlays
- Zoom effects
- Smooth transitions

### Phase 5: Thumbnail Generation
- Aspect ratio optimization
- Professional styling
- Text overlay

### Phase 6: Scheduling
- USA peak time detection
- Timezone conversion
- Queue management

### Phase 7: Publishing
- YouTube upload with metadata
- Facebook Reels upload
- Status tracking

---

## Available Topics (Brain & Body Science)

1. Why Babies Need to Crawl Before Walking
2. The 3 Sleep Stages Every Baby Parent Must Know
3. Brain Development Milestones: 0-6 Months
4. Right Brain vs Left Brain: How Parents Can Help
5. The Science Behind Baby Babbling
6. Motor Skill Development Timeline
7. How Touch Develops Baby's Brain
8. Language Development: What Parents Miss
9. Sensory Development in First Year
10. Why Babies Cry: The Neuroscience
11. Attachment Theory: Science Explained
12. Brain Growth Nutrition for Babies
13. The 4 Month Sleep Regression Explained
14. How Play Develops Your Baby's Brain
15. Emotional Intelligence in Toddlers
16. Why Babies Love Repetition: Brain Science
17. Object Permanence Development Explained
18. Mirror Neurons and Baby Learning
19. Bilingual Brain Development in Babies
20. How Music Helps Baby Brain Development

---

## Quality Metrics

Each video is scored on:
- **Hook Score** (0-100): First 3 seconds attention grab
- **Engagement Score** (0-100): Overall engagement potential
- **Pacing Score** (0-100): Timing for 50-60 second format
- **CTA Score** (0-100): Call-to-action effectiveness
- **Overall Quality** (0-100): Combined score

**Approval Threshold:** 75+

---

## Anti-Spam Checks

Each video is analyzed for:
- Keyword stuffing
- Plagiarism (vs previous videos)
- Engagement bait
- Title quality
- Content similarity
- Duplicate detection

**Risk Levels:** LOW, MEDIUM, HIGH, CRITICAL

---

## Output Files

```
output/
├── final_video.mp4          # Generated video
├── thumbnail.jpg            # YouTube thumbnail
├── voice.wav                # Generated audio
└── video_history.json       # Track of all videos

scene_0.png
scene_1.png
scene_2.png
... (generated images)
```

---

## Monitoring & Analytics

After publishing, track these metrics:
1. **CTR** (Click-Through Rate) - Target: 8%+
2. **View Duration** - Target: 50%+ of video length
3. **Swap Rate** - Target: 20% (from current 72%)
4. **Engagement Rate** - Target: 80%+
5. **Subscriber Growth** - Monthly tracking

---

## Troubleshooting

### Image Generation Fails
```
Error: Koi image generate nahi hui

Solution:
1. Check GEMINI_API_KEY and HF_API_KEY
2. Ensure assets/placeholder.png exists
3. Try with placeholder only
```

### YouTube Upload Fails
```
Error: YT_CLIENT_SECRET missing

Solution:
1. Create service account in Google Cloud
2. Enable YouTube Data API v3
3. Download credentials JSON
4. Set YT_CLIENT_SECRET in .env
```

### Facebook Upload Fails
```
Error: FB_ACCESS_TOKEN missing

Solution:
1. Get access token from Facebook Developers
2. Ensure token has required permissions
3. Verify FB_PAGE_ID is correct
```

### Spam Risk Too High
```
Error: Spam risk too high: CRITICAL

Solution:
1. Rewrite script with different angle
2. Change title wording
3. Vary keywords and phrasing
4. Check against recent videos
```

---

## Advanced Configuration

### Custom Peak Times
Edit `scheduler.py` `PEAK_TIMES` to customize posting times:

```python
PEAK_TIMES = [
    {'hour': 6, 'minute': 0, 'zone': 'EST', 'name': 'Early Morning'},
    {'hour': 12, 'minute': 30, 'zone': 'EST', 'name': 'Lunch Time'},
    {'hour': 20, 'minute': 0, 'zone': 'EST', 'name': 'Evening'},
]
```

### Quality Thresholds
Edit `quality_checker.py` to adjust:

```python
self.hook_threshold = 0.8
self.engagement_threshold = 0.75
self.pacing_threshold = 0.8
```

---

## Performance Tips

1. **Faster Generation:** Use Hugging Face (faster than Gemini)
2. **Higher Quality:** Use Gemini (more creative)
3. **Batch Processing:** Run multiple videos overnight
4. **Rate Limiting:** Space out API calls to avoid throttling
5. **Caching:** Reuse generated images where appropriate

---

## Support

For issues:
1. Check README.md
2. Review AUTOMATION_REQUIREMENTS.md
3. Check logs in output/ directory
4. GitHub Issues: https://github.com/jashaidaslamhfd/SKILLOR/issues

---

**Made for USA Parents • Brain & Body Science • 3x Daily • Peak Times • Zero Spam**
