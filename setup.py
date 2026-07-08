#!/usr/bin/env python3
"""
Installation and setup script for SKILLOR.
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install all required dependencies."""
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
    print("✅ Dependencies installed")

def create_directories():
    """Create required directories."""
    print("📁 Creating directories...")
    os.makedirs("assets", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("prompts", exist_ok=True)
    print("✅ Directories created")

def setup_env():
    """Setup environment variables."""
    print("\n⚙️  Environment Setup\n")
    
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print("🔐 Creating .env file (copy from .env.example)")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as f:
                content = f.read()
            with open(env_file, "w") as f:
                f.write(content)
            print("✅ .env file created")
    else:
        print("✅ .env file already exists")
    
    print("\n📋 Required API Keys:")
    print("  1. GROQ_API_KEY - https://console.groq.com")
    print("  2. GEMINI_API_KEY - https://ai.google.dev")
    print("  3. HF_API_KEY - https://huggingface.co/settings/tokens")
    print("  4. YT_CLIENT_SECRET - Google Cloud Console")
    print("  5. FB_ACCESS_TOKEN - Facebook Developers")
    print("  6. FB_PAGE_ID - Your Facebook Page ID")
    print("\nUpdate these in .env file before running pipeline.")

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    print("\n🎬 Checking FFmpeg installation...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg is not installed")
        print("\n📥 Install FFmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt-get install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")

def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("🚀 SKILLOR Setup")
    print("YouTube Shorts Automation for Parenting Content")
    print("="*60 + "\n")
    
    try:
        create_directories()
        install_dependencies()
        setup_env()
        check_ffmpeg()
        
        print("\n" + "="*60)
        print("✅ Setup Complete!")
        print("="*60)
        print("\n🎯 Next Steps:")
        print("  1. Edit .env file with your API keys")
        print("  2. Place placeholder.png in assets/ folder")
        print("  3. Run: python src/main.py")
        print("\n📚 Documentation:")
        print("  - README.md - Overview and features")
        print("  - AUTOMATION_REQUIREMENTS.md - Detailed strategy")
        print("\n" + "="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
