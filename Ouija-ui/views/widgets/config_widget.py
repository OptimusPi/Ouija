"""
Configuration Widget for Ouija Seed Finder Application
Handles config name, save/load buttons, deck settings, and extra scoring options
"""
import tkinter as tk
from tkinter import ttk, filedialog
from utils.ui_utils import BACKGROUND, LIGHT_TEXT, BLUE, RED, DARK_BACKGROUND
from utils.game_data import AVAILABLE_ITEMS


class ConfigWidget:
    """Widget for configuration management and deck settings"""

    def __init__(self, parent_frame, controller, main_window):
        self.parent_frame = parent_frame
        self.controller = controller
        self.main_window = main_window

        # Template mapping dictionary for converting between UI-friendly names and template filenames
        self.template_mapping = {
            "Default": "ouija_template",
            "Anaglyph": "ouija_template_anaglyph",
            "Anaglyph (DEBUG)": "ouija_template_anaglyph_debug",
            "Erratic Ranks": "ouija_template_erratic_ranks",
            "Erratic Suits": "ouija_template_erratic_suits",
            "Analyzer (Immolate)": "immolate_analyzer",
        }

        # Initialize variables
        self.config_name_var = tk.StringVar()
        self.deck_var = tk.StringVar()
        self.stake_var = tk.StringVar()
        self.template_var = tk.StringVar()
        self.score_natural_negatives_var = tk.BooleanVar(value=True)
        self.score_desired_negatives_var = tk.BooleanVar(value=True)

        self.create_widget()

    def create_widget(self):
        """Create the configuration section with optimized spacing"""
        # Config frame with improved padding
        self.config_frame = tk.LabelFrame(self.parent_frame,
                                          text="Configuration",
                                          padx=4,
                                          pady=4,
                                          bg=BACKGROUND,
                                          fg=LIGHT_TEXT,
                                          font=("m6x11", 14))
        self.config_frame.pack(fill=tk.X, expand=False, padx=4, pady=(2, 5))

        # Config name entry with better padding
        self.config_name_entry = tk.Entry(self.config_frame,
                                          textvariable=self.config_name_var,
                                          font=("m6x11", 13))
        self.config_name_entry.pack(fill=tk.X, pady=4)
        self.config_name_var.trace_add("write", self.on_config_name_changed)

        # Button rows with improved spacing
        button_frame = tk.Frame(self.config_frame, bg=BACKGROUND)
        button_frame.pack(fill=tk.X, pady=4)

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
        self.save_as_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

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
        self.search_settings_frame = tk.LabelFrame(self.parent_frame,
                                                   text="Deck Settings",
                                                   padx=4,
                                                   pady=4,
                                                   bg=BACKGROUND,
                                                   fg=LIGHT_TEXT,
                                                   font=("m6x11", 14))
        self.search_settings_frame.pack(fill=tk.BOTH,
                                        expand=True,
                                        padx=1,
                                        pady=1)

        # Configure grid to make column 1 (dropdowns) expand
        self.search_settings_frame.grid_columnconfigure(1, weight=1)

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
                                          pady=4)
        self.deck_dropdown = ttk.Combobox(self.search_settings_frame,
                                          textvariable=self.deck_var,
                                          state="readonly",
                                          font=("m6x11", 12))
        self.deck_dropdown['values'] = AVAILABLE_ITEMS["Decks"]
        self.deck_dropdown.grid(row=row,
                                column=1,
                                sticky="ew",
                                pady=4,
                                padx=(5, 0))
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
                                          pady=4)
        self.stake_dropdown = ttk.Combobox(self.search_settings_frame,
                                           textvariable=self.stake_var,
                                           state="readonly",
                                           font=("m6x11", 12))
        self.stake_dropdown['values'] = AVAILABLE_ITEMS["Stakes"]
        self.stake_dropdown.grid(row=row,
                                 column=1,
                                 sticky="ew",
                                 pady=4,
                                 padx=(5, 0))
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
                                          pady=4)
        self.template_dropdown = ttk.Combobox(self.search_settings_frame,
                                              textvariable=self.template_var,
                                              state="readonly",
                                              font=("m6x11", 12))
        # Convert dictionary keys to list to avoid dict_keys object
        self.template_dropdown['values'] = list(self.template_mapping.keys())
        self.template_dropdown.grid(row=row, column=1, sticky="ew", pady=4)
        self.template_dropdown.bind("<<ComboboxSelected>>",
                                    self.on_template_changed)
        row += 1

        # --- Extra Scoring Settings ---
        scoring_frame = tk.LabelFrame(self.parent_frame,
                                      text="Extra Scoring Settings",
                                      padx=4,
                                      pady=4,
                                      bg=BACKGROUND,
                                      fg=LIGHT_TEXT,
                                      font=("m6x11", 13))
        scoring_frame.pack(fill=tk.X, expand=False, padx=4, pady=(2, 5))

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

    # Event handlers
    def on_config_name_changed(self, *args):
        """Handle configuration name changes"""
        self.controller.set_config_name(self.config_name_var.get())

    def on_deck_changed(self, event=None):
        """Handle deck selection changes"""
        self.controller.set_setting('deck', self.deck_var.get())

    def on_stake_changed(self, event=None):
        """Handle stake selection changes"""
        self.controller.set_setting('stake', self.stake_var.get())

    def on_template_changed(self, event=None):
        """Handle template selection changes"""
        # Get the friendly name from the dropdown
        friendly_name = self.template_var.get()
        # Get the actual template filename from our mapping
        template_name = self.template_mapping.get(friendly_name,
                                                  "ouija_template")
        # Update the setting with the actual template filename
        self.controller.set_setting('template', template_name)
        self.main_window.update_config_display()

    def on_save_direct(self):
        """Save directly to {config_name}.ouija.json in the config directory, no prompt."""
        import os
        config_name = self.config_name_var.get().strip()
        if not config_name:
            self.main_window.set_status(
                "Please enter a configuration name before saving.")
            return
        file_name = config_name.lower().replace(" ", "_") + ".ouija.json"
        file_path = os.path.join(self.controller.config_model.CONFIG_DIR,
                                 file_name)
        self.controller.save_config(file_path)

    def on_save_as(self):
        """Prompt user for file path, pre-filling with config name, and save there."""
        config_name = self.config_name_var.get().strip()
        default_filename = ""
        if config_name:
            default_filename = config_name.lower().replace(" ",
                                                           "_") + ".ouija.json"

        file_path = filedialog.asksaveasfilename(
            initialdir=self.controller.config_model.CONFIG_DIR,
            initialfile=default_filename,
            title="Save Configuration As",
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
            self.main_window.update_config_display()
            self.main_window.update_criteria_display()
            self.controller.refresh_results()

    def on_score_natural_negatives_changed(self):
        """Handle natural negatives scoring checkbox changes"""
        self.controller.set_setting('score_natural_negatives',
                                    self.score_natural_negatives_var.get())

    def on_score_desired_negatives_changed(self):
        """Handle desired negatives scoring checkbox changes"""
        self.controller.set_setting('score_desired_negatives',
                                    self.score_desired_negatives_var.get())

    def update_display(self):
        """Update the configuration display with current settings"""
        # Access settings directly from the controller's config_model
        config_model = self.controller.config_model

        # Update config name - add debug print
        config_name = getattr(config_model, 'config_name', '')
        print(
            f"DEBUG: update_display() - config_name from model: '{config_name}'"
        )
        self.config_name_var.set(config_name)

        # Update dropdowns
        self.deck_var.set(getattr(config_model, 'deck', ''))
        self.stake_var.set(getattr(config_model, 'stake', ''))

        # Update template (convert from filename to friendly name)
        template_filename = getattr(config_model, 'template', 'ouija_template')
        friendly_name = next((k for k, v in self.template_mapping.items()
                              if v == template_filename), 'Default')
        self.template_var.set(friendly_name)

        # Update checkboxes
        self.score_natural_negatives_var.set(
            getattr(config_model, 'score_natural_negatives', True))
        self.score_desired_negatives_var.set(
            getattr(config_model, 'score_desired_negatives', True))
