"""
Console Manager - Advanced console allocation and output management
Handles console attachment, output redirection, and smart logging
"""

import os
import sys
import ctypes
import time
from ctypes import wintypes
from typing import Optional, TextIO


class ConsoleManager:
    """Manages console allocation and output redirection for Windows applications"""
    
    def __init__(self):
        self.console_allocated = False
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.log_files = {}
        
        # Windows API constants
        self.STD_OUTPUT_HANDLE = -11
        self.STD_ERROR_HANDLE = -12
        self.GENERIC_WRITE = 0x40000000
        self.FILE_SHARE_WRITE = 0x2
        self.OPEN_EXISTING = 3
        
    def try_attach_console(self) -> bool:
        """
        Try to attach to parent console or allocate new one
        Returns True if console is available for output
        """
        if not os.name == 'nt':
            return True  # Unix-like systems always have console access
            
        try:
            # Try to attach to parent process console (if launched from terminal)
            kernel32 = ctypes.windll.kernel32
            
            # First try to attach to parent console
            if kernel32.AttachConsole(-1):  # ATTACH_PARENT_PROCESS
                self.console_allocated = True
                self._redirect_to_console()
                return True
                
            # If no parent console, try to allocate a new one
            if kernel32.AllocConsole():
                self.console_allocated = True
                self._redirect_to_console()
                # Set console title
                kernel32.SetConsoleTitleW("Ouija Debug Console")
                return True
                
            return False
            
        except Exception as e:
            print(f"Console allocation failed: {e}")
            return False
    
    def _redirect_to_console(self):
        """Redirect stdout/stderr to the allocated console"""
        try:
            # Redirect stdout
            sys.stdout = open('CONOUT$', 'w', encoding='utf-8', errors='replace')
            # Redirect stderr  
            sys.stderr = open('CONOUT$', 'w', encoding='utf-8', errors='replace')
        except Exception as e:
            print(f"Console redirection failed: {e}")
    
    def setup_file_logging(self, base_name: str = "ouija", cleanup_old: bool = True):
        """
        Set up file logging with rotation
        
        Args:
            base_name: Base name for log files
            cleanup_old: Whether to clean up old log files on startup
        """
        if cleanup_old:
            self._cleanup_old_logs(base_name)
        
        # Set up log files
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        stdout_file = f"{base_name}_stdout_{timestamp}.log"
        stderr_file = f"{base_name}_stderr_{timestamp}.log"
        
        try:
            self.log_files['stdout'] = open(stdout_file, 'w', encoding='utf-8')
            self.log_files['stderr'] = open(stderr_file, 'w', encoding='utf-8')
            
            # Create symlinks to latest logs (for easy access)
            self._create_latest_symlinks(base_name, stdout_file, stderr_file)
            
            return True
        except Exception as e:
            print(f"File logging setup failed: {e}")
            return False
    
    def _cleanup_old_logs(self, base_name: str, keep_count: int = 5):
        """Clean up old log files, keeping only the most recent ones"""
        try:
            import glob
            pattern = f"{base_name}_*.log"
            files = glob.glob(pattern)
            files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove old files beyond keep_count
            for old_file in files[keep_count:]:
                try:
                    os.remove(old_file)
                except:
                    pass  # Ignore errors when cleaning up
                    
        except Exception:
            pass  # Don't let cleanup errors affect startup
    
    def _create_latest_symlinks(self, base_name: str, stdout_file: str, stderr_file: str):
        """Create 'latest' symlinks for easy access to current logs"""
        try:
            latest_stdout = f"{base_name}_stdout_latest.log"
            latest_stderr = f"{base_name}_stderr_latest.log"
            
            # Remove existing symlinks
            for link in [latest_stdout, latest_stderr]:
                if os.path.exists(link):
                    os.remove(link)
            
            # Create new symlinks (fallback to copy on Windows without admin)
            try:
                os.symlink(stdout_file, latest_stdout)
                os.symlink(stderr_file, latest_stderr)
            except OSError:
                # Fallback: just copy the file paths to .txt files
                with open(f"{base_name}_latest_logs.txt", 'w') as f:
                    f.write(f"Current stdout log: {stdout_file}\n")
                    f.write(f"Current stderr log: {stderr_file}\n")
                    
        except Exception:
            pass  # Don't let symlink creation affect functionality
    
    def create_tee_output(self, original_stream: TextIO, log_file: Optional[TextIO] = None, 
                         console_output: bool = True) -> TextIO:
        """
        Create a "tee" output that writes to multiple destinations
        
        Args:
            original_stream: Original stream (stdout/stderr)
            log_file: Optional log file to write to
            console_output: Whether to write to console
        """
        class TeeOutput:
            def __init__(self, original, log_file, console_output):
                self.original = original
                self.log_file = log_file
                self.console_output = console_output
                
            def write(self, text):
                # Write to original stream if console output enabled
                if self.console_output and self.original:
                    try:
                        self.original.write(text)
                        self.original.flush()
                    except:
                        pass
                
                # Write to log file
                if self.log_file:
                    try:
                        self.log_file.write(text)
                        self.log_file.flush()
                    except:
                        pass
                        
            def flush(self):
                if self.console_output and self.original:
                    try:
                        self.original.flush()
                    except:
                        pass
                if self.log_file:
                    try:
                        self.log_file.flush()
                    except:
                        pass
        
        return TeeOutput(original_stream, log_file, console_output)
    
    def setup_comprehensive_logging(self) -> bool:
        """
        Set up comprehensive logging that captures everything
        Returns True if successfully configured
        """
        success = True
        
        # Try to attach console for development debugging
        console_available = self.try_attach_console()
        
        # Set up file logging
        file_logging = self.setup_file_logging()
        
        if file_logging:
            # Create tee outputs that write to both console and files
            stdout_tee = self.create_tee_output(
                self.original_stdout, 
                self.log_files.get('stdout'),
                console_available
            )
            stderr_tee = self.create_tee_output(
                self.original_stderr,
                self.log_files.get('stderr'), 
                console_available
            )
            
            # Replace system streams
            sys.stdout = stdout_tee
            sys.stderr = stderr_tee
            
            # Log startup info
            print(f"🔧 Ouija Console Manager initialized")
            print(f"   Console available: {console_available}")
            print(f"   File logging: {file_logging}")
            if file_logging:
                print(f"   Log files: ouija_stdout_latest.log, ouija_stderr_latest.log")
        
        return success
    
    def cleanup(self):
        """Clean up console manager resources"""
        try:
            # Close log files
            for log_file in self.log_files.values():
                if log_file and not log_file.closed:
                    log_file.close()
            
            # Restore original streams
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            
            # Free console if we allocated it
            if self.console_allocated and os.name == 'nt':
                ctypes.windll.kernel32.FreeConsole()
                
        except Exception as e:
            print(f"Console cleanup error: {e}")


# Global console manager instance
console_manager = ConsoleManager()


def setup_console_logging():
    """Convenience function to set up console logging"""
    return console_manager.setup_comprehensive_logging()


def cleanup_console_logging():
    """Convenience function to clean up console logging"""
    console_manager.cleanup()
