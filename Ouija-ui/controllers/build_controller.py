"""
Build Controller - Handles kernel build operations
"""

import json
import os
import subprocess
import threading                    

from utils.result import Result
from utils.version_manager import version_manager

class BuildController:
    """Controller for build operations"""

    def __init__(self):
        self.current_view = None
        self.build_running = False

    def register_view(self, view):
        """Register the main view for callbacks"""
        self.current_view = view

    def is_kernel_build_needed(self):
        """Check if kernel binaries are missing or installation is incomplete
        
        Returns:
            bool: True if build is needed
        """
        conf_path = 'user.ouija.conf'
        try:
            if os.path.exists(conf_path):
                with open(conf_path, 'r') as f:
                    conf = json.load(f)
                if conf.get('installation_success'):
                    return False
        except Exception:
            pass        
        # Check for Ouija-CLI.exe and at least one .bin kernel file
        exe_path = "./Ouija-CLI.exe"
        kernels_dir = "./ouija_filters"
        has_exe = os.path.exists(exe_path)
        has_bin = False

        if os.path.isdir(kernels_dir):
            for fname in os.listdir(kernels_dir):
                if fname.endswith('.bin'):
                    has_bin = True
                    break

        return not (has_exe and has_bin)

    def run_kernel_build(self, on_complete=None):
        """Run kernel build operation
        
        Args:
            on_complete (callable, optional): Callback when build completes
            
        Returns:
            Result: Success/failure with error details
        """
        if self.build_running:
            if self.current_view:
                self.current_view.write_to_console(
                    "[Info] Kernel build already running.\n", color="white")
            return Result.error("Kernel build already running")
        
        self.build_running = True
        
        # Update status and button state immediately when build starts
        if self.current_view:
            self.current_view.set_status("Building kernels...")
            self.current_view.run_settings_widget.update_kernel_button_state(False)

        def build_done():
            self.build_running = False
            if on_complete:
                on_complete()
            if self.current_view:
                self.current_view.set_status("Kernel build finished.")
                # Update button state after build completes - go directly to the widget
                self.current_view.run_settings_widget.update_kernel_button_state(False)

        try:
            self._run_build_script(on_complete=build_done)
            return Result.success("Kernel build started")
        except Exception as e:
            self.build_running = False
            return Result.error(f"Failed to start kernel build: {str(e)}")

    def _run_build_script(self, on_complete=None):
        """Run precompile_kernels.ps1 -PrecompileKernels and stream output to the console
        
        Args:
            on_complete (callable, optional): Callback when build completes
        """          
        def run_and_stream():
            try:
                if self.current_view:
                    self.current_view.write_to_console(
                        "\n⚙️ Running kernel build...\n", color="white")                # Find the precompile_kernels.ps1 script
                script_path = self._get_precompile_script_path()
                
                # Just run the local script directly
                process = subprocess.Popen([
                    'powershell.exe', '-NoProfile', '-WindowStyle', 'Hidden', '-NonInteractive', 
                    '-ExecutionPolicy', 'Bypass', '-File', script_path, '-PrecompileKernels'
                ], stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT,
                   text=True,
                   encoding='utf-8',
                   creationflags=subprocess.CREATE_NO_WINDOW,
                   startupinfo=self._get_startup_info())
                
                if self.current_view:
                    self.current_view.write_to_console(
                        "\n⚙️ Please Wait...This takes a long time but only needs to run once!\n", color="white")

                for line in process.stdout:
                    if self.current_view:
                        # Ensure each output ends with a newline for proper display
                        if not line.endswith('\n'):
                            line += '\n'
                        self.current_view.write_to_console(line, color="blue")

                process.wait()

                if process.returncode == 0:
                    if self.current_view:
                        self.current_view.write_to_console(
                            "\n✅ Kernel build complete!\n", color="green")
                    self._mark_installation_success()
                else:
                    if self.current_view:
                        self.current_view.write_to_console(
                            "\n❌ Kernel build failed!\n", color="red")

                if on_complete:
                    on_complete()

            except Exception as e:
                if self.current_view:
                    self.current_view.write_to_console(
                        f"[Error] Kernel build crashed: {e}\n", color="red")
                if on_complete:
                    on_complete()        # Run in a thread so the UI doesn't freeze
        threading.Thread(target=run_and_stream, daemon=True).start()

    def _get_startup_info(self):
        """Get startup info to hide console windows on Windows"""
        if os.name == "nt":  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            return startupinfo
        return None

    def _get_precompile_script_path(self):
        """Find the precompile_kernels.ps1 script path"""
        # Try different possible locations
        possible_paths = [
            "precompile_kernels.ps1",  # Current working directory (installed location)
            "./precompile_kernels.ps1",  # Same directory  
            "../precompile_kernels.ps1",  # Parent directory (development)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # If not found, raise an error with helpful info
        cwd = os.getcwd()
        raise FileNotFoundError(
            f"precompile_kernels.ps1 not found. Searched:\n"
            f"Current working directory: {cwd}\n" +
            "\n".join(f"  - {path} ({'EXISTS' if os.path.exists(path) else 'NOT FOUND'})" 
                     for path in possible_paths)
        )

    def _mark_installation_success(self):
        """Mark installation success in user.ouija.conf"""
        try:
            conf_path = os.path.join(os.getcwd(), 'user.ouija.conf')
            if os.path.exists(conf_path):
                with open(conf_path, 'r') as f:
                    conf = json.load(f)
            else:
                conf = {}

            conf['installation_success'] = True

            with open(conf_path, 'w') as f:
                json.dump(conf, f, indent=2)

        except Exception as e:
            if self.current_view:
                self.current_view.write_to_console(
                    f"[Warning] Could not update user.ouija.conf: {e}\n",
                    color="red")

    def is_build_running(self):
        """Check if a build is currently running
        
        Returns:
            bool: True if build is running
        """
        return self.build_running
