#!/usr/bin/env python3
"""
Server runner for BusinessAI Platform
Simple script to start the Flask server with proper configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the Flask app
from app import app

if __name__ == '__main__':
    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY not found!")
        print("📝 Please set your API key in the .env file or environment variables")
        print("🔗 Get your API key from: https://makersuite.google.com/app/apikey")
        print()
    
    print("🚀 Starting BusinessAI Platform Server...")
    print("🌐 Server will be available at: http://localhost:5000")
    print("🔧 API endpoints:")
    print("   - POST /api/upload    (File upload)")
    print("   - POST /api/scrape    (URL scraping)")
    print("   - GET  /api/health    (Health check)")
    print("   - GET  /api/content-types (Content types)")
    print()
    
    # Run the Flask app
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "True").lower() == "true",
        host='0.0.0.0',
        port=int(os.environ.get("FLASK_PORT", 5000)),
        threaded=True
    ) 