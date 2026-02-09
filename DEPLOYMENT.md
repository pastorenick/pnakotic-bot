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
- [ ] All files created (14 files total)
- [ ] `requirements.txt` has all dependencies
- [ ] `.gitignore` configured
- [ ] `.env.example` template created
- [ ] `README.md` complete

### 3. Git Repository
- [ ] Initialize git: `git init`
- [ ] Add files: `git add .`
- [ ] Commit: `git commit -m "Initial commit: PnakoticBot v1.0.0"`
- [ ] Create GitHub repository
- [ ] Push to GitHub: `git remote add origin <url> && git push -u origin main`

---

## 🌐 Render Deployment

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

---

## 🔗 Webhook Configuration

### Set Webhook

Replace `<TOKEN>` and `<WEBHOOK_URL>`:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WEBHOOK_URL>/webhook"
```

Example:
```bash
curl -X POST "https://api.telegram.org/bot123456789:ABC.../setWebhook?url=https://pnakoticbot.onrender.com/webhook"
```

### Verify Webhook

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

Expected response:
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
- [ ] Check Render logs for errors
- [ ] Monitor webhook status periodically
- [ ] Check cache files are being created (`data/cache/*.json`)

### Health Checks
- [ ] Visit `https://pnakoticbot.onrender.com/health`
  - Should return: `{"status": "ok", "bot": "PnakoticBot", "version": "1.0.0"}`
- [ ] Visit `https://pnakoticbot.onrender.com/`
  - Should return bot info

### Webhook Health
```bash
# Check webhook periodically
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

## 🛠️ Troubleshooting

### Bot Not Responding
- [ ] Check Render logs for errors
- [ ] Verify webhook URL is correct
- [ ] Verify bot token is correct
- [ ] Check Render app is running (not sleeping)

### Rate Limit Issues
- [ ] Wait 1 minute between requests
- [ ] Verify rate limiting logic in logs

### Cache Not Working
- [ ] Check `data/cache/` directory exists
- [ ] Verify write permissions
- [ ] Check Render logs for cache errors

### Image Not Loading
- [ ] Bot should automatically fall back to text-only
- [ ] Check if CloudFront CDN is accessible

---

## 📝 Maintenance

### Regular Tasks
- [ ] Monitor Render logs weekly
- [ ] Check webhook status monthly
- [ ] Update dependencies quarterly
- [ ] Review cache performance

### Updates
When updating code:
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
- Render health check returns 200 OK
- No errors in Render logs
- Rate limiting works correctly
- Cache is being populated

---

## 📞 Quick Commands Reference

```bash
# Set webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL>/webhook"

# Check webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Delete webhook (for local testing)
curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"

# Check health
curl "https://pnakoticbot.onrender.com/health"
```

---

## 🚀 You're All Set!

Once all checkboxes are ticked, PnakoticBot is fully deployed and ready to serve the Sorcery community!

**Bot Username**: `@pnakoticbot`  
**Version**: 1.0.0  
**Status**: Production Ready ✅
