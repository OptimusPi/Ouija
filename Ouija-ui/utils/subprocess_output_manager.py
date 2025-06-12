"""
Subprocess Output Manager - Handles subprocess output redirection and logging
Solves the problem of GUI applications losing CLI process output
"""

import os
import sys
import subprocess
import threading
import time
from typing import Optional, Callable, TextIO


class SubprocessOutputManager:
    """Manages subprocess output with proper console and file redirection"""
    
    def __init__(self, console_manager=None):
        self.console_manager = console_manager
        
    def create_process_with_output_redirection(
        self, 
        command: str,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
        cwd: Optional[str] = None,
        enable_console_output: bool = True
    ) -> subprocess.Popen:
        """
        Create a subprocess with proper output redirection
        
        Args:
            command: Command to execute
            stdout_callback: Callback for stdout lines
            stderr_callback: Callback for stderr lines  
            cwd: Working directory
            enable_console_output: Whether to enable console output (for terminal visibility)
            
        Returns:
            subprocess.Popen: The created process
        """
        # Configure process creation flags
        creation_flags = 0
        
        # If we have a console available and console output is enabled, don't suppress it
        if enable_console_output and self.console_manager and self.console_manager.console_allocated:
            # Allow the process to inherit the console
            creation_flags = 0
        else:
            # Suppress console window for GUI-only mode
            creation_flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        
        # Create process with pipes for output capture
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            creationflags=creation_flags,
            # On Windows, also try to use the same console
            **self._get_console_inheritance_kwargs()
        )
        
        # Start output processing threads
        if stdout_callback:
            stdout_thread = threading.Thread(
                target=self._process_stdout,
                args=(process, stdout_callback),
                daemon=True
            )
            stdout_thread.start()
            
        if stderr_callback:
            stderr_thread = threading.Thread(
                target=self._process_stderr,
                args=(process, stderr_callback),
                daemon=True
            )
            stderr_thread.start()
            
        return process
    
    def _get_console_inheritance_kwargs(self) -> dict:
        """Get platform-specific kwargs for console inheritance"""
        if os.name != 'nt':
            return {}
            
        # On Windows, try to inherit console handles if available
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            # Check if we have console handles
            stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            stderr_handle = kernel32.GetStdHandle(-12)  # STD_ERROR_HANDLE
            
            if stdout_handle and stderr_handle:
                return {
                    'startupinfo': subprocess.STARTUPINFO(),
                }
        except:
            pass
            
        return {}
    
    def _process_stdout(self, process: subprocess.Popen, callback: Callable[[str], None]):
        """Process stdout in a separate thread"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    # Send to callback
                    callback(line.rstrip('\n'))
                    
                    # Also send to console if available
                    if self.console_manager and self.console_manager.console_allocated:
                        try:
                            print(line.rstrip('\n'), flush=True)
                        except:
                            pass
                            
                    # Log to file if available
                    if self.console_manager and 'stdout' in self.console_manager.log_files:
                        try:
                            self.console_manager.log_files['stdout'].write(line)
                            self.console_manager.log_files['stdout'].flush()
                        except:
                            pass
                            
        except Exception as e:
            callback(f"Error processing stdout: {e}")
        finally:
            if process.stdout:
                process.stdout.close()
    
    def _process_stderr(self, process: subprocess.Popen, callback: Callable[[str], None]):
        """Process stderr in a separate thread"""
        try:
            for line in iter(process.stderr.readline, ''):
                if line:
                    # Send to callback
                    callback(line.rstrip('\n'))
                    
                    # Also send to console if available
                    if self.console_manager and self.console_manager.console_allocated:
                        try:
                            print("ERROR: " + line.rstrip('\n'), file=sys.stderr, flush=True)
                        except:
                            pass
                            
                    # Log to file if available
                    if self.console_manager and 'stderr' in self.console_manager.log_files:
                        try:
                            self.console_manager.log_files['stderr'].write(f"ERROR: {line}")
                            self.console_manager.log_files['stderr'].flush()
                        except:
                            pass
                            
        except Exception as e:
            callback(f"Error processing stderr: {e}")
        finally:
            if process.stderr:
                process.stderr.close()


class TeeOutput:
    """Utility class to duplicate output to multiple destinations"""
    
    def __init__(self, *outputs: TextIO):
        self.outputs = outputs
        
    def write(self, text: str):
        for output in self.outputs:
            try:
                output.write(text)
                output.flush()
            except:
                pass
                
    def flush(self):
        for output in self.outputs:
            try:
                output.flush()
            except:
                pass
