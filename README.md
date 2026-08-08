# ResumeGlobal.ai

Country-specific resume generator powered by Claude AI. Supports 12 countries with correct formats, section orders, photo rules, language norms, and cultural conventions.

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key
cp .env.example .env
# Edit .env and paste your Anthropic API key from https://console.anthropic.com

# 3. Run
python app.py

# 4. Open http://localhost:5000
```

## Deploy to Railway (1-click cloud)

1. Push this folder to a GitHub repo
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add environment variable: `ANTHROPIC_API_KEY=sk-ant-...`
4. Done — live in 2 minutes

## Deploy to Render

1. Push to GitHub
2. New Web Service → connect repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python app.py`
5. Add `ANTHROPIC_API_KEY` in environment variables

## Supported Countries

| Country | Format | Photo | Notes |
|---------|--------|-------|-------|
| 🇺🇸 USA | American Resume | ❌ | ATS-optimized, no personal details |
| 🇬🇧 UK | British CV | ❌ | 2 pages, personal profile |
| 🇩🇪 Germany | Lebenslauf | ✅ Required | DOB, marital status, signature |
| 🇫🇷 France | CV Français | ✅ Optional | Hobbies section important |
| 🇯🇵 Japan | Rirekisho | ✅ Required | Chronological oldest-first |
| 🇦🇺 Australia | Australian Resume | ❌ | Referees included |
| 🇨🇦 Canada | Canadian Resume | ❌ | Similar to US, bilingual option |
| 🇦🇪 UAE | Gulf CV | ✅ Expected | Nationality, visa status |
| 🇮🇳 India | Indian CV | ✅ Optional | Declaration at end |
| 🇸🇬 Singapore | Singapore CV | ✅ Optional | Multi-language focus |
| 🇳🇱 Netherlands | Dutch CV | ✅ Optional | Very concise, direct |
| 🇧🇷 Brazil | Currículo | ✅ Expected | Personal tone, Portuguese |

## Monetization Ideas

- **Freemium**: 1 free resume, $4.99/resume after
- **Subscription**: $12/mo unlimited
- **Credits**: 5-pack for $15
- **B2B**: Bulk pricing for immigration consultants / recruiters

## Tech Stack

- **Backend**: Python + Flask
- **AI**: Anthropic Claude (claude-opus-4-5)
- **Frontend**: Vanilla JS + Tailwind CSS CDN
- **PDF**: Browser print-to-PDF (zero dependencies)
