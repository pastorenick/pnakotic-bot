# ⚡ Quick Start Guide - PnakoticBot

## 🚀 5-Minute Deployment

### Step 1: Create Bot (2 minutes)
1. Open Telegram → Search `@BotFather`
2. Send `/newbot`
3. Name: `PnakoticBot`
4. Username: `pnakoticbot`
5. **Copy the token** (you'll need it!)

### Step 2: Configure Bot (1 minute)
Send to @BotFather:
```
/setcommands
start - Welcome message
card - Fetch card info
help - Show commands

/setprivacy
ENABLE

/setjoingroups
ENABLE
```

### Step 3: Deploy to Render (2 minutes)
1. Go to [render.com](https://render.com) → Sign up
2. Click "New +" → "Web Service"
3. Connect this GitHub repo
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`: (paste your token)
   - `WEBHOOK_URL`: `https://pnakoticbot.onrender.com/webhook`
5. Click "Create Web Service"

### Step 4: Set Webhook (30 seconds)
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://pnakoticbot.onrender.com/webhook"
```

### Step 5: Test! (30 seconds)
1. Search `@pnakoticbot` in Telegram
2. Send `/card Blink`
3. Enjoy! 🎉

---

## 📝 Essential Environment Variables

| Variable | Example |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | `123456789:ABC...` |
| `WEBHOOK_URL` | `https://pnakoticbot.onrender.com/webhook` |

---

## ✅ Success Checklist

- [ ] Bot responds to `/start`
- [ ] Bot shows card image for `/card Blink`
- [ ] Webhook status shows correct URL

---

## 🆘 Troubleshooting

**Bot not responding?**
```bash
# Check webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

**Still stuck?**  
See full guide in [README.md](README.md) or [DEPLOYMENT.md](DEPLOYMENT.md)

---

**That's it! Your bot is live!** 🤖✨
