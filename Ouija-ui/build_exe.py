#!/usr/bin/env python
"""
Build script for creating Ouija Windows executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Configuration
APP_NAME = "Ouija-UI"
VERSION = "0.3.14"

def run_command(cmd, cwd=None):
    """Run a command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    return result.returncode

def clean_directories(directories):
    """Clean specified directories"""
    for cleanup_dir in directories:
        if os.path.exists(cleanup_dir):
            print(f"Cleaning {cleanup_dir}...")
            shutil.rmtree(cleanup_dir)

def build_executable():
    """Build the executable using PyInstaller"""
    
    # Ensure we're in the right directory
    ui_dir = Path(__file__).parent
    os.chdir(ui_dir)
    
    print("=== Building Ouija UI Windows Executable ===")
    
    # Clean previous builds
    clean_directories(["dist", "build"])
    
    if os.path.exists(f"{APP_NAME}.spec"):
        os.remove(f"{APP_NAME}.spec")
      # PyInstaller command with noconsole flag to prevent terminal window
    cmd = [
        "python", "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--noconsole",
        "--noconfirm",
        "--icon", "icon.ouija.ico",
        "app.py"
    ]
    
    result = run_command(cmd)
    
    if result == 0 and os.path.exists(f"dist/{APP_NAME}.exe"):
        print(f"✅ Executable built successfully: dist/{APP_NAME}.exe")
        return True
    else:
        print(f"❌ Build failed with code {result}")
        return False

if __name__ == "__main__":
    if build_executable():
        print("✅ Build completed successfully!")
    else:
        print("❌ Build failed!")
        sys.exit(1)
