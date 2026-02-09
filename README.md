# 🤖 PnakoticBot

A Telegram bot that fetches **Sorcery: Contested Realm** card images and FAQs from [curiosa.io](https://curiosa.io).

Works in both **private chats** and **group chats** with intelligent fuzzy search, rate limiting, and automatic caching.

---

## ✨ Features

- 🔍 **Smart Search** - Exact match → Partial match → Fuzzy match (handles typos!)
- 🖼️ **Card Images** - High-quality images from CloudFront CDN
- ❓ **Complete FAQs** - All FAQ entries for each card (no truncation)
- 💬 **Group Support** - Works in private chats and group chats
- ⏱️ **Rate Limiting** - 10 requests/min (users), 5 requests/min (groups)
- 📦 **Smart Caching** - 24-hour cache to reduce API calls (lazy load)
- 🎯 **Brief Errors** - Short error messages in groups to avoid spam

---

## 📋 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message and usage guide | `/start` |
| `/card <name>` | Fetch card info (image + FAQ) | `/card Blink` |
| `/help` | Show available commands | `/help` |

### Usage Examples

```
/card Blink                  → Fetch "Blink" card
/card Apprentice Wizard      → Fetch "Apprentice Wizard"
/card blinc                  → Auto-corrects to "Blink" (fuzzy)
/card fire                   → Shows multiple matches
/card@pnakoticbot Blink      → Explicit mention (for multi-bot groups)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram account
- Render account (free tier works!)

---

## 📱 Step 1: Create Telegram Bot

### 1.1 Talk to @BotFather

Open Telegram and search for `@BotFather`, then follow these steps:

```
1. Send: /newbot
2. Bot name: PnakoticBot
3. Bot username: pnakoticbot
   (must be lowercase and end with 'bot')
4. Copy the token (looks like: 123456789:ABC...)
```

### 1.2 Configure Bot Settings

Send these commands to @BotFather:

#### Set Commands
```
/setcommands

Then paste:
start - Welcome message and usage guide
card - Fetch card info (usage: /card <name>)
help - Show available commands
```

#### Set Description
```
/setdescription

Then paste:
Fetch Sorcery: Contested Realm card images and FAQs from curiosa.io
```

#### Set About Text
```
/setabouttext

Then paste:
PnakoticBot - Your Sorcery card companion
```

#### Enable Privacy Mode (Recommended)
```
/setprivacy

Choose: ENABLE

This allows the bot to only see commands in groups (more private)
```

#### Enable Group Support
```
/setjoingroups

Choose: ENABLE

This allows the bot to be added to group chats
```

---

## 💻 Step 2: Local Development (Optional)

### 2.1 Clone and Setup

```bash
# Clone repository
git clone <your-repo-url>
cd OwlBot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2.2 Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your bot token
# TELEGRAM_BOT_TOKEN=<paste-your-token-here>
```

### 2.3 Run Locally (Polling Mode)

For local testing, you can modify `main.py` to use polling mode instead of webhooks:

```python
# In main.py, replace the webhook setup with:
if __name__ == '__main__':
    application = setup_bot()
    application.run_polling()
```

Then run:
```bash
python main.py
```

Test the bot by messaging it on Telegram!

---

## 🌐 Step 3: Deploy to Render

### 3.1 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up (free tier available)
3. Connect your GitHub account

### 3.2 Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `pnakoticbot`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 3.3 Set Environment Variables

In Render dashboard, add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `TELEGRAM_BOT_TOKEN` | `123456789:ABC...` | Your bot token from @BotFather |
| `WEBHOOK_URL` | `https://pnakoticbot.onrender.com/webhook` | Your Render app URL + /webhook |
| `PORT` | `10000` | Render default port |
| `CACHE_TTL_HOURS` | `24` | Cache duration |
| `LOG_LEVEL` | `INFO` | Logging level |

**Important**: Replace `pnakoticbot` in the `WEBHOOK_URL` with your actual Render app name!

### 3.4 Deploy

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for deployment
3. Check logs for "PnakoticBot is ready to receive messages!"

Your bot URL will be: `https://pnakoticbot.onrender.com`

---

## 🔗 Step 4: Set Telegram Webhook

After deployment, set the webhook so Telegram knows where to send messages:

```bash
# Replace <TOKEN> with your bot token
# Replace <WEBHOOK_URL> with your Render app URL

curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WEBHOOK_URL>/webhook"

# Example:
curl -X POST "https://api.telegram.org/bot123456789:ABC.../setWebhook?url=https://pnakoticbot.onrender.com/webhook"
```

### Verify Webhook

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

You should see:
```json
{
  "ok": true,
  "result": {
    "url": "https://pnakoticbot.onrender.com/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 🧪 Step 5: Test the Bot

### Private Chat Testing

1. Search for `@pnakoticbot` in Telegram
2. Start a conversation
3. Send: `/start`
4. Send: `/card Blink`
5. Verify you receive card image and FAQ

### Group Chat Testing

1. Create a test group or use existing
2. Add `@pnakoticbot` to the group
   - Click group name → Add Members → Search for `@pnakoticbot`
3. Send: `/card Apprentice Wizard`
4. Verify bot replies to your message with card info

---

## 🏗️ Project Structure

```
OwlBot/
├── bot/
│   ├── __init__.py              # Package initialization
│   ├── cache.py                 # JSON file caching (lazy load)
│   ├── card_fetcher.py          # Sorcery API client + fuzzy search
│   ├── faq_scraper.py           # Curiosa.io FAQ scraper
│   ├── telegram_bot.py          # Bot command handlers
│   └── utils.py                 # Rate limiting + message formatting
│
├── data/
│   └── cache/                   # Auto-generated cache files
│       ├── cards.json           # Cached card data (24h TTL)
│       └── faqs.json            # Cached FAQ data (24h TTL)
│
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules
├── main.py                      # Flask + Bot entry point
├── Procfile                     # Render deployment command
├── render.yaml                  # Render infrastructure config
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🔧 How It Works

### Architecture

```
User sends /card Blink
       ↓
Telegram → Render Webhook → Flask → Bot Handler
       ↓
Check Cache (cards.json, faqs.json)
       ↓
If cache valid (< 24h): Load from disk
If cache stale: Fetch from API + Scrape FAQs
       ↓
Search card (exact → partial → fuzzy)
       ↓
Format message + Get image URL
       ↓
Send to user (with image or text-only if image fails)
```

### Data Sources

1. **Sorcery API** - `https://api.sorcerytcg.com/api/cards` (1,104 cards)
2. **CloudFront CDN** - `https://d27a44hjr9gen3.cloudfront.net/cards/{slug}.png`
3. **Curiosa.io FAQs** - `https://curiosa.io/faqs` (web scraping)

### Caching Strategy

- **Lazy Load**: Cache is populated on first request, not on startup
- **TTL**: 24 hours (configurable via `CACHE_TTL_HOURS`)
- **Storage**: JSON files in `data/cache/`
- **Refresh**: Automatic when cache expires

### Rate Limiting

- **Private chats**: 10 requests/minute per user
- **Group chats**: 5 requests/minute per group
- **Storage**: In-memory (resets on restart)

---

## 🛠️ Troubleshooting

### Bot not responding

**Check webhook status:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

**Common issues:**
- Webhook URL incorrect → Update in Render env vars
- Bot token wrong → Verify in .env or Render dashboard
- Render app sleeping (free tier) → Send a request to wake it up

### "Rate limit exceeded" error

Wait 1 minute before sending more requests.

### Card not found

- Check spelling
- Try partial name (e.g., "apprentice" instead of full name)
- Some cards may not be in the API yet

### Image not loading

Bot automatically falls back to text-only mode if image fails. This is expected behavior.

### Cache not updating

Delete cache files manually:
```bash
rm data/cache/*.json
```

The bot will re-fetch on next request.

---

## 📊 Bot Behavior

### Search Examples

| Input | Result |
|-------|--------|
| `/card Blink` | ✅ Exact match - shows card |
| `/card blink` | ✅ Case-insensitive match |
| `/card apprentice` | ✅ Partial match - shows "Apprentice Wizard" |
| `/card blinc` | ✅ Fuzzy match - auto-corrects to "Blink" |
| `/card fire` | 🔍 Multiple matches - asks to be specific |
| `/card xyz123` | ❌ Not found |

### Group vs Private Chat

| Feature | Private Chat | Group Chat |
|---------|-------------|------------|
| Error messages | Detailed | Brief ("❌ Not found") |
| Response style | Direct message | Reply to user's message |
| Rate limit | 10/min per user | 5/min per group |
| Multiple matches | Shows first 5 names | Just count ("🔍 50 matches") |

---

## 🔐 Privacy & Security

- **Privacy mode enabled**: Bot only sees commands in groups (not all messages)
- **No data storage**: No user data is stored permanently
- **Rate limiting**: Prevents spam and abuse
- **Open source**: All code is transparent and auditable

---

## 📜 License

This project is open source and available under the MIT License.

---

## 🙏 Credits

- **Data Source**: [Curiosa.io](https://curiosa.io) - Sorcery card database
- **Game**: [Sorcery: Contested Realm](https://sorcerytcg.com) by Erik's Curiosa
- **Bot Framework**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- **Hosting**: [Render.com](https://render.com)

---

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review Render logs for errors
3. Verify environment variables are set correctly
4. Make sure bot token and webhook URL are correct

---

## 🚀 Future Enhancements

Possible features to add:

- [ ] Inline queries (`@pnakoticbot Blink` in any chat)
- [ ] Random card command (`/random`)
- [ ] Search by type/element (`/search type:minion`)
- [ ] Card comparison (`/compare Blink vs Teleport`)
- [ ] Favorite cards system
- [ ] Multi-language support
- [ ] Advanced filtering

---

## ⚡ Quick Reference

### Essential Commands

```bash
# Local testing
python main.py

# Set webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL>/webhook"

# Check webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Delete webhook (for local testing)
curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=123456789:ABC...        # Required
WEBHOOK_URL=https://yourapp.onrender.com/webhook  # Required
PORT=10000                                  # Optional (default: 10000)
CACHE_TTL_HOURS=24                         # Optional (default: 24)
LOG_LEVEL=INFO                             # Optional (default: INFO)
```

---

## 🎯 Bot Username

`@pnakoticbot`

Use `/card@pnakoticbot <name>` in groups with multiple bots to ensure this bot responds.

---

**Made with ❤️ for the Sorcery: Contested Realm community**
