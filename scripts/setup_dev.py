#!/usr/bin/env python3
"""
Development environment setup script.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"📋 {description}")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False
    return True

def main():
    """Set up development environment."""
    print("🚀 Setting up PolyIngest development environment")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "Creating .env file from template")
            print("📝 Please edit .env file with your API keys and configuration")
        else:
            print("⚠️  No .env.example found, please create .env manually")
    
    # Run tests
    if not run_command("python -m pytest tests/test_phase1.py -v", "Running Phase 1 tests"):
        print("⚠️  Some tests failed, but this is expected for initial setup")
    
    print("\n🎉 Phase 1 setup complete!")
    print("📝 Next steps:")
    print("   1. Edit .env file with your API keys")
    print("   2. Run: python -m uvicorn app.main:app --reload")
    print("   3. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()