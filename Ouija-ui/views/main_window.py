"""
Main Window View for Ouija Seed Finder Application
"""
import tkinter as tk
from tkinter import font
import sys
import time
import os
from utils.ui_utils import StatusBar, BACKGROUND, LIGHT_TEXT
from views.widgets.config_widget import ConfigWidget
from views.widgets.criteria_widget import CriteriaWidget
from views.widgets.results_widget import ResultsWidget
from views.widgets.run_settings_widget import RunSettingsWidget


class MainWindow:
    """Main window view for Ouija Seed Finder application"""

    def __init__(self, root, controller):
        """Initialize the main window"""
        self.root = root
        self.controller = controller
        self.search_running = False
        self._search_start_time = None

        # Define table font attributes early
        self.table_font_family = "m6x11"
        self.table_font_size = 16

        # Register this view with the controller
        controller.register_view(self)

        # Apply custom font
        self.setup_font()
        
        # Create main layout frames
        self.create_layout()
        
        # Create widgets in each section
        self.config_widget = ConfigWidget(self.left_column, controller, self)
        self.criteria_widget = CriteriaWidget(self.middle_column, controller, self)
        self.run_settings_widget = RunSettingsWidget(self.right_column, controller, self)
        self.results_widget = ResultsWidget(self.bottom_frame, controller, self)
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add startup logging
        print("🚀 Ouija UI initialized successfully!")
        print(f"🎯 Python executable: {sys.executable}")
        print(f"🔧 Frozen executable: {getattr(sys, 'frozen', False)}")
        
        # Initialize the UI with current settings
        self.update_config_display()
        self.update_criteria_display()

        # Connect to database if config was loaded
        if self.controller.config_model.loaded_config_path:
            self.controller.database_model.connect(
                self.controller.config_model.loaded_config_path)
        self.controller.refresh_results()
          # Check kernel status and update button accordingly
        self.update_kernel_button_state()

    def setup_font(self):
        """Set up custom font for the application and load TTF file"""
        # Load the font file from the Ouija root directory
        font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'm6x11.ttf')
        if os.path.exists(font_path):
            try:
                # Try to register the font with Windows
                import ctypes
                from ctypes import wintypes
                
                # Load the font temporarily for this session
                ctypes.windll.gdi32.AddFontResourceW(font_path)
                print(f"✅ Loaded m6x11.ttf font from {font_path}")
                
                # Configure the default font to use m6x11
                self.custom_font = font.nametofont("TkDefaultFont")
                self.custom_font.configure(family="m6x11", size=14)
                self.root.option_add("*Font", self.custom_font)
                
            except Exception as e:
                print(f"Could not load m6x11.ttf: {e}, using default font")
                self.custom_font = font.nametofont("TkDefaultFont")
                self.root.option_add("*Font", self.custom_font)
        else:
            print(f"m6x11.ttf not found at {font_path}, using default font.")
            self.custom_font = font.nametofont("TkDefaultFont")
            self.root.option_add("*Font", self.custom_font)

    def create_layout(self):
        """Create the main layout with fixed left/middle columns and expanding right column"""
        # Create status bar first
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.lift() 

        # Main container frame
        self.main_container = tk.Frame(self.root, bg=BACKGROUND)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)        
        
        # Create top section with fixed height
        self.settings_frame = tk.Frame(self.main_container, bg=BACKGROUND, height=320)
        self.settings_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 5))
        self.settings_frame.pack_propagate(False)   

        # Fixed widths for left and middle columns
        LEFT_WIDTH = 305
        MIDDLE_WIDTH = 475

        self.left_column = tk.Frame(self.settings_frame, bg=BACKGROUND, width=LEFT_WIDTH)
        self.left_column.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 4))
        self.left_column.pack_propagate(False)

        self.middle_column = tk.Frame(self.settings_frame, bg=BACKGROUND, width=MIDDLE_WIDTH)
        self.middle_column.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 4))
        self.middle_column.pack_propagate(False)

        self.right_column = tk.Frame(self.settings_frame, bg=BACKGROUND)
        self.right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        self.right_column.pack_propagate(True)

        # Bottom section (remaining height)
        self.bottom_frame = tk.Frame(self.main_container, bg=BACKGROUND)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    # Delegate methods to widgets    
    def set_search_running(self, is_running):
        """Update the UI state when search is running or stops"""
        self.run_settings_widget.set_search_running(is_running)
        self.search_running = is_running

    def write_to_console(self, text, color=None):
        """Write text to the console output"""
        self.run_settings_widget.write_to_console(text, color)
        
    def set_status(self, text):
        """Set status bar text"""
        self.status_bar.set_status(text)
        
    def set_metrics(self, text):
        """Set metrics text in the status bar"""
        self.status_bar.set_metrics(text)
    
    def update_config_display(self):
        """Update the configuration display with current settings"""
        self.config_widget.update_display()
        self.run_settings_widget.update_display()
        self.results_widget.update_config_display()

    def update_criteria_display(self):
        """Update the criteria list display"""
        self.criteria_widget.update_criteria_display()

    def update_kernel_button_state(self, search_running=None):
        """Update the run button state based on kernel status"""
        if search_running is not None:
            self.search_running = search_running
        self.run_settings_widget.update_kernel_button_state(self.search_running)

    def update_results_table(self, dataframe):
        """Update results table with new data"""
        self.results_widget.update_results_table(dataframe)

    def run_fun_seed_search(self, category):
        """Run a fun seed search for the given category"""
        self.controller.run_fun_seed_search(category)
            
    def on_closing(self):
        """Handle window closing"""
        try:
            # Stop any running search
            if self.search_running:
                self.controller.stop_search()
            
            # Close database connections
            if hasattr(self.controller, 'database_model'):
                self.controller.database_model.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.destroy()
