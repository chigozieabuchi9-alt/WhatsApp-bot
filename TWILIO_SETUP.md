# Twilio WhatsApp Setup Guide

This guide will walk you through setting up Twilio WhatsApp integration for your bot.

## Table of Contents

1. [Create Twilio Account](#1-create-twilio-account)
2. [Get WhatsApp Sandbox](#2-get-whatsapp-sandbox)
3. [Configure Webhook](#3-configure-webhook)
4. [Test the Integration](#4-test-the-integration)
5. [Go Live (Optional)](#5-go-live-optional)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Create Twilio Account

1. Go to [Twilio Console](https://www.twilio.com/try-twilio)
2. Sign up for a free account
3. Verify your email and phone number
4. You'll receive:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (keep this secret!)

### Get Your Credentials

1. Log into [Twilio Console](https://console.twilio.com/)
2. On the dashboard, you'll see:
   ```
   ACCOUNT SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   AUTH TOKEN:  [Click to reveal]
   ```
3. Copy these values to your `.env` file:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   ```

---

## 2. Get WhatsApp Sandbox

### Using the Sandbox (Free)

1. In Twilio Console, go to **Messaging** → **Try it out** → **Send a WhatsApp message**
2. You'll see a QR code and a phone number
3. Save this phone number - it's your bot's WhatsApp number!
4. Add it to your `.env`:
   ```env
   TWILIO_PHONE_NUMBER=+14155238886  # Example sandbox number
   ```

### Join the Sandbox

1. Send a WhatsApp message to the sandbox number with the join code:
   ```
   join <your-join-code>
   ```
2. You'll receive a confirmation message
3. Your phone is now connected to the sandbox

---

## 3. Configure Webhook

### For Local Development (using ngrok)

1. Install ngrok:
   ```bash
   # macOS
   brew install ngrok

   # Linux
   wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
   tar xvzf ngrok-v3-stable-linux-amd64.tgz
   sudo mv ngrok /usr/local/bin/
   ```

2. Sign up at [ngrok.com](https://ngrok.com) and get your authtoken

3. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

4. Start your bot locally:
   ```bash
   make up
   ```

5. In another terminal, expose your local server:
   ```bash
   ngrok http 8000
   ```

6. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

7. Update your `.env`:
   ```env
   TWILIO_WEBHOOK_URL=https://abc123.ngrok.io/webhook/whatsapp
   ```

### Configure in Twilio Console

1. Go to **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Click on **Sandbox Settings**
3. Under "When a message comes in":
   - URL: `https://your-ngrok-url.ngrok.io/webhook/whatsapp`
   - Method: `HTTP POST`
4. Click **Save**

### For Production

1. Deploy your bot to a server with a public domain
2. Update `.env` with your production URL:
   ```env
   TWILIO_WEBHOOK_URL=https://your-domain.com/webhook/whatsapp
   ```
3. Configure the webhook in Twilio Console with your production URL

---

## 4. Test the Integration

### Send a Test Message

1. Open WhatsApp on your phone
2. Send a message to your bot's number:
   ```
   !help
   ```
3. You should receive a response with available commands!

### Common Test Commands

```
!help              - Show all commands
!ping              - Test bot response
!weather London    - Get weather
!joke              - Get a joke
!wordle            - Play Wordle
```

### Check Logs

```bash
# View application logs
make logs-app

# Or using docker-compose directly
docker-compose logs -f app
```

---

## 5. Go Live (Optional)

To use your own WhatsApp Business number instead of the sandbox:

### Requirements

- Facebook Business Manager account
- Verified business
- WhatsApp Business API access

### Steps

1. Go to **Messaging** → **Senders** → **WhatsApp Senders**
2. Click **Add WhatsApp Sender**
3. Follow the setup wizard:
   - Connect Facebook Business account
   - Verify your business
   - Add phone number
   - Complete registration

4. Once approved, update your `.env`:
   ```env
   TWILIO_PHONE_NUMBER=+1234567890  # Your verified number
   ```

---

## 6. Troubleshooting

### Bot Not Responding

**Check webhook URL:**
```bash
curl -X POST https://your-url/webhook/whatsapp \
  -d "From=whatsapp:+1234567890" \
  -d "Body=!help"
```

**Check Twilio logs:**
1. Go to **Monitor** → **Logs** → **Messaging**
2. Look for failed requests

**Verify environment variables:**
```bash
docker-compose exec app env | grep TWILIO
```

### Webhook Validation Failed

In production, the bot validates Twilio signatures. For testing:

```env
APP_ENV=development  # Disables signature validation
```

### Rate Limiting

If you see "Rate limit exceeded":
- Check `RATE_LIMIT_REQUESTS_PER_MINUTE` in `.env`
- Default is 30 requests per minute

### Database Connection Errors

```bash
# Check database status
docker-compose ps db

# View database logs
docker-compose logs db

# Test connection
docker-compose exec db psql -U postgres -d whatsapp_bot -c "SELECT 1;"
```

### Redis Connection Errors

```bash
# Check Redis status
docker-compose ps redis

# Test Redis
docker-compose exec redis redis-cli ping
```

### Invalid Signature Errors

1. Ensure `TWILIO_AUTH_TOKEN` is correct
2. Check that webhook URL matches exactly
3. For ngrok, restart if URL changed

---

## Webhook Security

### Signature Validation

In production, always validate webhook signatures:

```python
# This is handled automatically in app/main.py
from twilio.request_validator import RequestValidator

validator = RequestValidator(auth_token)
is_valid = validator.validate(url, params, signature)
```

### HTTPS Only

Always use HTTPS for webhooks in production:
- Use a reverse proxy (nginx, traefik)
- Or use a service like ngrok for development

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID | `ACxxxxxxxx...` |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | `your_token...` |
| `TWILIO_PHONE_NUMBER` | WhatsApp sender number | `+14155238886` |
| `TWILIO_WEBHOOK_URL` | Public URL for webhooks | `https://.../webhook/whatsapp` |

---

## Next Steps

- [Read the main README](README.md)
- [Explore available commands](README.md#command-categories)
- [Set up monitoring with Flower](README.md#monitoring)

## Support

- [Twilio Documentation](https://www.twilio.com/docs/whatsapp)
- [Twilio Support](https://support.twilio.com/)
- Create an issue in this repository
