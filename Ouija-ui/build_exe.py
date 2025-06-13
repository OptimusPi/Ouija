#!/usr/bin/env python
"""
Build script for creating Ouija Windows executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tkinter.font as tkfont

# Configuration
APP_NAME = "Ouija-UI"
# Dynamically read version from version.ouija.txt
with open(os.path.join(os.path.dirname(__file__), '..', 'version.ouija.txt'), 'r', encoding='utf-8') as vf:
    VERSION = vf.read().strip()

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

    # Ensure icon file exists
    if not os.path.exists("icon.ouija.ico"):
        print("❌ ERROR: icon.ouija.ico not found! The app will use a default icon if you continue.")
        return False
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

def setup_font(self):
    """Set up custom font for the application with slightly larger size"""
    font_path = os.path.join(os.path.dirname(__file__), '..', 'm6x11.ttf')
    if os.path.exists(font_path):
        try:
            # Register the font with Tkinter
            font_name = tkfont.Font(family="m6x11", size=13).actual('family')
            self.root.tk.call('font', 'create', 'm6x11', '-family', 'm6x11', '-size', 13)
            self.root.tk.call('font', 'configure', 'm6x11', '-family', 'm6x11', '-size', 13)
            # For Tk 8.6+, you can use 'font add' to load a font file
            self.root.tk.call('font', 'add', font_path)
        except Exception as e:
            print(f"Could not load m6x11.ttf: {e}")
    else:
        print("m6x11.ttf not found, using default font.")

    # Now set the default font for the app
    self.custom_font = tkfont.Font(family="m6x11", size=13)
    self.root.option_add("*Font", self.custom_font)

if __name__ == "__main__":
    if build_executable():
        print("✅ Build completed successfully!")
    else:
        print("❌ Build failed!")
        sys.exit(1)
