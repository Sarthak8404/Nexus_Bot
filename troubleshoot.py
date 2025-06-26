#!/usr/bin/env python3
"""
Troubleshooting script for BusinessAI Platform
Diagnoses common issues and provides solutions
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_required_files():
    """Check if all required files exist."""
    print("\n🔍 Checking required files...")
    required_files = [
        'app.py',
        'requirements.txt',
        'index.html',
        'dashboard.html',
        'styles.css',
        'dashboard.js',
        'auth.js'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files

def check_environment_file():
    """Check environment configuration."""
    print("\n🔍 Checking environment configuration...")
    
    if os.path.exists('.env'):
        print("✅ .env file exists")
        try:
            with open('.env', 'r') as f:
                content = f.read()
                if 'GEMINI_API_KEY=' in content and 'your_gemini_api_key_here' not in content:
                    print("✅ GEMINI_API_KEY appears to be configured")
                    return True
                else:
                    print("⚠️  GEMINI_API_KEY not properly configured in .env")
                    return False
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
            return False
    else:
        print("❌ .env file missing")
        return False

def check_dependencies():
    """Check if all required Python packages are installed."""
    print("\n🔍 Checking Python dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'requests',
        'bs4',
        'litellm',
        'dotenv',
        'PyPDF2',
        'docx'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def test_flask_import():
    """Test if Flask app can be imported."""
    print("\n🔍 Testing Flask app import...")
    try:
        sys.path.insert(0, os.getcwd())
        from app import app
        print("✅ Flask app imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False

def check_port_availability():
    """Check if port 5000 is available."""
    print("\n🔍 Checking port availability...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("⚠️  Port 5000 is already in use")
            return False
        else:
            print("✅ Port 5000 is available")
            return True
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False

def provide_solutions(issues):
    """Provide solutions for identified issues."""
    print("\n" + "="*50)
    print("🔧 SOLUTIONS FOR IDENTIFIED ISSUES")
    print("="*50)
    
    if 'python_version' in issues:
        print("\n❌ Python Version Issue:")
        print("   Solution: Install Python 3.8 or higher")
        print("   Download: https://www.python.org/downloads/")
    
    if 'missing_files' in issues:
        print(f"\n❌ Missing Files: {', '.join(issues['missing_files'])}")
        print("   Solution: Make sure you have all project files")
        print("   Re-download the complete project if necessary")
    
    if 'env_file' in issues:
        print("\n❌ Environment Configuration Issue:")
        print("   Solution 1: Create .env file:")
        print("   cp config.example.env .env")
        print("   Solution 2: Add your Gemini API key to .env:")
        print("   GEMINI_API_KEY=your_actual_api_key_here")
        print("   Get API key: https://makersuite.google.com/app/apikey")
    
    if 'dependencies' in issues:
        print(f"\n❌ Missing Dependencies: {', '.join(issues['dependencies'])}")
        print("   Solution: Install missing packages:")
        print("   pip install -r requirements.txt")
        print("   Or run: python setup.py")
    
    if 'flask_import' in issues:
        print("\n❌ Flask Import Issue:")
        print("   Solution 1: Reinstall dependencies:")
        print("   pip install -r requirements.txt --force-reinstall")
        print("   Solution 2: Check for syntax errors in app.py")
    
    if 'port_in_use' in issues:
        print("\n❌ Port 5000 In Use:")
        print("   Solution 1: Kill process using port 5000")
        print("   Solution 2: Use different port:")
        print("   python run_server.py --port 5001")
        print("   Solution 3: Update FLASK_PORT in .env file")

def run_quick_fixes():
    """Run quick fixes for common issues."""
    print("\n🔧 Running quick fixes...")
    
    # Create .env file if missing
    if not os.path.exists('.env') and os.path.exists('config.example.env'):
        try:
            import shutil
            shutil.copy('config.example.env', '.env')
            print("✅ Created .env file from template")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    
    # Try to install missing dependencies
    if os.path.exists('requirements.txt'):
        try:
            print("🔧 Attempting to install dependencies...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")

def main():
    """Main troubleshooting function."""
    print("🔍 BusinessAI Platform Troubleshooter")
    print("="*50)
    
    issues = {}
    
    # Run all checks
    if not check_python_version():
        issues['python_version'] = True
    
    files_ok, missing_files = check_required_files()
    if not files_ok:
        issues['missing_files'] = missing_files
    
    if not check_environment_file():
        issues['env_file'] = True
    
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        issues['dependencies'] = missing_deps
    
    if not test_flask_import():
        issues['flask_import'] = True
    
    if not check_port_availability():
        issues['port_in_use'] = True
    
    # Provide solutions if issues found
    if issues:
        provide_solutions(issues)
        
        # Ask if user wants to run quick fixes
        print("\n" + "="*50)
        response = input("🤖 Would you like me to run quick fixes? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            run_quick_fixes()
    else:
        print("\n🎉 All checks passed! Your setup looks good.")
        print("\n📋 To start the platform:")
        print("1. Make sure your GEMINI_API_KEY is set in .env")
        print("2. Run: python run_server.py")
        print("3. Open index.html in your browser")
    
    print("\n" + "="*50)
    print("🆘 If you're still having issues:")
    print("1. Share the exact error message")
    print("2. Mention what you were doing when the error occurred")
    print("3. Check the console output for more details")

if __name__ == "__main__":
    main() 