# 🚀 PnakoticBot Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Telegram Bot Setup
- [ ] Created bot with @BotFather
- [ ] Got bot token (format: `123456789:ABC...`)
- [ ] Set bot username to `pnakoticbot`
- [ ] Configured `/setcommands`
- [ ] Set `/setdescription`
- [ ] Set `/setabouttext`
- [ ] Enabled privacy mode (`/setprivacy` → ENABLE)
- [ ] Enabled group support (`/setjoingroups` → ENABLE)

### 2. Code Ready
- [ ] All files created (17 files total)
- [ ] `requirements.txt` has all dependencies
- [ ] `.gitignore` configured
- [ ] `.env.example` template created
- [ ] `README.md` complete
- [ ] `Dockerfile` created
- [ ] `fly.toml` configured

### 3. Git Repository
- [x] Initialize git: `git init`
- [x] Add files: `git add .`
- [x] Commit: `git commit -m "Initial commit: PnakoticBot v1.0.0"`
- [x] Create GitHub repository
- [x] Push to GitHub: `git remote add origin <url> && git push -u origin main`

---

## ✈️ Fly.io Deployment (Recommended)

### 1. Install Fly CLI
```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. Sign Up / Login
```bash
# Sign up for new account
fly auth signup

# Or login to existing account
fly auth login
```

### 3. Launch the App
```bash
# From project directory
fly launch --no-deploy

# This will:
# - Detect Dockerfile
# - Use fly.toml configuration
# - Ask you to confirm app name (pnakoticbot)
# - Select region (choose closest to you)
# - Create app without deploying yet
```

### 4. Set Secrets (Environment Variables)
```bash
# Set bot token (REQUIRED)
fly secrets set TELEGRAM_BOT_TOKEN=8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo

# Webhook URL will be: https://pnakoticbot.fly.dev/webhook
fly secrets set WEBHOOK_URL=https://pnakoticbot.fly.dev/webhook
```

**Note**: Other environment variables (PORT, CACHE_TTL_HOURS, LOG_LEVEL) are already set in `fly.toml`

### 5. Deploy
```bash
fly deploy
```

This will:
- Build Docker image
- Deploy to Fly.io
- Start the bot
- Give you URL: `https://pnakoticbot.fly.dev`

### 6. Verify Deployment
```bash
# Check app status
fly status

# View logs
fly logs

# Check health endpoint
curl https://pnakoticbot.fly.dev/health
```

---

## 🌐 Alternative: Render Deployment

<details>
<summary>Click to expand Render.com instructions</summary>

### 1. Create Render Account
- [ ] Sign up at https://render.com
- [ ] Connect GitHub account

### 2. Create Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Select your GitHub repository
- [ ] Name: `pnakoticbot`
- [ ] Environment: Python 3
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 3. Set Environment Variables

In Render dashboard, add these:

| Variable | Value | Example |
|----------|-------|---------|
| `TELEGRAM_BOT_TOKEN` | Your bot token | `123456789:ABC...` |
| `WEBHOOK_URL` | Your app URL + /webhook | `https://pnakoticbot.onrender.com/webhook` |
| `PORT` | 10000 | `10000` |
| `CACHE_TTL_HOURS` | 24 | `24` |
| `LOG_LEVEL` | INFO | `INFO` |

**IMPORTANT**: Update `WEBHOOK_URL` with your actual Render app name!

### 4. Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (5-10 minutes)
- [ ] Check logs for success message
- [ ] Note your app URL (e.g., `https://pnakoticbot.onrender.com`)

</details>

---

## 🔗 Webhook Configuration

### Set Webhook

**For Fly.io:**
```bash
curl -X POST "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/setWebhook?url=https://pnakoticbot.fly.dev/webhook"
```

**For Render.com:**
```bash
curl -X POST "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/setWebhook?url=https://pnakoticbot.onrender.com/webhook"
```

### Verify Webhook

```bash
curl "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/getWebhookInfo"
```

Expected response:
```json
{
  "ok": true,
  "result": {
    "url": "https://pnakoticbot.fly.dev/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

- [ ] Webhook set successfully
- [ ] Webhook verified

---

## 🧪 Testing

### Private Chat Testing
- [ ] Search for `@pnakoticbot` in Telegram
- [ ] Send `/start` → Verify welcome message
- [ ] Send `/help` → Verify help message
- [ ] Send `/card Blink` → Verify card + image + FAQ
- [ ] Send `/card blinc` (typo) → Verify auto-correction
- [ ] Send `/card fire` → Verify multiple matches message
- [ ] Send `/card xyz123` → Verify "not found" message

### Group Chat Testing
- [ ] Create test group
- [ ] Add `@pnakoticbot` to group
- [ ] Send `/card Apprentice Wizard` → Verify reply-to-message
- [ ] Send `/card@pnakoticbot Blink` → Verify explicit mention works
- [ ] Send invalid command → Verify brief error message
- [ ] Test rate limiting (send 6+ requests rapidly)

### Error Testing
- [ ] Test with card that has no FAQ
- [ ] Test with very long card name
- [ ] Test rate limiting in groups

---

## 📊 Post-Deployment

### Monitoring
- [ ] Check logs for errors: `fly logs` (or Render dashboard)
- [ ] Monitor webhook status periodically
- [ ] Check cache files are being created (`data/cache/*.json`)

### Health Checks
**For Fly.io:**
- [ ] Visit `https://pnakoticbot.fly.dev/health`
  - Should return: `{"status": "ok", "bot": "PnakoticBot", "version": "1.0.0"}`
- [ ] Visit `https://pnakoticbot.fly.dev/`
  - Should return bot info

**For Render.com:**
- [ ] Visit `https://pnakoticbot.onrender.com/health`
  - Should return: `{"status": "ok", "bot": "PnakoticBot", "version": "1.0.0"}`
- [ ] Visit `https://pnakoticbot.onrender.com/`
  - Should return bot info

### Webhook Health
```bash
# Check webhook periodically
curl "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/getWebhookInfo"
```

### Fly.io Specific Commands
```bash
# View app status
fly status

# View logs (live)
fly logs

# SSH into app
fly ssh console

# Scale app (free tier: 256MB RAM)
fly scale memory 256

# View app info
fly info

# Restart app
fly apps restart pnakoticbot
```

---

## 🛠️ Troubleshooting

### Bot Not Responding
- [ ] Check logs: `fly logs` (or Render dashboard)
- [ ] Verify webhook URL is correct
- [ ] Verify bot token is correct
- [ ] Check app is running: `fly status` (or Render dashboard)
- [ ] For Fly.io: Check if app scaled to zero, wake it with: `fly scale count 1`

### Rate Limit Issues
- [ ] Wait 1 minute between requests
- [ ] Verify rate limiting logic in logs

### Cache Not Working
- [ ] Check `data/cache/` directory exists
- [ ] Verify write permissions
- [ ] Check logs for cache errors: `fly logs` (or Render)
- [ ] **Note**: Fly.io has ephemeral storage - cache resets on restarts

### Image Not Loading
- [ ] Bot should automatically fall back to text-only
- [ ] Check if CloudFront CDN is accessible

---

## 📝 Maintenance

### Regular Tasks
- [ ] Monitor logs weekly: `fly logs` (or Render)
- [ ] Check webhook status monthly
- [ ] Update dependencies quarterly
- [ ] Review cache performance

### Updates
**For Fly.io:**
1. Push changes to GitHub
2. Run `fly deploy` to deploy changes
3. Monitor logs: `fly logs`
4. Test bot functionality

**For Render.com:**
1. Push changes to GitHub
2. Render auto-deploys
3. Monitor logs for errors
4. Test bot functionality

---

## 🎉 Success Criteria

✅ **Deployment is successful when:**
- Bot responds to `/start` in private chat
- Bot responds to `/card <name>` with image + FAQ
- Bot works in group chats with reply-to-message
- Webhook status shows correct URL
- Health check returns 200 OK
- No errors in logs
- Rate limiting works correctly
- Cache is being populated

---

## 📞 Quick Commands Reference

### Fly.io Commands
```bash
# Deploy
fly deploy

# View logs
fly logs

# Check status
fly status

# Set secrets
fly secrets set KEY=value

# SSH into app
fly ssh console

# Restart app
fly apps restart pnakoticbot
```

### Telegram Commands
```bash
# Set webhook (Fly.io)
curl -X POST "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/setWebhook?url=https://pnakoticbot.fly.dev/webhook"

# Set webhook (Render)
curl -X POST "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/setWebhook?url=https://pnakoticbot.onrender.com/webhook"

# Check webhook
curl "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/getWebhookInfo"

# Delete webhook (for local testing)
curl -X POST "https://api.telegram.org/bot8572725963:AAEucyStFJbVY053nDXUakUdLPfErIb5wPo/deleteWebhook"
```

### Health Check
```bash
# Fly.io
curl "https://pnakoticbot.fly.dev/health"

# Render
curl "https://pnakoticbot.onrender.com/health"
```

---

## 🚀 You're All Set!

Once all checkboxes are ticked, PnakoticBot is fully deployed and ready to serve the Sorcery community!

**Bot Username**: `@pnakoticbot`  
**Version**: 1.0.0  
**Status**: Production Ready ✅
