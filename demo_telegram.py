#!/usr/bin/env python3
"""
Telegram Bot Demo Script
This script demonstrates the Telegram bot integration with sample business data.
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:5000"
DEMO_USER_ID = "demo_user_456"

def setup_demo_data():
    """Setup sample business data for the demo."""
    print("📊 Setting up demo business data...")
    
    # Sample bakery data
    sample_data = [
        {
            "name": "Chocolate Brownie",
            "description": "Rich and fudgy chocolate brownie with walnuts",
            "price": "₹120",
            "category": "Brownies",
            "availability": "In Stock"
        },
        {
            "name": "Vanilla Cupcake",
            "description": "Soft vanilla cupcake with buttercream frosting",
            "price": "₹80",
            "category": "Cupcakes",
            "availability": "In Stock"
        },
        {
            "name": "Red Velvet Cake",
            "description": "Classic red velvet cake with cream cheese frosting",
            "price": "₹450",
            "category": "Cakes",
            "availability": "In Stock"
        },
        {
            "name": "Chocolate Chip Cookies",
            "description": "Fresh baked cookies with chocolate chips",
            "price": "₹60",
            "category": "Cookies",
            "availability": "In Stock"
        },
        {
            "name": "Blueberry Muffin",
            "description": "Moist muffin loaded with fresh blueberries",
            "price": "₹90",
            "category": "Muffins",
            "availability": "In Stock"
        }
    ]
    
    # Store data in ChromaDB
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/store-chroma",
            json={
                "data": sample_data,
                "user_id": DEMO_USER_ID
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Demo data stored successfully")
                return True
            else:
                print(f"❌ Failed to store demo data: {result.get('error')}")
                return False
        else:
            print(f"❌ Failed to store demo data: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error storing demo data: {str(e)}")
        return False

def test_chat_responses():
    """Test various chat scenarios."""
    print("\n💬 Testing chat responses...")
    
    test_messages = [
        "What products do you have?",
        "Do you have brownies?",
        "How much does the red velvet cake cost?",
        "Tell me about your cupcakes",
        "What's the most expensive item?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/chat",
                json={
                    "message": message,
                    "user_id": DEMO_USER_ID
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('response'):
                    print(f"   Response: {result['response'][:100]}...")
                elif result.get('error'):
                    print(f"   Error: {result['error']}")
                else:
                    print("   No response")
            else:
                print(f"   HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        time.sleep(1)  # Small delay between requests

def simulate_telegram_message(message):
    """Simulate a Telegram message being received."""
    print(f"\n📱 Simulating Telegram message: '{message}'")
    
    # Simulate the webhook payload that Telegram would send
    webhook_payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 987654321,
                "first_name": "Demo",
                "username": "demo_user"
            },
            "chat": {
                "id": 987654321,
                "type": "private"
            },
            "date": int(time.time()),
            "text": message
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/telegram/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook processed successfully")
                print("   (In a real scenario, the bot would send a response to Telegram)")
            else:
                print(f"❌ Webhook error: {result}")
        else:
            print(f"❌ Webhook failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error simulating webhook: {str(e)}")

def main():
    """Main demonstration function."""
    print("🤖 BusinessAI Platform - Telegram Bot Demo")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend is not responding properly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}")
        return
    
    print("✅ Backend is running")
    
    # Setup demo data
    if not setup_demo_data():
        print("❌ Failed to setup demo data. Exiting.")
        return
    
    # Test chat functionality
    test_chat_responses()
    
    # Simulate Telegram messages
    print("\n📱 Simulating Telegram Bot Integration")
    print("-" * 40)
    
    telegram_messages = [
        "Hi! What do you have today?",
        "I want to order a cake",
        "How much are your brownies?",
        "Do you deliver?",
        "What's your most popular item?"
    ]
    
    for message in telegram_messages:
        simulate_telegram_message(message)
        time.sleep(2)  # Delay between simulations
    
    print("\n🎉 Demo completed!")
    print("\n📝 What this demonstrates:")
    print("1. ✅ Business data storage in ChromaDB")
    print("2. ✅ AI-powered chat responses")
    print("3. ✅ Telegram webhook processing")
    print("4. ✅ Contextual responses based on business data")
    print("\n🚀 To use with a real Telegram bot:")
    print("1. Create a bot with @BotFather")
    print("2. Configure it in the dashboard")
    print("3. Setup the webhook")
    print("4. Start receiving customer messages!")

if __name__ == "__main__":
    main() 