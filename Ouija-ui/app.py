#!/usr/bin/env python
"""
Ouija - Balatro Seed Finder (MVC Version)
Main application entry point
Author: pifreak
"""

import atexit
import os
import subprocess
import tkinter as tk

from controllers.application_controller import ApplicationController
from models.config_model import ConfigModel
from models.database_model import DatabaseModel
from models.search_model import SearchModel
from views.main_window import MainWindow

def cleanup_ouija_processes():
    """Ensure all Ouija-CLI.exe processes are terminated when the app exits"""
    try:
        if os.name == 'nt':  # Windows
            # Check if any Ouija-CLI.exe processes are running first
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Ouija-CLI.exe'], 
                                  capture_output=True, text=True)
            if 'Ouija-CLI.exe' in result.stdout:
                print("🧹 Cleaning up Ouija-CLI.exe processes...")
                subprocess.call(['taskkill', '/F', '/IM', 'Ouija-CLI.exe'], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:  # Unix/Linux/Mac
            subprocess.call(['pkill', '-f', 'Ouija-CLI.exe'], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Silently handle any cleanup errors - app is exiting anyway
        pass


def main():
    """Main entry point for the Ouija application"""
    import traceback
    import sys
    
    # Set up comprehensive error logging
    def log_error(error_type, error_msg, tb_str=""):
        """Log errors to both console and file"""
        timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {error_type}: {error_msg}"
        print(full_msg)
        if tb_str:
            print(f"Traceback:\n{tb_str}")
        
        try:
            with open("ouija_error.log", "a", encoding="utf-8") as f:
                f.write(f"{full_msg}\n")
                if tb_str:
                    f.write(f"Traceback:\n{tb_str}\n")
                f.write("-" * 50 + "\n")
        except:
            pass  # Don't let logging errors crash the app
    
    # Redirect stderr to capture any PyInstaller errors
    class ErrorCapture:
        def __init__(self, original_stderr):
            self.original_stderr = original_stderr
            
        def write(self, text):
            if text.strip():
                log_error("STDERR", text.strip())
            if self.original_stderr:
                self.original_stderr.write(text)
                
        def flush(self):
            if self.original_stderr:
                self.original_stderr.flush()
    
    # Capture stderr only in frozen executables (PyInstaller)
    if getattr(sys, 'frozen', False):
        sys.stderr = ErrorCapture(sys.stderr)
    
    # Set up global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_error("UNHANDLED EXCEPTION", str(exc_value), tb_str)
        
        # Still call the original exception handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception
    
    # Register cleanup handler to ensure Ouija processes are terminated on exit
    atexit.register(cleanup_ouija_processes)

    # Initialize the root window
    root = tk.Tk()
    root.title("Ouija - Balatro Seed Finder")
    root.geometry("1200x800")
    root.configure(bg="#394D53")
    
    # Set app icon
    try:
        root.iconbitmap("icon.ouija.ico")
    except tk.TclError:
        log_error("WARNING", "Icon file not found, using default icon")    # Initialize models with error handling
    try:
        config_model = ConfigModel()
        search_model = SearchModel()  # Remove console manager dependency
        database_model = DatabaseModel()
        
        # Initialize controller with models
        controller = ApplicationController(config_model, search_model, database_model)
        
        # Create the main window view and pass the controller
        main_window = MainWindow(root, controller)
        
        log_error("INFO", "Application initialized successfully")
        
    except Exception as e:
        tb_str = traceback.format_exc()
        log_error("INITIALIZATION ERROR", str(e), tb_str)
        return

    # Start the main event loop with proper exception handling
    try:
        log_error("INFO", "Starting main event loop")
        root.mainloop()
        log_error("INFO", "Main event loop ended normally")
    except KeyboardInterrupt:
        log_error("INFO", "Application closed by user (Ctrl+C)")
    except Exception as e:
        tb_str = traceback.format_exc()
        log_error("MAINLOOP ERROR", str(e), tb_str)
    finally:
        log_error("INFO", "Starting final cleanup")
        # Ensure cleanup happens regardless of how we exit
        try:
            if 'controller' in locals():
                controller.cleanup()
            log_error("INFO", "Controller cleanup completed")
        except Exception as e:
            tb_str = traceback.format_exc()
            log_error("CLEANUP ERROR", str(e), tb_str)
        
        try:
            cleanup_ouija_processes()
            log_error("INFO", "Process cleanup completed")
        except Exception as e:
            tb_str = traceback.format_exc()
            log_error("PROCESS CLEANUP ERROR", str(e), tb_str)
        
        log_error("INFO", "Application shutdown complete")


if __name__ == "__main__":
    main()
