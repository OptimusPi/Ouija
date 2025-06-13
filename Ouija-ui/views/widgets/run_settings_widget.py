"""
Run Settings Widget - Handles console output, GPU settings, and run button
"""
import tkinter as tk
from tkinter import ttk
import time
from utils.ui_utils import (BLUE, RED, GREEN, YELLOW, BACKGROUND, DARK_BACKGROUND, LIGHT_TEXT)


class RunSettingsWidget:
    """Widget for run settings including console, GPU controls, and run button"""
    
    def __init__(self, parent_frame, controller, main_window):
        """
        Initialize the run settings widget
        
        Args:
            parent_frame: The parent frame to place this widget in
            controller: The application controller
            main_window: Reference to the main window for callbacks
        """
        self.parent_frame = parent_frame
        self.controller = controller
        self.main_window = main_window
        
        # Initialize state
        self.search_running = False
        self._search_start_time = None
        self._color_tags_configured = False
        
        # Create the widget
        self.create_widget()
        
    def create_widget(self):
        """Create the run settings section with console on TOP, GPU settings in middle, button on BOTTOM"""
        self.run_settings_frame = tk.LabelFrame(self.parent_frame,
                                                text="Run",
                                                padx=3,
                                                pady=3,
                                                bg=BACKGROUND,
                                                fg=LIGHT_TEXT,
                                                font=("m6x11", 14))
        self.run_settings_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # 1. CONSOLE OUTPUT AT THE TOP (expandable)
        self.create_console()
        
        # 2. GPU SETTINGS IN 2x2 GRID (fixed height, always visible)
        self.create_gpu_settings()
        
        # 3. "LET JIMBO COOK!" BUTTON AT THE BOTTOM (always visible, full width)
        self.create_run_button()
        
    def create_console(self):
        """Create the console output area"""
        console_frame = tk.Frame(self.run_settings_frame, bg=BACKGROUND)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.output_text = tk.Text(console_frame, wrap=tk.WORD, bg=DARK_BACKGROUND, fg=LIGHT_TEXT,
                                font=("m6x11", 13), insertbackground='white', height=8)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
    def create_gpu_settings(self):
        """Create the GPU settings in 2x2 grid"""
        gpu_frame = tk.Frame(self.run_settings_frame, bg=BACKGROUND, height=80)
        gpu_frame.pack(fill=tk.X, padx=4, pady=4)
        gpu_frame.pack_propagate(False)  # Keep fixed height
        
        # Configure grid columns for 2x2 layout
        gpu_frame.grid_columnconfigure(0, weight=0)  # Left labels
        gpu_frame.grid_columnconfigure(1, weight=1)  # Left controls
        gpu_frame.grid_columnconfigure(2, weight=0)  # Right labels
        gpu_frame.grid_columnconfigure(3, weight=1)  # Right controls
        
        # Row 0: GPU Batch Size (left) | Thread Groups (right)
        tk.Label(gpu_frame, text="Batch Multiplier:", bg=BACKGROUND, fg=LIGHT_TEXT, 
                font=("m6x11", 12)).grid(row=0, column=0, sticky="w", pady=4, padx=(0, 5))
        self.gpu_batch_var = tk.StringVar()
        self.gpu_batch_dropdown = ttk.Combobox(gpu_frame, textvariable=self.gpu_batch_var,
                                            state="readonly", font=("m6x11", 12), width=12)
        self.gpu_batch_dropdown['values'] = ["1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1024"]
        self.gpu_batch_dropdown.grid(row=0, column=1, sticky="w", pady=4)
        self.gpu_batch_dropdown.bind("<<ComboboxSelected>>", self.on_gpu_batch_changed)

        tk.Label(gpu_frame, text="Thread Groups:", bg=BACKGROUND, fg=LIGHT_TEXT,
                font=("m6x11", 12)).grid(row=0, column=2, sticky="w", pady=4, padx=(15, 5))
        self.thread_groups_var = tk.StringVar()
        self.thread_groups_dropdown = ttk.Combobox(gpu_frame, textvariable=self.thread_groups_var,
                                                state="readonly", font=("m6x11", 12), width=12)
        self.thread_groups_dropdown['values'] = ["Single", "16", "32", "64", "128", "256"]
        self.thread_groups_dropdown.grid(row=0, column=3, sticky="w", pady=4)
        self.thread_groups_dropdown.bind("<<ComboboxSelected>>", self.on_thread_groups_changed)

        # Row 1: Starting Seed (left) | Search Size (right)
        tk.Label(gpu_frame, text="Starting Seed:", bg=BACKGROUND, fg=LIGHT_TEXT,
                font=("m6x11", 12)).grid(row=1, column=0, sticky="w", pady=4, padx=(0, 5))
        seed_frame = tk.Frame(gpu_frame, bg=BACKGROUND)
        seed_frame.grid(row=1, column=1, sticky="w", pady=4)
        
        self.starting_seed_var = tk.StringVar()
        self.starting_seed_entry = tk.Entry(seed_frame, textvariable=self.starting_seed_var, 
                                            font=("m6x11", 12), width=11)
        self.starting_seed_entry.grid(row=0, column=0)
        
        random_seed_button = tk.Button(seed_frame, text="🎲", bg=GREEN, fg=LIGHT_TEXT,
                                    command=self.on_random_seed, font=("m6x11", 12))
        random_seed_button.grid(row=0, column=1, padx=(2, 2))

        tk.Label(gpu_frame, text="Search Size:", bg=BACKGROUND, fg=LIGHT_TEXT,
                font=("m6x11", 12)).grid(row=1, column=2, sticky="w", pady=4, padx=(15, 5))
        self.number_of_seeds_var = tk.StringVar()
        self.number_of_seeds_dropdown = ttk.Combobox(gpu_frame, textvariable=self.number_of_seeds_var,
                                                    state="readonly", font=("m6x11", 12), width=12)
        self.number_of_seeds_dropdown['values'] = ["All", "1 Single Seed", "1K", "100K", "1M", "100M", "1B", "10B", "100B"]
        self.number_of_seeds_dropdown.grid(row=1, column=3, sticky="w", pady=4)
        self.number_of_seeds_dropdown.bind("<<ComboboxSelected>>", self.on_number_of_seeds_changed)
        
    def create_run_button(self):
        """Create the main run button"""
        self.run_button = tk.Button(self.run_settings_frame, text="Let Jimbo Cook!",
                                    command=self.on_run_search, bg=BLUE, fg=LIGHT_TEXT,
                                    font=("m6x11", 16), height=2)
        self.run_button.pack(fill=tk.X, padx=4, pady=(5, 5))

    def write_to_console(self, text, color=None):
        """Write text to the console output with optional color coding
        
        Args:
            text: Text to write to console
            color: Optional color for the text ("white", "blue", "red")
                  - WHITE: Ouija UI messages
                  - BLUE: Ouija-CLI messages (status, CSV results, speedometer)
                  - RED: Ouija-CLI stderr messages
        """
        # Check if widgets still exist before trying to use them
        try:
            if hasattr(self, 'output_text') and self.output_text.winfo_exists():
                # Configure color tags if not already done
                if not self._color_tags_configured:
                    self.output_text.tag_configure("white", foreground="white")
                    self.output_text.tag_configure("blue", foreground="#008DFB")
                    self.output_text.tag_configure("red", foreground="#F94C3E")
                    self.output_text.tag_configure("green", foreground="#4CAF50")
                    self._color_tags_configured = True
                
                # Insert text with appropriate color tag
                if color:
                    # Get current position
                    start_pos = self.output_text.index(tk.END + "-1c")
                    self.output_text.insert(tk.END, text)
                    end_pos = self.output_text.index(tk.END + "-1c")
                    
                    # Apply color tag to the inserted text
                    self.output_text.tag_add(color, start_pos, end_pos)
                else:
                    # Default color (white) for unspecified text
                    start_pos = self.output_text.index(tk.END + "-1c")
                    self.output_text.insert(tk.END, text)
                    end_pos = self.output_text.index(tk.END + "-1c")
                    self.output_text.tag_add("white", start_pos, end_pos)
                
                self.output_text.see(tk.END)
        except tk.TclError:
            # Widget has been destroyed, silently ignore
            pass

    def on_run_search(self):
        """Handle run search button clicks"""
        if self.search_running:
            self.controller.stop_search()
        else:
            self.controller.run_search()

    def update_display(self):
        """Update the GPU settings display with current settings"""
        # Access settings directly from the controller's config_model
        config_model = self.controller.config_model
        # Update GPU settings
        self.gpu_batch_var.set(getattr(config_model, 'gpu_batch', '16'))
        self.thread_groups_var.set(getattr(config_model, 'thread_groups', '32'))
        self.starting_seed_var.set(getattr(config_model, 'startingSeed', 'random'))
        self.number_of_seeds_var.set(getattr(config_model, 'number_of_seeds', 'All'))

    def update_kernel_button_state(self, search_running):
        """Update the run button state based on kernel status"""
        self.search_running = search_running
        if search_running:
            self.run_button.config(text="STOP SEARCH", bg=RED)
        else:
            # Check if kernel build is currently running
            if hasattr(self.controller, 'build_controller') and self.controller.build_controller.is_build_running():
                self.run_button.config(text="PLEASE WAIT...", bg="#FFA500", state="disabled")
            # Check if kernel build is needed
            elif self.controller.is_kernel_build_needed():
                self.run_button.config(text="Build Kernels First", bg=YELLOW, state="normal")
            else:
                self.run_button.config(text="Let Jimbo Cook!", bg=BLUE, state="normal")

    def set_search_running(self, is_running):
        """Update search running state"""
        self.search_running = is_running
        if is_running:
            self._search_start_time = time.time()
        else:
            self._search_start_time = None
        self.update_kernel_button_state(is_running)

    # Event handlers
    def on_gpu_batch_changed(self, event=None):
        """Handle GPU batch size selection changes"""
        self.controller.set_setting('gpu_batch', self.gpu_batch_var.get())

    def on_thread_groups_changed(self, event=None):
        """Handle thread groups selection changes"""
        self.controller.set_setting('thread_groups', self.thread_groups_var.get())

    def on_random_seed(self):
        """Set the search seed to random, Ouija-CLI.exe handles this"""
        self.starting_seed_entry.delete(0, tk.END)
        self.starting_seed_entry.insert(0, "random")

    def on_number_of_seeds_changed(self, event=None):
        """Handle number of seeds selection changes"""
        self.controller.set_setting('number_of_seeds', self.number_of_seeds_var.get())

    def on_run_search(self):
        """Handle run search button clicks"""
        if self.search_running:
            self.controller.stop_search()
        else:            # Check if we need to build kernels first
            if self.controller.is_kernel_build_needed():
                self.controller.run_kernel_build()
            else:
                self.controller.run_search()
