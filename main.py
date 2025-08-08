#!/usr/bin/env python3
"""
GamerX Installer - Main Entry Point
A modern, modular Arch Linux installer with beautiful TUI
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.app import GamerXInstallerApp
from utils.logging import setup_logging
from config.settings import VERSION, APP_NAME, THEME_COLORS

def check_requirements():
    """Check if running as root and other requirements"""
    if os.geteuid() != 0:
        print("❌ This installer must be run as root!")
        print("Please run: sudo python3 main.py")
        sys.exit(1)
    
    # Check if we're in a live environment
    if not os.path.exists("/run/archiso"):
        print("⚠️  Warning: Not running in Arch Linux live environment")
        print("This installer is designed for Arch Linux ISO")
        
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            sys.exit(1)

async def main():
    """Main application entry point"""
    print(f"🚀 Starting {APP_NAME} v{VERSION}")
    
    # Check requirements
    check_requirements()
    
    # Setup logging
    setup_logging()
    
    # Create and run the TUI application
    app = GamerXInstallerApp()
    await app.run_async()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Installation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
