# Telegram Bot Troubleshooting Guide

## 🚨 Common Issues and Solutions

### 1. Bot Not Responding to Messages

**Problem**: You've set up the bot but it's not responding when you send messages.

**Solutions**:

#### A. Check Bot Token
1. Verify your bot token is correct
2. Test the token using the test script:
   ```bash
   python test_telegram.py
   ```

#### B. Start Conversation with Bot
1. Find your bot on Telegram (search for `@your_bot_name`)
2. Click "Start" or send `/start` message
3. This is required before the bot can send you messages

#### C. Check Chat ID
1. Get your chat ID by visiting:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
2. Look for `"chat":{"id":123456789}` in the response
3. Use this ID in the dashboard test

#### D. Test with Dashboard
1. Go to Analytics → Integration Settings
2. Enter your bot token and enable it
3. Click "Test Bot" and enter your chat ID
4. Check if the test message is sent successfully

### 2. Webhook Issues

**Problem**: Bot works with test messages but not with real-time messages.

**Solutions**:

#### A. For Development (Local Testing)
1. **Use Test Messages**: Use the "Test Bot" button in the dashboard
2. **Use Polling**: Click "Poll Updates" to manually check for new messages
3. **Use ngrok**: For real webhook testing:
   ```bash
   # Install ngrok
   npm install -g ngrok
   
   # Start your Flask server
   python app.py
   
   # In another terminal, expose your server
   ngrok http 5000
   
   # Set the webhook URL to your ngrok URL
   # e.g., https://abc123.ngrok.io/api/telegram/webhook
   ```

#### B. For Production
1. Set the `WEBHOOK_DOMAIN` environment variable:
   ```bash
   export WEBHOOK_DOMAIN=your-domain.com
   ```
2. Make sure your domain has HTTPS
3. The webhook URL will be: `https://your-domain.com/api/telegram/webhook`

### 3. Bot Token Issues

**Problem**: "Invalid bot token" or "Bot not found" errors.

**Solutions**:

1. **Get a new token**:
   - Message @BotFather on Telegram
   - Send `/newbot` or `/mybots`
   - Follow the instructions to create a new bot

2. **Check token format**:
   - Should look like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Contains numbers, colon, and letters

3. **Test token validity**:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

### 4. No Data in ChromaDB

**Problem**: Bot responds but says "I'm having trouble finding specific information".

**Solutions**:

1. **Upload Data First**:
   - Go to "Upload Data" section
   - Upload your business data (products, services, etc.)
   - Click "Save to Database"

2. **Store in ChromaDB**:
   - Go to "Data Testing" section
   - Click "Store in Database" button
   - This makes data available for the AI assistant

3. **Check Data Format**:
   - Make sure your data contains product information
   - Include names, descriptions, prices, etc.

### 5. AI Model Issues

**Problem**: Bot responds with "AI model is not properly configured".

**Solutions**:

1. **Set GEMINI_API_KEY**:
   ```bash
   export GEMINI_API_KEY=your_gemini_api_key
   ```
   Or add to your `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

2. **Get Gemini API Key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy and use it in your environment

## 🔧 Testing Steps

### Step 1: Basic Bot Test
```bash
python test_telegram.py
```

### Step 2: Dashboard Test
1. Open dashboard
2. Go to Analytics → Integration Settings
3. Enter bot token and enable
4. Click "Test Bot"
5. Enter your chat ID
6. Check if message is sent

### Step 3: Data Test
1. Upload some test data
2. Store it in ChromaDB
3. Test the bot with questions about your data

### Step 4: Webhook Test (Optional)
1. Set up ngrok
2. Configure webhook
3. Send real messages to bot

## 📋 Debug Checklist

- [ ] Bot token is valid and working
- [ ] You've started a conversation with the bot (`/start`)
- [ ] You have the correct chat ID
- [ ] Bot is enabled in dashboard settings
- [ ] Data is uploaded and stored in ChromaDB
- [ ] GEMINI_API_KEY is set
- [ ] Flask server is running
- [ ] No firewall blocking requests

## 🆘 Getting Help

If you're still having issues:

1. **Check the logs**: Look at the Flask server console for error messages
2. **Test step by step**: Use the test script to isolate the issue
3. **Check network**: Make sure your server can reach Telegram's API
4. **Verify data**: Ensure you have business data loaded

## 📞 Common Error Messages

- **"Bot not found"**: Check your bot token
- **"Chat not found"**: Start a conversation with your bot first
- **"No data found"**: Upload and store data in ChromaDB
- **"AI model not configured"**: Set GEMINI_API_KEY
- **"Webhook failed"**: Use ngrok or set up HTTPS domain

## 🎯 Quick Fix Commands

```bash
# Test bot token
curl https://api.telegram.org/bot<TOKEN>/getMe

# Get updates (to find chat ID)
curl https://api.telegram.org/bot<TOKEN>/getUpdates

# Send test message
curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"<CHAT_ID>","text":"Test message"}'

# Set webhook
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/telegram/webhook"}'
``` 