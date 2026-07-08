# Image Fallback System — Duniya ke Bade Platforms, 50 tak

## Ab kya hai (8 providers, sab real aur working code)

| # | Provider | Key chahiye? | Notes |
|---|----------|-------------|-------|
| 1 | Pollinations (flux) | ❌ | free, no signup |
| 2 | Pollinations (turbo) | ❌ | free, no signup, alag seed/model |
| 3 | Hugging Face | ✅ `HF_API_KEY` | free monthly credit |
| 4 | Google Gemini | ✅ `GEMINI_API_KEY` | ~50 free req/day, no card |
| 5 | DeepAI | ✅ `DEEPAI_API_KEY` | free tier |
| 6 | Craiyon | ❌ | free, no signup |
| 7 | ModelsLab | ✅ `MODELSLAB_API_KEY` | 10,000+ models, free key, no card |
| 8 | Replicate | ✅ `REPLICATE_API_TOKEN` | bada platform, free trial credits |

Ye sab `src/image_providers.py` mein ek hi `PROVIDER_REGISTRY` list mein hain.
Jaise hi ek fail/rate-limit ho, agla try hota hai — dono `image_generator.py`
(live per-video generation) aur `generate_fallback_images.py` (500-image pool
builder) isi list ko use karte hain.

## Honest reality check — "50 tools" ka matlab

Duniya mein 50 image-gen platforms exist karte hain, lekin:
- Har ek ki apni free-tier policy hai, aur ye policies har 2-3 mahine mein
  badalti rehti hain (jaisa aapke log mein dikha — HuggingFace credits khatam
  ho gaye, Gemini quota exceed ho gaya).
- Kuch (Stability AI, OpenAI DALL-E, Adobe Firefly) ab **bilkul free nahi**
  hain — sirf trial credit dete hain, phir paid ho jate hain.
- Isliye "50 simultaneously free" ka wada koi bhi honestly nahi de sakta.

**Jo maine banaya hai wo isse behtar hai**: ek architecture jahan aap jitne
bhi free-tier keys bana sakte hain (zyada tar sirf email se free milti hain),
unhe 5 minute mein registry mein daal sakte hain — system khud unke beech
rotate karega. Neeche list hai kis tarah 50 tak pahunchein.

## 50 tak kaise pahunchein — agle candidates

Inme se har ek ki free/trial key bana kar `PROVIDER_REGISTRY` mein TEMPLATE
pattern se add kar dein (`src/image_providers.py` ke end mein `gen_TEMPLATE`
copy karke):

| Platform | Free access | Env var suggestion |
|----------|-------------|---------------------|
| Stability AI | $5-25 one-time trial credit | `STABILITY_API_KEY` |
| Leonardo AI | daily free tokens | `LEONARDO_API_KEY` |
| Segmind | free credits on signup | `SEGMIND_API_KEY` |
| Together AI | free trial credit | `TOGETHER_API_KEY` |
| Fireworks AI | free trial credit | `FIREWORKS_API_KEY` |
| Cloudflare Workers AI | free tier on Cloudflare account | `CF_API_TOKEN` |
| Ideogram | 10 free credits/week | `IDEOGRAM_API_KEY` |
| Getimg.ai | free daily credits | `GETIMG_API_KEY` |
| Fal.ai | free trial credit | `FAL_API_KEY` |
| Playground AI | free daily generations | `PLAYGROUND_API_KEY` |
| StableDiffusionAPI.com | free trial credits | `SDAPI_KEY` |
| OpenAI DALL-E | paid only, last-resort layer if you already pay for GPT | `OPENAI_API_KEY` |

Har naye provider ke liye docs check karein (endpoints/format waqt ke sath
badalte hain) — is repo mein maujood 8 providers ka code hi pattern hai
jise copy karna hai.

## GitHub Actions Secrets

Repo → **Settings → Secrets and variables → Actions** → jo bhi keys banayein
unhe wahan add karein, phir workflow YAML mein:

```yaml
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  HF_API_KEY: ${{ secrets.HF_API_KEY }}
  DEEPAI_API_KEY: ${{ secrets.DEEPAI_API_KEY }}
  MODELSLAB_API_KEY: ${{ secrets.MODELSLAB_API_KEY }}
  REPLICATE_API_TOKEN: ${{ secrets.REPLICATE_API_TOKEN }}
```

Jo key set nahi hogi uska provider automatically skip ho jayega
(`available_providers()` khud check karta hai) — kuch bhi crash nahi hoga.

## Fallback pool bhi zaroor banayein

Live providers fail hone par final safety net `assets/fallback_images/`
folder hai. Ye khali hai to system same `assets/placeholder.png` baar baar
use karta hai (yehi aapke channel ka masla tha). Ek baar chalayein:

```bash
python scripts/generate_fallback_images.py
```

Ye sab 8 providers ke beech rotate karke 500 unique images banayega. Inhe
commit kar dein — ab final fallback bhi kabhi repeat nahi hoga (jab tak
scenes > 500 na ho jayein ek hi run mein).
