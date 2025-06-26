#!/usr/bin/env python3
"""
Simple Telegram Bot Test Script
This script helps you test your Telegram bot integration
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bot_token(token):
    """Test if the bot token is valid."""
    print(f"🔍 Testing bot token: {token[:10]}...")
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Bot token is valid!")
                print(f"   Bot name: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   Bot ID: {bot_info.get('id')}")
                return True
            else:
                print(f"❌ Bot token is invalid: {data.get('description')}")
                return False
        else:
            print(f"❌ Failed to validate bot token: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing bot token: {str(e)}")
        return False

def get_updates(token):
    """Get recent updates from the bot."""
    print(f"📥 Getting updates for bot...")
    
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                print(f"✅ Found {len(updates)} updates")
                
                if updates:
                    print("\n📋 Recent messages:")
                    for update in updates[-3:]:  # Show last 3 updates
                        if 'message' in update:
                            msg = update['message']
                            chat_id = msg.get('chat', {}).get('id')
                            text = msg.get('text', '')
                            from_user = msg.get('from', {})
                            print(f"   Chat ID: {chat_id}")
                            print(f"   From: {from_user.get('first_name', 'Unknown')}")
                            print(f"   Message: {text[:50]}...")
                            print()
                else:
                    print("   No messages found. Send a message to your bot first!")
                
                return updates
            else:
                print(f"❌ Failed to get updates: {data.get('description')}")
                return []
        else:
            print(f"❌ Failed to get updates: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting updates: {str(e)}")
        return []

def send_test_message(token, chat_id, message):
    """Send a test message to the bot."""
    print(f"📤 Sending test message to chat {chat_id}...")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Message sent successfully!")
                return True
            else:
                print(f"❌ Failed to send message: {result.get('description')}")
                return False
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        return False

def test_webhook(token, webhook_url):
    """Test webhook setup."""
    print(f"🔗 Testing webhook: {webhook_url}")
    
    # Set webhook
    set_url = f"https://api.telegram.org/bot{token}/setWebhook"
    set_data = {"url": webhook_url}
    
    try:
        response = requests.post(set_url, json=set_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Webhook set successfully!")
                
                # Get webhook info
                info_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
                info_response = requests.get(info_url)
                if info_response.status_code == 200:
                    info_data = info_response.json()
                    if info_data.get('ok'):
                        webhook_info = info_data['result']
                        print(f"   Webhook URL: {webhook_info.get('url', 'Not set')}")
                        print(f"   Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
                        print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
                        print(f"   Last error: {webhook_info.get('last_error_message', 'None')}")
                return True
            else:
                print(f"❌ Failed to set webhook: {result.get('description')}")
                return False
        else:
            print(f"❌ Failed to set webhook: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error setting webhook: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🤖 Telegram Bot Test Script")
    print("=" * 50)
    
    # Get bot token
    token = input("Enter your Telegram bot token: ").strip()
    if not token:
        print("❌ No token provided")
        return
    
    # Test bot token
    if not test_bot_token(token):
        return
    
    print("\n" + "=" * 50)
    
    # Get updates
    updates = get_updates(token)
    
    print("\n" + "=" * 50)
    
    # Ask for chat ID
    if updates:
        latest_update = updates[-1]
        if 'message' in latest_update:
            default_chat_id = latest_update['message']['chat']['id']
            print(f"💡 Found recent chat ID: {default_chat_id}")
        else:
            default_chat_id = ""
    else:
        default_chat_id = ""
    
    chat_id = input(f"Enter chat ID to test with (or press Enter for {default_chat_id}): ").strip()
    if not chat_id and default_chat_id:
        chat_id = default_chat_id
    elif not chat_id:
        print("❌ No chat ID provided")
        return
    
    # Send test message
    test_message = "Hello! This is a test message from the BusinessAI bot. 🍰"
    if send_test_message(token, chat_id, test_message):
        print(f"\n✅ Test completed successfully!")
        print(f"   Check your Telegram bot for the test message")
        print(f"   Chat ID: {chat_id}")
        print(f"   Use this chat ID in your dashboard for testing")
    else:
        print(f"\n❌ Test failed. Make sure:")
        print(f"   1. You've started a conversation with your bot")
        print(f"   2. You've sent /start to your bot")
        print(f"   3. The chat ID is correct")
    
    print("\n" + "=" * 50)
    
    # Test webhook (optional)
    webhook_test = input("Do you want to test webhook setup? (y/n): ").strip().lower()
    if webhook_test == 'y':
        webhook_url = input("Enter webhook URL (e.g., https://your-domain.com/api/telegram/webhook): ").strip()
        if webhook_url:
            test_webhook(token, webhook_url)

if __name__ == "__main__":
    main() 