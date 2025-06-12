"""
Main Window View for Ouija Seed Finder Application
"""
import json
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font

import pandas as pd
from models.database_model import DatabaseModel
from pandastable import Table
from utils.game_data import AVAILABLE_ITEMS, get_display_name
from utils.ui_utils import (add_tooltip, StatusBar, ScrollableFrame, BLUE,
                            RED, GREEN, BACKGROUND, DARK_BACKGROUND,
                            LIGHT_TEXT)
# Import from our own modules
from views.dialogs import ItemSelectorDialog


class StdoutRedirector:

    def __init__(self, gui_write_func, orig_stream):
        self.gui_write_func = gui_write_func
        self.orig_stream = orig_stream

    def write(self, text):
        self.orig_stream.write(text)
        self.orig_stream.flush()
        if text.strip():
            self.gui_write_func(text)

    def flush(self):
        self.orig_stream.flush()


class MainWindow:
    """Main window view for Ouija Seed Finder application"""

    # Template mapping dictionary for converting between UI-friendly names and template filenames
    template_mapping = {
        "Default": "ouija_template",
        "Erratic Ranks": "ouija_template_erratic_ranks",
        "Erratic Suits": "ouija_template_erratic_suits",
        "Anaglyph": "ouija_template_anaglyph",
        "Natural Negatives": "ouija_template_negatives",
        "Legendary Negatives": "ouija_template_negative_legendaries",
    }

    def __init__(self, root, controller):
        """Initialize the main window
        
        Args:
            root: The root Tk window
            controller: The application controller
        """
        self.root = root
        self.controller = controller
        self.start_time = None  # Ensure this always exists
        self.search_running = False
        self._search_start_time = None

        # Define table font attributes early
        self.table_font_family = "m6x11"
        self.table_font_size = 13  # Updated font size

        # Register this view with the controller
        controller.register_view(self)

        # Apply custom font
        self.setup_font()

        # Create main layout frames
        self.create_layout()

        # Create widgets in each section
        self.create_config_section()
        self.create_criteria_section()
        self.create_run_settings_section()
        self.create_results_section()        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add startup logging
        print("🚀 Ouija UI initialized successfully!")
        print(f"🎯 Python executable: {sys.executable}")
        print(f"🔧 Frozen executable: {getattr(sys, 'frozen', False)}")
        
        # Log if we're running in a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            print("📦 Running as PyInstaller executable")        # Initialize the UI with current settings
        self.update_config_display()
        self.update_criteria_display()

        # Connect to database if config was loaded
        if self.controller.config_model.loaded_config_path:
            self.controller.database_model.connect(
                self.controller.config_model.loaded_config_path)

        self.controller.refresh_results()

        # Add to __init__
        self._debounce_table_update_id = None
        
        # Check kernel status and update button accordingly
        self.update_kernel_button_state()
        self._pending_table_df = None
        self._status_update_id = None
        self._last_results_count = 0
        self._search_results_count = 0

        # Redirect stdout and stderr to both terminal and GUI
        # sys.stdout = StdoutRedirector(self.write_to_console, sys.__stdout__)
        # sys.stderr = StdoutRedirector(self.write_to_console, sys.__stderr__)

        self.latest_df = None  # Initialize latest_df to avoid attribute errors

    def setup_font(self):
        """Set up custom font for the application with slightly larger size"""
        # Use system monospace font as fallback if m6x11 not available
        self.custom_font = font.nametofont("TkDefaultFont")
        self.custom_font.configure(family="m6x11", size=18)
        self.root.option_add("*Font", self.custom_font)

        # Define table font attributes with slightly larger size
        self.table_font_family = "m6x11"
        # Increase table font size from 12 to 13
        self.table_font_size = 16

    def create_layout(self):
        """Create the main layout with proper 50/50 split"""
        # Create status bar first to ensure it stays on top of all elements
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.lift()  # Ensure it stays on top

        # Main container frame with proper padding
        self.main_container = tk.Frame(self.root, bg=BACKGROUND)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)        # Create top section with fixed height (not based on window size)
        self.settings_frame = tk.Frame(self.main_container,
                                       bg=BACKGROUND,
                                       height=400)  # Fixed height in pixels
        self.settings_frame.pack(side=tk.TOP,
                                 fill=tk.X,  # Only fill horizontally, not vertically
                                 expand=False,
                                 pady=(0, 5))
        self.settings_frame.pack_propagate(False)  # Fix the height        # Create three columns with fixed left/middle and expandable right column
        self.left_column = tk.Frame(self.settings_frame,
                                    bg=BACKGROUND,
                                    width=350)  # Fixed width for config section
        self.left_column.pack(side=tk.LEFT,
                              fill=tk.Y,  # Only fill vertically, not horizontally
                              expand=False,  # Don't expand horizontally
                              padx=(0, 5))
        self.left_column.pack_propagate(False)  # Prevent content from resizing the column

        self.middle_column = tk.Frame(self.settings_frame,
                                      bg=BACKGROUND,
                                      width=400)  # Fixed width for criteria section
        self.middle_column.pack(side=tk.LEFT,
                                fill=tk.Y,  # Only fill vertically, not horizontally
                                expand=False,  # Don't expand horizontally
                                padx=5)
        self.middle_column.pack_propagate(False)  # Prevent content from resizing the column

        self.right_column = tk.Frame(self.settings_frame,
                                     bg=BACKGROUND)  # No fixed width - will expand
        self.right_column.pack(side=tk.LEFT,
                               fill=tk.BOTH,  # Fill both directions
                               expand=True,  # Expand to take remaining space
                               padx=(5, 0))# Bottom section (remaining height)
        self.bottom_frame = tk.Frame(self.main_container, bg=BACKGROUND)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def create_config_section(self):
        """Create the configuration section with optimized spacing"""
        # Config frame with improved padding
        self.config_frame = tk.LabelFrame(self.left_column,
                                          text="Configuration",
                                          padx=5,
                                          pady=5,
                                          bg=BACKGROUND,
                                          fg=LIGHT_TEXT,
                                          font=("m6x11", 14))
        self.config_frame.pack(fill=tk.X, expand=False, padx=2, pady=(2, 5))

        # Config name entry with better padding
        self.config_name_var = tk.StringVar()
        self.config_name_entry = tk.Entry(self.config_frame,
                                          textvariable=self.config_name_var,
                                          font=("m6x11", 13))
        self.config_name_entry.pack(fill=tk.X, pady=5)
        self.config_name_var.trace_add("write", self.on_config_name_changed)

        # Button rows with improved spacing
        button_frame = tk.Frame(self.config_frame, bg=BACKGROUND)
        button_frame.pack(fill=tk.X, pady=5)

        self.save_button = tk.Button(button_frame,
                                     text="Save",
                                     command=self.on_save_direct,
                                     bg=BLUE,
                                     fg=LIGHT_TEXT,
                                     font=("m6x11", 12))
        self.save_button.pack(side=tk.LEFT,
                              expand=True,
                              fill=tk.X,
                              padx=(0, 5))

        self.save_as_button = tk.Button(button_frame,
                                        text="Save As",
                                        command=self.on_save_as,
                                        bg=BLUE,
                                        fg=LIGHT_TEXT,
                                        font=("m6x11", 12))
        self.save_as_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.load_button = tk.Button(button_frame,
                                     text="Load",
                                     command=self.on_load_config,
                                     bg=BLUE,
                                     fg=LIGHT_TEXT,
                                     font=("m6x11", 12))
        self.load_button.pack(side=tk.RIGHT,
                              expand=True,
                              fill=tk.X,
                              padx=(5, 0))

        # ===== Search Settings Frame =====
        self.search_settings_frame = tk.LabelFrame(self.left_column,
                                                   text="Deck Settings",
                                                   padx=2,
                                                   pady=2,
                                                   bg=BACKGROUND,
                                                   fg=LIGHT_TEXT,
                                                   font=("m6x11", 14))
        self.search_settings_frame.pack(fill=tk.BOTH,
                                        expand=True,
                                        padx=1,
                                        pady=1)

        # Create a grid layout for more compact controls
        row = 0

        # Deck label and dropdown
        tk.Label(self.search_settings_frame,
                 text="Deck:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=row,
                                          column=0,
                                          sticky="w",
                                          pady=2)
        self.deck_var = tk.StringVar()
        self.deck_dropdown = ttk.Combobox(self.search_settings_frame,
                                          textvariable=self.deck_var,
                                          state="readonly",
                                          font=("m6x11", 12))
        self.deck_dropdown['values'] = AVAILABLE_ITEMS["Decks"]
        self.deck_dropdown.grid(row=row, column=1, sticky="ew", pady=2)
        self.deck_dropdown.bind("<<ComboboxSelected>>", self.on_deck_changed)
        row += 1

        # Stake label and dropdown
        tk.Label(self.search_settings_frame,
                 text="Stake:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=row,
                                          column=0,
                                          sticky="w",
                                          pady=2)
        self.stake_var = tk.StringVar()
        self.stake_dropdown = ttk.Combobox(self.search_settings_frame,
                                           textvariable=self.stake_var,
                                           state="readonly",
                                           font=("m6x11", 12))
        self.stake_dropdown['values'] = AVAILABLE_ITEMS["Stakes"]
        self.stake_dropdown.grid(row=row, column=1, sticky="ew", pady=2)
        self.stake_dropdown.bind("<<ComboboxSelected>>", self.on_stake_changed)
        row += 1

        # Template dropdown
        tk.Label(self.search_settings_frame,
                 text="Template:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=row,
                                          column=0,
                                          sticky="w",
                                          pady=2)
        self.template_var = tk.StringVar()
        self.template_dropdown = ttk.Combobox(self.search_settings_frame,
                                              textvariable=self.template_var,
                                              state="readonly",
                                              font=("m6x11", 12))
        # Convert dictionary keys to list to avoid dict_keys object
        self.template_dropdown['values'] = list(self.template_mapping.keys())
        self.template_dropdown.grid(row=row, column=1, sticky="ew", pady=2)
        self.template_dropdown.bind("<<ComboboxSelected>>",
                                    self.on_template_changed)
        row += 1

        # --- Extra Scoring Settings ---
        scoring_frame = tk.LabelFrame(
            self.left_column,
            text="Extra Scoring Settings",
            padx=5,
            pady=5,
            bg=BACKGROUND,
            fg=LIGHT_TEXT,
            font=("m6x11", 13))
        scoring_frame.pack(fill=tk.X, expand=False, padx=2, pady=(2, 5))

        self.score_natural_negatives_var = tk.BooleanVar(value=True)
        self.score_desired_negatives_var = tk.BooleanVar(value=True)

        self.natural_neg_check = tk.Checkbutton(
            scoring_frame,
            text="Column for Natural Negative",
            variable=self.score_natural_negatives_var,
            selectcolor=BACKGROUND,
            activeforeground=LIGHT_TEXT,
            foreground=LIGHT_TEXT,
            background=BACKGROUND,
            activebackground=DARK_BACKGROUND,
            anchor="w",
            font=("m6x11", 12),
            command=self.on_score_natural_negatives_changed)
        self.natural_neg_check.pack(anchor="w")

        self.desired_negative_check = tk.Checkbutton(
            scoring_frame,
            text="Column for Desired Negative",
            variable=self.score_desired_negatives_var,
            selectcolor=BACKGROUND,
            activeforeground=LIGHT_TEXT,
            foreground=LIGHT_TEXT,
            background=BACKGROUND,
            activebackground=DARK_BACKGROUND,
            anchor="w",
            font=("m6x11", 12),
            command=self.on_score_desired_negatives_changed)
        self.desired_negative_check.pack(anchor="w")

        # Create a grid section within scoring_frame for the remaining controls
        grid_section = tk.Frame(scoring_frame, bg=BACKGROUND)
        grid_section.pack(fill=tk.X, pady=(10, 0))

        # Configure grid section
        grid_section.columnconfigure(1, weight=1)

        row = 0

        # Seed label and entry
        tk.Label(grid_section,
                 text="Starting Seed:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=row,
                                          column=0,
                                          sticky="w",
                                          pady=2)

        seed_entry_frame = tk.Frame(grid_section, bg=BACKGROUND)
        seed_entry_frame.grid(row=row, column=1, sticky="ew", pady=2)
        seed_entry_frame.columnconfigure(0, weight=1)

        self.starting_seed_var = tk.StringVar()
        self.starting_seed_entry = tk.Entry(
            seed_entry_frame,
            textvariable=self.starting_seed_var,
            font=("m6x11", 12))
        self.starting_seed_entry.grid(row=0, column=0, sticky="ew")

        random_seed_button = tk.Button(seed_entry_frame,
                                       text="🎲",
                                       bg=GREEN,
                                       fg=LIGHT_TEXT,
                                       command=self.on_random_seed,
                                       font=("m6x11", 12),
                                       width=6)
        random_seed_button.grid(row=0, column=1, padx=(5, 0))
        row += 1

        # Search size dropdown
        tk.Label(grid_section,
                 text="Search Size:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=row,
                                          column=0,
                                          sticky="w",
                                          pady=2)

        self.number_of_seeds_var = tk.StringVar()
        self.number_of_seeds_dropdown = ttk.Combobox(
            grid_section,
            textvariable=self.number_of_seeds_var,
            state="readonly",
            font=("m6x11", 12))

        self.number_of_seeds_dropdown['values'] = [
            "All", "1 Single Seed", "1K", "100K", "1M", "100M", "1B", "10B",
            "100B"
        ]
        self.number_of_seeds_dropdown.grid(row=row, column=1, sticky="ew", pady=2)
        self.number_of_seeds_dropdown.bind("<<ComboboxSelected>>",
                                           self.on_number_of_seeds_changed)

        # Configure column weights
        self.search_settings_frame.columnconfigure(1, weight=1)

        # Make the grid rows more compact
        for row in range(4):  # Assuming we have about 8 rows in the grid
            self.search_settings_frame.grid_rowconfigure(
                row, pad=1)  # Minimal row padding

    def create_criteria_section(self):
        """Create the criteria selection section with improved spacing"""
        self.criteria_frame = tk.LabelFrame(self.middle_column,
                                            text="Search Criteria",
                                            padx=5,
                                            pady=5,
                                            bg=BACKGROUND,
                                            fg=LIGHT_TEXT,
                                            font=("m6x11", 14))
        self.criteria_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Criteria section - split into left (deck settings) and right (criteria list)
        criteria_left = tk.Frame(self.criteria_frame, bg=BACKGROUND)
        criteria_left.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        criteria_right = tk.Frame(self.criteria_frame, bg=BACKGROUND)
        criteria_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Criteria buttons in right side
        self.add_criteria_frame = tk.Frame(criteria_right, bg=BACKGROUND)
        self.add_criteria_frame.pack(fill=tk.X, pady=5)

        # Add criteria buttons
        tk.Button(self.add_criteria_frame,
                  text="+Joker",
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12),
                  command=lambda: self.on_add_need("Jokers")).pack(
            side=tk.LEFT, padx=4)
        tk.Button(self.add_criteria_frame,
                  text="+Tarot",
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12),
                  command=lambda: self.on_add_need("Tarots")).pack(
            side=tk.LEFT, padx=4)
        tk.Button(self.add_criteria_frame,
                  text="+Spectral",
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12),
                  command=lambda: self.on_add_need("Spectrals")).pack(
            side=tk.LEFT, padx=4)
        tk.Button(self.add_criteria_frame,
                  text="+Tag",
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12),
                  command=lambda: self.on_add_need("Tags")).pack(side=tk.LEFT,
                                                                 padx=4)
        tk.Button(self.add_criteria_frame,
                  text="+Voucher",
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12),
                  command=lambda: self.on_add_need("Vouchers")).pack(
            side=tk.LEFT, padx=4)
        tk.Button(self.add_criteria_frame,
                  text="+Rank",
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12),
                  command=lambda: self.on_add_need("Ranks")).pack(side=tk.LEFT,
                                                                  padx=4)
        tk.Button(self.add_criteria_frame,
                  text="+Suit",
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12),
                  command=lambda: self.on_add_need("Suits")).pack(side=tk.LEFT,
                                                                  padx=4)

        # Criteria list
        self.criteria_list = tk.Listbox(criteria_right,
                                        bg=DARK_BACKGROUND,
                                        fg=LIGHT_TEXT,
                                        selectmode=tk.SINGLE,
                                        font=("m6x11", 12))
        self.criteria_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Criteria action buttons
        self.criteria_buttons_frame = tk.Frame(criteria_right, bg=BACKGROUND)
        self.criteria_buttons_frame.pack(fill=tk.X, pady=5)

        tk.Button(self.criteria_buttons_frame,
                  text="Clear All",
                  command=self.on_clear_all,
                  bg=RED,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12)).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.criteria_buttons_frame,
                  text="Remove Selected",
                  command=self.on_remove_selected,
                  bg=RED,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12)).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.criteria_buttons_frame,
                  text="Edit Selected",
                  command=self.on_edit_selected,
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12)).pack(side=tk.RIGHT, padx=5)

    def create_run_settings_section(self):
        """Create the run settings section with the button properly positioned"""
        self.run_settings_frame = tk.LabelFrame(self.right_column,
                                                text="Run",
                                                padx=3,
                                                pady=3,
                                                bg=BACKGROUND,
                                                fg=LIGHT_TEXT,
                                                font=("m6x11", 14))
        self.run_settings_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Create a container frame with proper layout
        run_container = tk.Frame(self.run_settings_frame, bg=BACKGROUND)
        run_container.pack(fill=tk.BOTH, expand=True)

        # Configure rows to ensure proper distribution
        run_container.grid_rowconfigure(
            0, weight=1)  # Console gets all extra space
        run_container.grid_rowconfigure(
            1, weight=0)  # Button row has fixed height
        run_container.grid_rowconfigure(
            2, weight=0)  # Button row has fixed height
        run_container.grid_columnconfigure(0, weight=1)  # Full width

        # Console output at top now, using grid
        console_frame = tk.Frame(run_container, bg=BACKGROUND)
        console_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.output_text = tk.Text(console_frame,
                                   wrap=tk.WORD,
                                   bg=DARK_BACKGROUND,
                                   fg=LIGHT_TEXT,
                                   font=("m6x11", 13),
                                   insertbackground='white')
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Redirect stdout and stderr to both terminal and GUI
        # sys.stdout = StdoutRedirector(self.write_to_console, sys.__stdout__)
        # sys.stderr = StdoutRedirector(self.write_to_console, sys.__stderr__)        # GPU and Cutoff settings frame between console and buttons
        gpu_frame = tk.Frame(run_container, bg=BACKGROUND, height=100)
        gpu_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(5, 0))
        gpu_frame.grid_propagate(False)  # Prevent shrinking

        # Configure grid for the GPU frame
        gpu_frame.columnconfigure(1,
                                  weight=1)  # Make dropdown column expandable

        # GPU Batch dropdown
        tk.Label(gpu_frame,
                 text="GPU Batch Size:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=0,
                                          column=0,
                                          sticky="w",
                                          pady=2,
                                          padx=(0, 5))

        self.gpu_batch_var = tk.StringVar()
        self.gpu_batch_dropdown = ttk.Combobox(gpu_frame,
                                               textvariable=self.gpu_batch_var,
                                               state="readonly",
                                               font=("m6x11", 12))
        self.gpu_batch_dropdown['values'] = [
            "1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1024",
            "2048", "4096", "8192"
        ]
        row = 0
        self.gpu_batch_dropdown.grid(row=row, column=1, sticky="ew", pady=2)
        self.gpu_batch_dropdown.bind("<<ComboboxSelected>>",
                                     self.on_gpu_batch_changed)
        row += 1

        # Thread groups
        tk.Label(gpu_frame,
                 text="Thread Groups:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=row,
                                          column=0,
                                          sticky="w",
                                          pady=2)

        self.thread_groups_var = tk.StringVar()
        self.thread_groups_dropdown = ttk.Combobox(
            gpu_frame,
            textvariable=self.thread_groups_var,
            state="readonly",
            font=("m6x11", 12))
        self.thread_groups_dropdown.grid(row=row,
                                         column=1,
                                         sticky="ew",
                                         pady=2)

        self.thread_groups_dropdown['values'] = [
            "Single", "16", "32", "64", "128", "256"
        ]
        self.thread_groups_dropdown.bind("<<ComboboxSelected>>",
                                         self.on_thread_groups_changed)
        row += 1

        # Cutoff entry
        tk.Label(gpu_frame,
                 text="Cutoff Score:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).grid(row=row,
                                          column=0,
                                          sticky="w",
                                          pady=2,
                                          padx=(0, 5))
        row += 1

        # Create a frame to hold both the cutoff entry and auto checkbox
        cutoff_frame = tk.Frame(gpu_frame, bg=BACKGROUND)
        cutoff_frame.grid(row=2, column=1, sticky="ew", pady=2)
        cutoff_frame.columnconfigure(0,
                                     weight=1)  # Entry takes available space

        self.cutoff_var = tk.StringVar()
        self.cutoff_entry = tk.Entry(cutoff_frame,
                                     textvariable=self.cutoff_var,
                                     font=("m6x11", 12))
        self.cutoff_entry.grid(row=0, column=0, sticky="ew")

        # Add Auto checkbox
        self.auto_cutoff_var = tk.BooleanVar(value=False)
        self.auto_cutoff_check = tk.Checkbutton(
            cutoff_frame,
            text="Auto?",
            variable=self.auto_cutoff_var,
            bg=BACKGROUND,
            selectcolor=BACKGROUND,
            fg=LIGHT_TEXT,
            activebackground=BACKGROUND,
            anchor="w",
            font=("m6x11", 12),
            command=self.on_auto_cutoff_changed)
        self.auto_cutoff_check.grid(row=0, column=2)
        self.cutoff_var.trace_add("write", self.on_cutoff_changed)

        # Button at bottom with fixed height
        button_frame = tk.Frame(run_container, bg=BACKGROUND, height=50)
        button_frame.grid(row=2, column=0, sticky="sew", padx=0, pady=(5, 0))
        button_frame.grid_propagate(False)  # Prevent shrinking
        self.run_button = tk.Button(button_frame,
                                    text="Let Jimbo Cook!",
                                    command=self.on_run_search,
                                    bg=BLUE,
                                    fg=LIGHT_TEXT,
                                    font=("m6x11", 16))
        self.run_button.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_results_section(self):
        """Create results table section with optimized spacing"""
        self.results_frame = tk.LabelFrame(self.bottom_frame,
                                           text="Results",
                                           padx=2,
                                           pady=2,
                                           bg=BACKGROUND,
                                           fg=LIGHT_TEXT,
                                           font=("m6x11", 14))
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Add Refresh/Delete Everything buttons
        button_row = tk.Frame(self.results_frame, bg=BACKGROUND)
        button_row.pack(fill=tk.X, pady=(0, 5))

        # Left side buttons
        left_buttons = tk.Frame(button_row, bg=BACKGROUND)
        left_buttons.pack(side=tk.LEFT)
        tk.Button(
            left_buttons,
            text="Refresh",
            bg=GREEN,
            fg=LIGHT_TEXT,
            font=("m6x11", 12),
            width=10,
            command=self.on_refresh_results,
        ).pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(
            left_buttons,
            text="Export...",
            bg=BLUE,
            fg=LIGHT_TEXT,
            font=("m6x11", 12),
            width=10,
            command=self.on_export_results,
        ).pack(side=tk.LEFT, padx=(4, 4))

        tk.Button(
            left_buttons,
            text="Delete Everything",
            bg=RED,
            fg=LIGHT_TEXT,
            font=("m6x11", 12),
            width=16,
            command=self.on_delete_all_results,
        ).pack(side=tk.LEFT, padx=(4, 0))

        # Right side - Secret button
        right_buttons = tk.Frame(button_row, bg=BACKGROUND)
        right_buttons.pack(side=tk.RIGHT)

        # The secret button
        self.secret_button = tk.Button(
            right_buttons,
            text="Click Me for a fun time",
            bg="#FF6F61",  # Coral color
            fg="#020403",  # Dark 
            font=("m6x11", 10),
            command=self.on_secret_button_clicked,
        )
        self.secret_button.pack(side=tk.RIGHT, padx=2)

        # Hidden fun buttons frame (initially hidden)
        self.fun_buttons_frame = tk.Frame(button_row, bg=BACKGROUND)
        # Don't pack it initially - it will be shown when secret button is clicked

        # Create the fun category buttons
        self.lol_button = tk.Button(
            self.fun_buttons_frame,
            text="LOL Seeds 😂",
            bg="#FFD93D",  # Yellow
            fg="black",
            font=("m6x11", 10),
            command=lambda: self.run_fun_seed_search("LOL"),
        )
        self.lol_button.pack(side=tk.LEFT, padx=2)

        self.gross_button = tk.Button(
            self.fun_buttons_frame,
            text="GROSS Seeds 🤮",
            bg="#6BCF7F",  # Green
            fg="black",
            font=("m6x11", 10),
            command=lambda: self.run_fun_seed_search("GROSS"),
        )
        self.gross_button.pack(side=tk.LEFT, padx=2)

        self.nsfw_button = tk.Button(
            self.fun_buttons_frame,
            text="NSFW Seeds 🍆",
            bg="#9D4EDD",  # Purple
            fg=LIGHT_TEXT,
            font=("m6x11", 10),
            command=lambda: self.run_fun_seed_search("NSFW"),
        )
        self.nsfw_button.pack(side=tk.LEFT, padx=2)

        self.cool_button = tk.Button(
            self.fun_buttons_frame,
            text="COOL Seeds 😎",
            bg="#4ECDC4",  # Teal
            fg="black",
            font=("m6x11", 10),
            command=lambda: self.run_fun_seed_search("COOL"),
        )
        self.cool_button.pack(side=tk.LEFT, padx=2)

        # Create a dedicated container frame for the table to isolate grid geometry manager
        table_container = tk.Frame(self.results_frame, bg=BACKGROUND)
        table_container.pack(fill=tk.BOTH, expand=True)

        # Table with no wasted space
        self.pt = Table(table_container,
                        dataframe=pd.DataFrame(),
                        showtoolbar=False,
                        showstatusbar=False,
                        font=self.table_font_family,
                        fontsize=self.table_font_size,
                        headerfont=(self.table_font_family,
                                    self.table_font_size))

        # Show the table with tight packing
        self.pt.show()
        # Set default precision for numeric columns
        if not hasattr(self.pt, 'columnformats'):
            self.pt.columnformats = {}
            self.pt.columnformats['default'] = {'precision': 0}

            self.latest_df = None

            self._setup_initial_table()

    def _adjust_table_column_widths(self):
        """Adjusts column widths to show full headers and make Seed column 50% larger."""
        if not hasattr(self.pt, 'model') or self.pt.model is None or \
                not hasattr(self.pt.model, 'df') or self.pt.model.df is None:
            return

        # Initialize colwidths if not present
        if not hasattr(self.pt, 'colwidths'):
            self.pt.colwidths = {}

        # Get the column list
        columns = self.pt.model.df.columns.tolist()        
        # Calculate header width based on column name length with minimum width
        for col in columns:
            display_name = str(col)
            header_width = len(display_name) * 11

            # Special handling for Seed column - make 50% wider
            if display_name == 'Seed':
                header_width = header_width * 2.5
            
            # Ensure minimum width for single character columns (like "2", "#", etc.)
            # This prevents columns from being too narrow to see values
            min_width = 60  # Minimum 60 pixels for readability
            header_width = max(header_width, min_width)

            # Set the width, use max of calculated width or existing width
            if col in self.pt.colwidths:
                self.pt.colwidths[col] = max(self.pt.colwidths[col],
                                             header_width)
            else:
                self.pt.colwidths[col] = header_width

        # Update column widths in pandastable
        self.pt.columnwidths = self.pt.colwidths.copy()        
        # Redraw the table
        self.pt.redraw()

    def _setup_initial_table(self):
        """Set up the results table to refresh immediately and then every 400ms."""
        self._refresh_timer_id = None
        
        def refresh_loop():
            if self._refresh_timer_id is not None: 
                 # Only continue if not cancelled
                self.refresh_results_table()
                self._refresh_timer_id = self.root.after(400, refresh_loop)

        self.refresh_results_table()
        self._refresh_timer_id = self.root.after(400, refresh_loop)

    def update_results_table(self, dataframe):
        """Update results table with new data and handle auto cutoff if enabled"""
        self.latest_df = dataframe
        if dataframe is not None and not dataframe.empty:
            # Ensure all columns are of a robust type for display
            display_df = dataframe.copy()
            for col in display_df.columns:
                if col == "Seed":
                    # Convert Seed column to string without padding - Balatro seeds should remain as-is
                    display_df[col] = display_df[col].astype(str)
                elif pd.api.types.is_integer_dtype(display_df[col]):
                    display_df[col] = display_df[col].fillna(0)  # Fill NaN for integers
                elif pd.api.types.is_float_dtype(display_df[col]):
                    display_df[col] = display_df[col].fillna(0).map(lambda x: f'{x:.2f}')  # Format floats only

            self.pt.model.df = display_df
        else:
            self.pt.model.df = pd.DataFrame()

        try:
            self.pt.redraw()
            self._adjust_table_column_widths()
        except (IndexError, AttributeError) as e:
            # Handle IndexError when clicking on empty table or AttributeError for missing data
            # This prevents crashes when the pandastable tries to access non-existent rows
            pass
        self._search_results_count = len(dataframe) if dataframe is not None else 0

    def refresh_results_table(self):
        """Reload the results table from the database and update the UI."""
        from models.database_model import DatabaseModel
        db_model = DatabaseModel()

        # Try to get the current config path from the controller first
        config_path = self.controller.get_current_config_path()

        # Fall back to last saved config if needed
        if not config_path:
            try:
                with open('user.ouija.conf', 'r') as f:
                    user_conf = json.load(f)
                config_path = user_conf.get('last_config_path')
            except Exception:
                config_path = None

        if config_path and db_model.connect(config_path) and db_model.table_exists():
            df = db_model.get_dataframe()
            if df is not None and (self.latest_df is None or not df.equals(self.latest_df)):
                self.update_results_table(df)
        else:
            if self.latest_df is not None:
                self.update_results_table(pd.DataFrame())

    def set_search_running(self, is_running):
        """Update the UI state when search is running or stops
        
        Args:
            is_running: Boolean indicating if search is running
        """
        if self.search_running == is_running:
            return  # Prevent duplicate finish/stop messages        self.search_running = is_running
        if is_running:
            self.run_button.config(text="STOP SEARCH", bg=RED)
            self._search_start_time = time.time()
            self._search_results_count = 0
        else:
            # Check kernel status when search stops to set appropriate button text
            self.update_kernel_button_state()
            if self._search_start_time is not None:
                elapsed = time.time() - self._search_start_time
                self.write_to_console(
                    f"Search finished. Elapsed time: {elapsed:.2f} seconds\n", color="white")
            self._search_start_time = None

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
                if not hasattr(self, '_color_tags_configured'):
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

    def set_status(self, text):        
        """Set status bar text

        Args:
            text: Status text to display
        """
        self.status_bar.set_status(text)

    def set_metrics(self, text):
        """Set metrics text in the status bar (right side)
        
        Args:
            text: Metrics text to display
        """
        # Text should already have ⏱️ from the search controller
        self.status_bar.set_metrics(text)

    def get_available_items(self):
        """Get the available items by category
        
        Returns:
            Dictionary mapping category names to lists of item names
        """
        return AVAILABLE_ITEMS

    def validate_seed(self, new_value):
        """Validate the seed input
        
        Args:
            new_value: New value to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Allow empty (will default to random) or "random"
        if new_value == "" or new_value.lower() == "random":
            return True

        # Otherwise only allow valid seed characters and max length 8
        seed_dictionary = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return len(new_value) <= 8 and all(char in seed_dictionary
                                           for char in new_value.upper())

    def on_config_name_changed(self, *args):
        """Handle configuration name changes"""
        self.controller.set_config_name(self.config_name_var.get())

    def on_deck_changed(self, event=None):
        """Handle deck selection changes"""
        self.controller.set_setting('deck', self.deck_var.get())

    def on_stake_changed(self, event=None):
        """Handle stake selection changes"""
        self.controller.set_setting('stake', self.stake_var.get())

    def on_thread_groups_changed(self, event=None):
        """Handle thread groups selection changes"""
        self.controller.set_setting('thread_groups',
                                    self.thread_groups_var.get())

    def on_cutoff_changed(self, *args):
        """Handle cutoff score changes and sync auto checkbox if needed"""
        value = self.cutoff_var.get()
        if value.strip().lower() == "auto":
            if not self.auto_cutoff_var.get():
                self.auto_cutoff_var.set(True)
            self.cutoff_entry.config(state="disabled")
        else:
            # Save last manual value for restoration
            self._last_manual_cutoff = value
            if self.auto_cutoff_var.get():
                self.auto_cutoff_var.set(False)
            self.cutoff_entry.config(state="normal")
        self.controller.set_setting('cutoff', value)

    def on_gpu_batch_changed(self, event=None):
        """Handle GPU batch size selection changes"""
        self.controller.set_setting('gpu_batch', self.gpu_batch_var.get())

    def on_template_changed(self, event=None):
        """Handle template selection changes"""
        # Get the friendly name from the dropdown
        friendly_name = self.template_var.get()
        # Get the actual template filename from our mapping
        template_name = self.template_mapping.get(friendly_name,
                                                  "ouija_template")
        # Update the setting with the actual template filename
        self.controller.set_setting('template', template_name)
        self.update_config_display()

    def on_random_seed(self):
        """Set the search seed to random, Ouija-CLI.exe handles this"""
        self.starting_seed_entry.delete(0, tk.END)
        self.starting_seed_entry.insert(0, "random")

    def on_number_of_seeds_changed(self, event=None):
        """Handle number of seeds selection changes"""
        self.controller.set_setting('number_of_seeds',
                                    self.number_of_seeds_var.get())

    def on_save_direct(self):
        """Save directly to {config_name}.ouija.json in the config directory, no prompt."""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            self.set_status("Please enter a configuration name before saving.")
            return
        file_name = config_name.lower().replace(" ", "_") + ".ouija.json"
        file_path = os.path.join(self.controller.config_model.CONFIG_DIR,
                                 file_name)
        self.controller.save_config(file_path)

    def on_save_as(self):
        """Prompt user for file path, pre-filling with config name, and save there."""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            self.set_status("Please enter a configuration name before saving.")
            return
        file_name = config_name.lower().replace(" ", "_") + ".ouija.json"
        file_path = filedialog.asksaveasfilename(
            initialdir=self.controller.config_model.CONFIG_DIR,
            initialfile=file_name,
            defaultextension=".ouija.json",
            filetypes=[("Ouija JSON files", "*.ouija.json"),
                       ("All files", "*.*")])
        if file_path:
            self.controller.save_config(file_path)

    def on_load_config(self):
        """Load a configuration"""
        file_path = filedialog.askopenfilename(
            initialdir=self.controller.config_model.CONFIG_DIR,
            title="Load Configuration",
            filetypes=[("Ouija JSON files", "*.ouija.json"),
                       ("All files", "*.*")])

        if file_path:
            self.controller.load_config(file_path)
            self.update_config_display(
            )  # Add this to refresh config UI elements
            self.update_criteria_display()  # Add this to refresh criteria list
            self.controller.refresh_results(
            )  # Refresh results table once after UI updates

    def on_add_need(self, category):
        """Add a need from the selected category"""
        # The True argument indicates to the dialog that the initial context is a 'Need'
        result = ItemSelectorDialog.show_dialog(self.root,
                                                f"Select Need: {category}",
                                                category, True)
        if result:
            item_payload = result["payload"]

            if result["is_need"]:
                # If it's a Rank or Suit Need, explicitly set desireByAnte to 1 as per requirements
                if result["type"] == "RankOrSuit":
                    item_payload["desireByAnte"] = 1
                # For Standard needs, desireByAnte should already be in item_payload if ante > 0
                self.controller.add_need(item_payload)
            else:
                # If is_need is False (either Rank/Suit selected as Want, or Standard item with Ante 0)
                # it's treated as a Want. Ensure desireByAnte is not in payload for wants if it was 0.
                if "desireByAnte" in item_payload and item_payload[
                    "desireByAnte"] == 0:
                    del item_payload["desireByAnte"]
                self.controller.add_want(item_payload)

            self.update_criteria_display()  # Refresh list after adding

    def on_add_want(self, category):
        """Add a want from the selected category"""
        # The False argument indicates to the dialog that the initial context is a 'Want'
        result = ItemSelectorDialog.show_dialog(self.root,
                                                f"Select Want: {category}",
                                                category, False)
        if result:
            item_payload = result["payload"]
            # Ensure desireByAnte is not part of a want payload,
            # especially if it might have been added and set to 0 by the dialog for standard items.
            if "desireByAnte" in item_payload:
                del item_payload["desireByAnte"]
            self.controller.add_want(item_payload)
            self.update_criteria_display()  # Refresh list after adding

    def on_remove_selected(self):
        """Remove the selected criterion"""
        selected_indices = self.criteria_list.curselection()
        if selected_indices:
            self.controller.remove_criterion(selected_indices[0])

    def on_edit_selected(self):
        """Edit the selected criterion"""
        selected_indices = self.criteria_list.curselection()
        if not selected_indices:
            return

        # Get the selected index and determine if it's a need or a want
        index = selected_indices[0]
        needs_count = len(self.controller.config_model.needs_list)

        is_need = index < needs_count

        # Get the criterion data
        if is_need:
            criterion = self.controller.config_model.needs_list[index]
            category = self.get_category_for_item(criterion["value"])
        else:
            criterion = self.controller.config_model.wants_list[index -
                                                                needs_count]
            category = self.get_category_for_item(criterion["value"])

        # Show the dialog with the existing item data
        result = ItemSelectorDialog.show_dialog(
            self.root,
            f"Edit {'Need' if is_need else 'Want'}: {category}",
            category,
            is_need,
            edit_mode=True,
            existing_item=criterion)

        if result:
            item_payload = result["payload"]

            # Handle Need/Want changes
            if result["is_need"] != is_need:
                # Need/Want type changed - remove old and add new
                self.controller.remove_criterion(index)

                if result["is_need"]:
                    self.controller.add_need(item_payload)
                else:
                    # Ensure desireByAnte is removed for wants
                    if "desireByAnte" in item_payload:
                        del item_payload["desireByAnte"]
                    self.controller.add_want(item_payload)
            else:
                # Same type, just update
                self.controller.edit_criterion(index, item_payload)

            self.update_criteria_display()

    def get_category_for_item(self, item_value):
        """Determine the category for an item based on its value
        
        Args:
            item_value: The internal item value
            
        Returns:
            The category name
        """
        # Check each category for the item value
        from utils.game_data import AVAILABLE_ITEMS, get_display_name

        item_display_name = get_display_name(item_value)

        for category, items in AVAILABLE_ITEMS.items():
            if item_display_name in items:
                return category

        # Default to Jokers if not found
        return "Jokers"

    def on_clear_all(self):
        """Clear all criteria"""
        if messagebox.askyesno("Confirm",
                               "Are you sure you want to clear all criteria?"):
            self.controller.clear_all_criteria()

    def update_kernel_button_state(self):
        """Check kernel status and update the run button text accordingly"""
        try:
            if self.controller.is_kernel_build_needed():
                self.run_button.config(text="Finish GPU Setup...", bg="#FF8C00")  # Orange color
                self.set_status("⚙️ GPU kernel setup required - click 'Finish GPU Setup...' to compile OpenCL kernels")
            else:
                self.run_button.config(text="Let Jimbo Cook!", bg=BLUE)
                self.set_status("✅ GPU kernels ready - ready to search!")
        except Exception as e:
            self.write_to_console(f"⚠️ Warning: Could not check kernel status: {e}\n", color="red")            # Default to normal state if we can't check
            self.run_button.config(text="Let Jimbo Cook!", bg=BLUE)

    def run_kernel_build(self):
        """Run kernel build process with UI feedback"""
        def on_build_complete():
            """Callback when kernel build completes"""
            self.write_to_console("🎯 GPU kernel setup complete! Ready to search.\n", color="green")
            self.update_kernel_button_state()  # Update button back to normal
            self.set_status("✅ GPU kernels compiled successfully - ready to search!")

        self.write_to_console("🔧 Starting GPU kernel compilation...\n", color="white")
        self.set_status("⚙️ Compiling OpenCL kernels... Please wait...")
        
        # Disable the button during build
        self.run_button.config(text="Building Kernels...", state="disabled", bg="#808080")
        
        # Start the kernel build
        try:
            success = self.controller.run_kernel_build(on_complete=on_build_complete)
            if not success:
                self.write_to_console("❌ Failed to start kernel build process.\n", color="red")
                self.set_status("❌ Kernel build failed to start")
                self.run_button.config(state="normal")
                self.update_kernel_button_state()
        except Exception as e:
            self.write_to_console(f"❌ Error starting kernel build: {e}\n", color="red")
            self.set_status("❌ Kernel build error")
            self.run_button.config(state="normal")
            self.update_kernel_button_state()

    def on_run_search(self):
        """Start or stop the search process, or run kernel build if needed"""
        if not hasattr(self, 'search_running'):
            self.search_running = False
            self.start_time = None

        # Check if we need to build kernels first
        if not self.search_running and self.controller.is_kernel_build_needed():
            self.run_kernel_build()
            return

        if not self.search_running:
            # Get the current seed value
            seed_value = self.starting_seed_var.get().strip()
            if not seed_value or seed_value.lower() == 'random':
                seed_value = 'random'

            self.search_running = True
            self.start_time = time.time()
            self.run_button.config(text="STOP SEARCH", bg=RED)
            self.controller.set_setting('starting_seed',
                                        seed_value)  # Update the controller
            self.controller.run_search()
        else:
            self.search_running = False
            self.run_button.config(text="Let Jimbo Cook!", bg=BLUE)
            self.controller.stop_search()
 
        if self.start_time:
                elapsed = time.time() - self.start_time
                self.write_to_console(
                    f"Search stopped. Elapsed time: {elapsed:.2f} seconds\n")

    def on_closing(self):
        """Simple closing handler that prevents error dialogs"""
        import os
        
        # Hide the window immediately to prevent visual glitches
        self.root.withdraw()
        
        # Stop any running searches
        if hasattr(self, 'search_running') and self.search_running:
            self.controller.stop_search()
        
        # Clean up controller resources
        if hasattr(self, 'controller'):
            self.controller.cleanup()
            
        # Force exit the application
        os._exit(0)
        
        try:
            # Log the shutdown attempt
            print("🚪 Starting application shutdown sequence...")
            
            # Cancel all timers in a single block to avoid partial failures
            timers_to_cancel = []
            if hasattr(self, '_refresh_timer_id') and self._refresh_timer_id is not None:
                timers_to_cancel.append(self._refresh_timer_id)
            if hasattr(self, 'update_timer_id') and self.update_timer_id:
                timers_to_cancel.append(self.update_timer_id)
            if hasattr(self, '_debounce_table_update_id') and self._debounce_table_update_id:
                timers_to_cancel.append(self._debounce_table_update_id)
            if hasattr(self, '_status_update_id') and self._status_update_id:
                timers_to_cancel.append(self._status_update_id)
                
            # Cancel all timers at once
            for timer_id in timers_to_cancel:
                try:
                    self.root.after_cancel(timer_id)
                except:
                    pass
            print("✅ Timers cancelled")
                
            # Make sure we stop all search processes
            if hasattr(self, 'search_running') and self.search_running:
                try:
                    print("🛑 Stopping active searches...")
                    self.controller.stop_search()
                    print("✅ Searches stopped")
                except Exception:
                    pass

            # Run controller cleanup
            try:
                print("🧹 Running controller cleanup...")
                self.controller.cleanup()
                print("✅ Controller cleanup complete")
            except Exception:
                pass

            # Clean up widget references
            try:
                # Clear all potential widget references to prevent callbacks
                for attr in dir(self):
                    if attr.startswith('_') or attr in ['root', 'controller']:
                        continue
                    try:
                        setattr(self, attr, None)
                    except:
                        pass
                print("✅ Widget references cleared")
            except Exception:
                pass
                
            # Final exit - use a more reliable shutdown approach
            print("🎯 Shutdown sequence complete, exiting...")
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
                
            # As final resort, use os._exit for a clean process termination
            os._exit(0)
            
        except Exception:
            # Force clean exit as last resort
            os._exit(0)

    def update_config_display(self):
        """Update the UI with current configuration settings"""
        # Example: update config name, deck, stake, etc.
        self.config_name_var.set(self.controller.get_config_name())
        self.deck_var.set(self.controller.get_setting('deck', 'Red Deck'))
        self.stake_var.set(self.controller.get_setting('stake', 'Black Stake'))
        self.thread_groups_var.set(
            self.controller.get_setting('thread_groups', '32'))
        self.starting_seed_var.set(
            self.controller.get_setting('starting_seed', 'random'))
        self.number_of_seeds_var.set(
            self.controller.get_setting('number_of_seeds', 'All'))
        self.gpu_batch_var.set(
            self.controller.get_setting('gpu_batch', '16'))
        self.template_var.set(
            self.controller.get_setting('template', 'Default'))

        # Set auto cutoff state and update UI accordingly
        is_auto = self.controller.get_setting('auto_cutoff', False)
        self.auto_cutoff_var.set(is_auto)
        self.cutoff_entry.configure(state='disabled' if is_auto else 'normal')
        if not is_auto:
            self.cutoff_var.set(self.controller.get_setting('cutoff', ''))

        # Ensure cutoff and auto checkbox are always in sync on config load
        cutoff_val = self.controller.get_setting('cutoff', None)
        if cutoff_val is not None:
            self.cutoff_var.set(str(cutoff_val))
        else:
            self.cutoff_var.set(
                ""
            )  # This will trigger on_cutoff_changed and sync the checkbox
        self.on_cutoff_changed()

        # Sync scoring flags
        self.score_natural_negatives_var.set(
            self.controller.get_setting('score_natural_negatives', True))
        self.score_desired_negatives_var.set(
            self.controller.get_setting('score_desired_negatives', True))

    def update_criteria_display(self):
        """Update the criteria list with current needs and wants"""
        # Clear current list
        self.criteria_list.delete(0, tk.END)
        # Add needs
        for need in self.controller.config_model.needs_list:
            display_text = f"NEED: {get_display_name(need['value'])}"
            if "desireByAnte" in need and need["desireByAnte"] > 0:
                display_text += f" by Ante {need['desireByAnte']}"
            if "jokeredition" in need and need["jokeredition"] != "No_Edition":
                display_text += f" ({need['jokeredition']})"
            self.criteria_list.insert(tk.END, display_text)
        # Add wants
        for want in self.controller.config_model.wants_list:
            display_text = f"WANT: {get_display_name(want['value'])}"
            if "jokeredition" in want and want["jokeredition"] != "No_Edition":
                display_text += f" ({want['jokeredition']})"
            self.criteria_list.insert(tk.END, display_text)

    def update_deck_Settings_display(self):
        """Update the deck settings display with current values"""
        self.deck_var.set(self.controller.get_setting('deck', 'Red Deck'))
        self.stake_var.set(self.controller.get_setting('stake', 'Black Stake'))

    def on_refresh_results(self):
        """Manually refresh the results table"""
        self.controller.refresh_results()
        self.set_status("Results refreshed")

    def on_export_results(self):
        """Export results to a CSV file"""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            config_name = "ouija_results"
        file_name = config_name.lower().replace(" ", "_") + ".ouija.csv"
        file_path = filedialog.asksaveasfilename(
            initialdir=self.controller.config_model.EXPORT_DIR,
            initialfile=file_name,
            title="Export Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])

        if file_path:
            try:
                self.controller.export_results(file_path)
                self.set_status(f"Results exported to {file_path}")
                self.write_to_console(f"Results exported to {file_path}\n", color="white")
            except Exception as e:
                self.set_status(f"Error exporting results: {str(e)}")
                self.write_to_console(f"Error exporting results: {str(e)}\n", color="red")

    def on_delete_all_results(self):
        """Delete all results from the database after confirmation"""
        if messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete ALL results? This cannot be undone!",
                icon="warning",
        ):
            try:
                # Clear the table first for immediate visual feedback
                self.update_results_table(pd.DataFrame())

                # Delete from database
                if self.controller.delete_all_results():
                    self.set_status("All results deleted successfully")                    
                    self.write_to_console("All results deleted from database.\n", color="white")
                else:
                    self.set_status("Failed to delete results")                    
                    self.write_to_console("Error: Failed to delete results from database.\n", color="red")
            except Exception as e:
                self.set_status(f"Error deleting results: {str(e)}")
                self.write_to_console(f"Error deleting results: {str(e)}\n", color="red")

    def on_auto_cutoff_changed(self, *args):
        """Handle changes to the auto cutoff checkbox, keeping cutoff_var and checkbox in sync"""
        if self.auto_cutoff_var.get():
            # Checkbox checked: set cutoff to 'auto' and disable entry
            self.cutoff_var.set("auto")
            self.cutoff_entry.config(state="disabled")
            self.controller.set_setting('cutoff', 'auto')
        else:
            # Checkbox unchecked: restore last manual value or clear, and enable entry
            last_manual = getattr(self, '_last_manual_cutoff', "")
            self.cutoff_entry.config(state="normal")
            if self.cutoff_var.get() == "auto":
                self.cutoff_var.set(last_manual)
            self.controller.set_setting('cutoff', self.cutoff_var.get())

    def on_score_natural_negatives_changed(self, *args):
        """Handle changes to the score natural negatives checkbox"""
        self.controller.set_setting('score_natural_negatives',
                                    self.score_natural_negatives_var.get())

    def on_score_desired_negatives_changed(self, *args):
        """Handle changes to the score tag skip negatives checkbox"""
        self.controller.set_setting('score_desired_negatives',
                                    self.score_desired_negatives_var.get())

    def on_gpu_batch_changed(self, event=None):
        """Handle GPU batch size selection changes"""
        self.controller.set_setting('gpu_batch', self.gpu_batch_var.get())

    def on_template_changed(self, event=None):
        """Handle template selection changes"""
        # Get the friendly name from the dropdown
        friendly_name = self.template_var.get()
        # Get the actual template filename from our mapping
        template_name = self.template_mapping.get(friendly_name,
                                                  "ouija_template")
        # Update the setting with the actual template filename
        self.controller.set_setting('template', template_name)
        self.update_config_display()

    def on_random_seed(self):
        """Set the search seed to random, Ouija-CLI.exe handles this"""
        self.starting_seed_entry.delete(0, tk.END)
        self.starting_seed_entry.insert(0, "random")

    def on_number_of_seeds_changed(self, event=None):
        """Handle number of seeds selection changes"""
        self.controller.set_setting('number_of_seeds',
                                    self.number_of_seeds_var.get())

    def on_save_direct(self):
        """Save directly to {config_name}.ouija.json in the config directory, no prompt."""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            self.set_status("Please enter a configuration name before saving.")
            return
        file_name = config_name.lower().replace(" ", "_") + ".ouija.json"
        file_path = os.path.join(self.controller.config_model.CONFIG_DIR,
                                 file_name)
        self.controller.save_config(file_path)

    def on_save_as(self):
        """Prompt user for file path, pre-filling with config name, and save there."""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            self.set_status("Please enter a configuration name before saving.")
            return
        file_name = config_name.lower().replace(" ", "_") + ".ouija.json"
        file_path = filedialog.asksaveasfilename(
            initialdir=self.controller.config_model.CONFIG_DIR,
            initialfile=file_name,
            defaultextension=".ouija.json",
            filetypes=[("Ouija JSON files", "*.ouija.json"),
                       ("All files", "*.*")])
        if file_path:
            self.controller.save_config(file_path)

    def on_load_config(self):
        """Load a configuration"""
        file_path = filedialog.askopenfilename(
            initialdir=self.controller.config_model.CONFIG_DIR,
            title="Load Configuration",
            filetypes=[("Ouija JSON files", "*.ouija.json"),
                       ("All files", "*.*")])

        if file_path:
            self.controller.load_config(file_path)
            self.update_config_display(
            )  # Add this to refresh config UI elements
            self.update_criteria_display()  # Add this to refresh criteria list
            self.controller.refresh_results(
            )  # Refresh results table once after UI updates

    def on_add_need(self, category):
        """Add a need from the selected category"""
        # The True argument indicates to the dialog that the initial context is a 'Need'
        result = ItemSelectorDialog.show_dialog(self.root,
                                                f"Select Need: {category}",
                                                category, True)
        if result:
            item_payload = result["payload"]

            if result["is_need"]:
                # If it's a Rank or Suit Need, explicitly set desireByAnte to 1 as per requirements
                if result["type"] == "RankOrSuit":
                    item_payload["desireByAnte"] = 1
                # For Standard needs, desireByAnte should already be in item_payload if ante > 0
                self.controller.add_need(item_payload)
            else:
                # If is_need is False (either Rank/Suit selected as Want, or Standard item with Ante 0)
                # it's treated as a Want. Ensure desireByAnte is not in payload for wants if it was 0.
                if "desireByAnte" in item_payload and item_payload[
                    "desireByAnte"] == 0:
                    del item_payload["desireByAnte"]
                self.controller.add_want(item_payload)

            self.update_criteria_display()  # Refresh list after adding

    def on_add_want(self, category):
        """Add a want from the selected category"""
        # The False argument indicates to the dialog that the initial context is a 'Want'
        result = ItemSelectorDialog.show_dialog(self.root,
                                                f"Select Want: {category}",
                                                category, False)
        if result:
            item_payload = result["payload"]
            # Ensure desireByAnte is not part of a want payload,
            # especially if it might have been added and set to 0 by the dialog for standard items.
            if "desireByAnte" in item_payload:
                del item_payload["desireByAnte"]
            self.controller.add_want(item_payload)
            self.update_criteria_display()  # Refresh list after adding

    def on_remove_selected(self):
        """Remove the selected criterion"""
        selected_indices = self.criteria_list.curselection()
        if selected_indices:
            self.controller.remove_criterion(selected_indices[0])

    def on_edit_selected(self):
        """Edit the selected criterion"""
        selected_indices = self.criteria_list.curselection()
        if not selected_indices:
            return

        # Get the selected index and determine if it's a need or a want
        index = selected_indices[0]
        needs_count = len(self.controller.config_model.needs_list)

        is_need = index < needs_count

        # Get the criterion data
        if is_need:
            criterion = self.controller.config_model.needs_list[index]
            category = self.get_category_for_item(criterion["value"])
        else:
            criterion = self.controller.config_model.wants_list[index -
                                                                needs_count]
            category = self.get_category_for_item(criterion["value"])

        # Show the dialog with the existing item data
        result = ItemSelectorDialog.show_dialog(
            self.root,
            f"Edit {'Need' if is_need else 'Want'}: {category}",
            category,
            is_need,
            edit_mode=True,
            existing_item=criterion)

        if result:
            item_payload = result["payload"]

            # Handle Need/Want changes
            if result["is_need"] != is_need:
                # Need/Want type changed - remove old and add new
                self.controller.remove_criterion(index)

                if result["is_need"]:
                    self.controller.add_need(item_payload)
                else:
                    # Ensure desireByAnte is removed for wants
                    if "desireByAnte" in item_payload:
                        del item_payload["desireByAnte"]
                    self.controller.add_want(item_payload)
            else:
                # Same type, just update
                self.controller.edit_criterion(index, item_payload)

            self.update_criteria_display()

    def get_category_for_item(self, item_value):
        """Determine the category for an item based on its value
        
        Args:
            item_value: The internal item value
            
        Returns:
            The category name
        """
        # Check each category for the item value
        from utils.game_data import AVAILABLE_ITEMS, get_display_name

        item_display_name = get_display_name(item_value)

        for category, items in AVAILABLE_ITEMS.items():
            if item_display_name in items:
                return category

        # Default to Jokers if not found
        return "Jokers"

    def on_secret_button_clicked(self):
        """Handle clicking the secret button - reveals fun category buttons"""
        if hasattr(self, 'fun_buttons_visible') and self.fun_buttons_visible:
            # Hide fun buttons
            self.fun_buttons_frame.pack_forget()
            self.secret_button.config(text="do not push this button!")
            self.fun_buttons_visible = False
        else:
            # Show fun buttons
            self.fun_buttons_frame.pack(side=tk.RIGHT, padx=(10, 0))
            self.secret_button.config(text="hide fun buttons")
            self.fun_buttons_visible = True

    def run_fun_seed_search(self, category):
        """Run a fun seed search for the specified category, with robust error handling"""
        import traceback
        try:
            if not self.controller:
                return

            # Call the controller method to run the fun seed search
            success = self.controller.run_fun_seed_search(category)
            if success:                
                self.write_to_console(
                    f"🎯 Starting {category} seed search! Check the console for progress...\n", color="white"
                )
            else:                self.write_to_console(
                    f"❌ Failed to start {category} seed search. Check your configuration.\n", color="red"
                )
        except Exception as e:            
            self.write_to_console(
                f"[ERROR] Exception in fun seed search: {e}\n", color="red")
            traceback.print_exc()
            import sys
            import io
            buf = io.StringIO()
            traceback.print_exc(file=buf)
            self.write_to_console(buf.getvalue(), color="red")

    def update_results_table(self, dataframe):
        """Update results table with new data and handle auto cutoff if enabled"""
        self.latest_df = dataframe
        if dataframe is not None and not dataframe.empty:
            # Ensure all columns are of a robust type for display
            display_df = dataframe.copy()
            for col in display_df.columns:
                if col == "Seed":
                    # Convert Seed column to string without padding - Balatro seeds should remain as-is
                    display_df[col] = display_df[col].astype(str)
                elif pd.api.types.is_integer_dtype(display_df[col]):
                    display_df[col] = display_df[col].fillna(0)  # Fill NaN for integers
                elif pd.api.types.is_float_dtype(display_df[col]):
                    display_df[col] = display_df[col].fillna(0).map(lambda x: f'{x:.2f}')  # Format floats only

            self.pt.model.df = display_df
        else:
            self.pt.model.df = pd.DataFrame()

        try:
            self.pt.redraw()
            self._adjust_table_column_widths()
        except (IndexError, AttributeError) as e:
            # Handle IndexError when clicking on empty table or AttributeError for missing data
            # This prevents crashes when the pandastable tries to access non-existent rows
            pass
        self._search_results_count = len(dataframe) if dataframe is not None else 0
