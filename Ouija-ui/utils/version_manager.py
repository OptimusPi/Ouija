"""
Version Utility - Manages application version information
"""

import os


class VersionManager:
    """Manages version information for Ouija application"""
    
    def __init__(self):
        self._version = None
        self._version_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version.ouija.txt')
        
    def get_version(self):
        """Get the current version string
        
        Returns:
            str: Version string (e.g., "0.3.14")
        """
        if self._version is None:
            self._load_version()
        return self._version
        
    def get_distribution_folder_name(self):
        """Get the distribution folder name based on version
        
        Returns:
            str: Distribution folder name (e.g., "Ouija-v0.3.14-Windows")
        """
        version = self.get_version()
        return f"Ouija-v{version}-Windows"
        
    def get_build_script_path(self):
        """Get the path to the distribution build script
        
        Returns:
            str: Path to build.ps1 in distribution folder
        """
        folder_name = self.get_distribution_folder_name()
        return os.path.join(os.getcwd(), 'distribution', folder_name, 'build.ps1')
        
    def get_distribution_working_dir(self):
        """Get the working directory for distribution builds
        
        Returns:
            str: Path to distribution folder
        """
        folder_name = self.get_distribution_folder_name()
        return os.path.join(os.getcwd(), 'distribution', folder_name)
        
    def _load_version(self):
        """Load version from version.ouija.txt file"""
        try:
            if os.path.exists(self._version_file_path):
                with open(self._version_file_path, 'r', encoding='utf-8') as f:
                    self._version = f.read().strip()
            else:
                # Fallback version if file doesn't exist
                self._version = "unknown"
        except Exception:
            # Fallback version if there's an error reading the file
            self._version = "unknown"


# Global instance
version_manager = VersionManager()
