#!/usr/bin/env python3
"""
Debug Telegram Bot Issues
This script helps identify what's wrong with your Telegram bot setup
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_backend():
    """Test if the backend is running and accessible."""
    print("🔍 Testing backend connectivity...")
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is running")
            print(f"   API Key configured: {data.get('api_key_configured')}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {str(e)}")
        print("   Make sure you're running: python app.py")
        return False

def test_telegram_token(token):
    """Test if the Telegram bot token is valid."""
    print(f"\n🔍 Testing Telegram bot token...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print("✅ Bot token is valid")
                print(f"   Bot name: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                return True
            else:
                print(f"❌ Invalid bot token: {data.get('description')}")
                return False
        else:
            print(f"❌ Failed to validate token: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing token: {str(e)}")
        return False

def test_chat_id(token, chat_id):
    """Test if the chat ID is valid by sending a test message."""
    print(f"\n🔍 Testing chat ID {chat_id}...")
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🔧 Test message from debug script"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ Chat ID is valid - test message sent!")
                return True
            else:
                print(f"❌ Chat ID error: {data.get('description')}")
                if "chat not found" in data.get('description', '').lower():
                    print("   💡 Make sure you've started a conversation with your bot")
                return False
        else:
            print(f"❌ Failed to send test message: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing chat ID: {str(e)}")
        return False

def test_backend_telegram_endpoint(token, chat_id):
    """Test the backend's Telegram endpoint."""
    print(f"\n🔍 Testing backend Telegram endpoint...")
    try:
        # Use a test user ID
        test_data = {
            "user_id": "test_user_123",
            "message": "What cakes do you have?",
            "chat_id": chat_id
        }
        
        response = requests.post(
            "http://localhost:5000/api/telegram/test-message",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Backend Telegram endpoint working!")
                return True
            else:
                print(f"❌ Backend error: {data.get('error')}")
                return False
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing backend endpoint: {str(e)}")
        return False

def main():
    """Main debug function."""
    print("🤖 Telegram Bot Debug Script")
    print("=" * 50)
    
    # Step 1: Test backend
    if not test_backend():
        return
    
    # Step 2: Get bot token
    token = input("\nEnter your Telegram bot token: ").strip()
    if not token:
        print("❌ No token provided")
        return
    
    # Step 3: Test bot token
    if not test_telegram_token(token):
        return
    
    # Step 4: Get chat ID
    chat_id = input("\nEnter your chat ID: ").strip()
    if not chat_id:
        print("❌ No chat ID provided")
        return
    
    # Step 5: Test chat ID
    if not test_chat_id(token, chat_id):
        return
    
    # Step 6: Test backend endpoint
    test_backend_telegram_endpoint(token, chat_id)
    
    print("\n" + "=" * 50)
    print("🔧 Debug Summary:")
    print("1. Backend is running ✅")
    print("2. Bot token is valid ✅")
    print("3. Chat ID is valid ✅")
    print("\nIf the backend endpoint failed, check:")
    print("- Your Telegram settings in the dashboard")
    print("- The Flask server logs for detailed errors")
    print("- Make sure you have data uploaded and stored in ChromaDB")

if __name__ == "__main__":
    main() 