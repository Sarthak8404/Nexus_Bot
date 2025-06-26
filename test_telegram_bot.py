#!/usr/bin/env python3
"""
Telegram Bot Test Script
This script helps test and debug Telegram bot integration.
"""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "test_user_123"

def test_bot_token(token):
    """Test if the bot token is valid."""
    print("🔍 Testing bot token...")
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_name = bot_info['result']['first_name']
                bot_username = bot_info['result']['username']
                print(f"✅ Bot token is valid: {bot_name} (@{bot_username})")
                return True
            else:
                print(f"❌ Invalid bot token: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ Failed to validate bot token: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error validating bot token: {str(e)}")
        return False

def test_webhook_setup(token):
    """Test webhook setup."""
    print("\n🔗 Testing webhook setup...")
    
    try:
        # Check current webhook info
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info.get('ok'):
                current_url = webhook_info['result'].get('url', '')
                if current_url:
                    print(f"📡 Current webhook URL: {current_url}")
                    return current_url
                else:
                    print("⚠️  No webhook is currently set")
                    return None
            else:
                print(f"❌ Failed to get webhook info: {webhook_info.get('description')}")
                return None
        else:
            print(f"❌ Failed to get webhook info: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking webhook: {str(e)}")
        return None

def test_backend_webhook_setup(token, user_id):
    """Test backend webhook setup."""
    print(f"\n🔄 Testing backend webhook setup...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/telegram/setup",
            json={"user_id": user_id, "token": token},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Backend webhook setup successful")
                print(f"   Webhook URL: {result.get('webhook_url')}")
                return True
            else:
                print(f"❌ Backend webhook setup failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Backend webhook setup failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error setting up backend webhook: {str(e)}")
        return False

def test_backend_connectivity():
    """Test if backend is accessible."""
    print("🌐 Testing backend connectivity...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is accessible")
            return True
        else:
            print(f"❌ Backend is not responding properly (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {str(e)}")
        return False

def test_chat_functionality(user_id):
    """Test chat functionality."""
    print(f"\n💬 Testing chat functionality...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={"message": "Hello, test message", "user_id": user_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('response'):
                print("✅ Chat functionality working")
                print(f"   Response: {result['response'][:100]}...")
                return True
            elif result.get('error'):
                print(f"⚠️  Chat error: {result['error']}")
                return False
            else:
                print("⚠️  No response from chat")
                return False
        else:
            print(f"❌ Chat test failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing chat: {str(e)}")
        return False

def send_test_message(token, chat_id, message="Hello from test script!"):
    """Send a test message to the bot."""
    print(f"\n📤 Sending test message to chat {chat_id}...")
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Test message sent successfully")
                return True
            else:
                print(f"❌ Failed to send test message: {result.get('description')}")
                return False
        else:
            print(f"❌ Failed to send test message: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending test message: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🤖 Telegram Bot Integration Test")
    print("=" * 50)
    
    # Check if ngrok is needed
    print("⚠️  IMPORTANT: Telegram requires HTTPS URLs for webhooks.")
    print("   For local development, you need to use ngrok.")
    print("   Run: ngrok http 5000")
    print("   Then set: export WEBHOOK_DOMAIN='your-ngrok-url.ngrok.io'")
    print()
    
    # Get bot token
    token = input("Enter your Telegram bot token: ").strip()
    if not token:
        print("❌ No token provided. Exiting.")
        return
    
    # Test backend connectivity first
    if not test_backend_connectivity():
        print("\n❌ Backend is not accessible. Please start the Flask server first.")
        return
    
    # Test bot token
    if not test_bot_token(token):
        print("\n❌ Bot token is invalid. Please check your token.")
        return
    
    # Test webhook setup
    current_webhook = test_webhook_setup(token)
    
    # Test backend webhook setup
    if test_backend_webhook_setup(token, TEST_USER_ID):
        # Check webhook again
        new_webhook = test_webhook_setup(token)
        if new_webhook and new_webhook != current_webhook:
            print("✅ Webhook was updated successfully")
        else:
            print("⚠️  Webhook may not have been updated")
    else:
        print("\n❌ Webhook setup failed. Make sure you:")
        print("   1. Have ngrok running: ngrok http 5000")
        print("   2. Set WEBHOOK_DOMAIN environment variable")
        print("   3. Restarted the Flask server")
    
    # Test chat functionality
    test_chat_functionality(TEST_USER_ID)
    
    # Ask for chat ID to send test message
    print(f"\n📝 To test the bot:")
    print(f"1. Send a message to your bot")
    print(f"2. Check the backend logs for webhook messages")
    print(f"3. The bot should respond using your business data")
    
    chat_id = input("\nEnter a chat ID to send test message (or press Enter to skip): ").strip()
    if chat_id:
        send_test_message(token, chat_id)
    
    print(f"\n🎉 Test completed!")
    print(f"\n📋 Next steps:")
    print(f"1. Make sure you have uploaded and stored data in the dashboard")
    print(f"2. Send a message to your bot")
    print(f"3. Check the backend logs for any issues")
    print(f"4. If using localhost, use ngrok for webhook testing")
    print(f"\n🔧 Troubleshooting:")
    print(f"   - Run: ngrok http 5000")
    print(f"   - Set: export WEBHOOK_DOMAIN='your-ngrok-url.ngrok.io'")
    print(f"   - Restart Flask server")
    print(f"   - Try webhook setup again")

if __name__ == "__main__":
    main() 