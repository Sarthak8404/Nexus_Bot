#!/usr/bin/env python3
"""
Setup script for BusinessAI Platform
Installs all required dependencies and sets up the environment
"""

import subprocess
import sys
import os
import shutil

def run_command(command):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return False

def setup_python_environment():
    """Set up Python environment and install dependencies."""
    print("🔧 Setting up Python environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Upgrade pip
    print("📦 Upgrading pip...")
    if not run_command(f"{sys.executable} -m pip install --upgrade pip"):
        return False
    
    # Install requirements
    print("📦 Installing Python dependencies...")
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        return False
    
    return True

def setup_environment_file():
    """Set up environment configuration file."""
    print("🔧 Setting up environment configuration...")
    
    env_file = ".env"
    example_file = "config.example.env"
    
    if os.path.exists(env_file):
        print(f"✅ {env_file} already exists")
        return True
    
    if os.path.exists(example_file):
        try:
            shutil.copy(example_file, env_file)
            print(f"✅ Created {env_file} from {example_file}")
            print("📝 Please edit .env file and add your GEMINI_API_KEY")
            return True
        except Exception as e:
            print(f"❌ Failed to copy {example_file} to {env_file}: {e}")
            return False
    
    # Create basic .env file
    try:
        with open(env_file, 'w') as f:
            f.write("# Google Gemini API Key\n")
            f.write("# Get your API key from: https://makersuite.google.com/app/apikey\n")
            f.write("GEMINI_API_KEY=your_gemini_api_key_here\n\n")
            f.write("# Flask configuration\n")
            f.write("FLASK_DEBUG=True\n")
            f.write("FLASK_PORT=5000\n")
        
        print(f"✅ Created {env_file}")
        print("📝 Please edit .env file and add your GEMINI_API_KEY")
        return True
    except Exception as e:
        print(f"❌ Failed to create {env_file}: {e}")
        return False

def test_installation():
    """Test the installation by importing key modules."""
    print("🧪 Testing installation...")
    
    test_modules = [
        'flask',
        'flask_cors',
        'requests',
        'bs4',
        'litellm',
        'dotenv',
        'PyPDF2',
        'docx'
    ]
    
    failed_modules = []
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_modules.append(module)
    
    if failed_modules:
        print(f"\n❌ Failed to import: {', '.join(failed_modules)}")
        return False
    
    print("✅ All modules imported successfully!")
    return True

def main():
    """Main setup function."""
    print("🌟 BusinessAI Platform Setup")
    print("=" * 40)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        print("Make sure you're in the correct directory.")
        return False
    
    # Setup Python environment
    if not setup_python_environment():
        print("\n❌ Failed to set up Python environment!")
        return False
    
    # Setup environment file
    if not setup_environment_file():
        print("\n❌ Failed to set up environment file!")
        return False
    
    # Test installation
    if not test_installation():
        print("\n❌ Installation test failed!")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your GEMINI_API_KEY")
    print("2. Run: python run_server.py")
    print("3. Open your browser and go to: http://localhost:5000")
    print("4. Open index.html in your browser for the frontend")
    print("\n🔗 Get Gemini API key: https://makersuite.google.com/app/apikey")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 