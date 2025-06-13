"""
Results Table Widget - Handles the results table and action buttons
"""
import json
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from pandastable import Table
from utils.ui_utils import (BLUE, RED, GREEN, BACKGROUND, DARK_BACKGROUND, LIGHT_TEXT)
from tkinter import filedialog
from models.database_model import DatabaseModel

class ResultsWidget:
    """Widget for displaying search results and action buttons"""
    
    def __init__(self, parent_frame, controller, main_window):
        """
        Initialize the results widget
        
        Args:
            parent_frame: The parent frame to place this widget in
            controller: The application controller
            main_window: Reference to the main window for callbacks
        """
        self.parent_frame = parent_frame
        self.controller = controller
        self.main_window = main_window
        
        # Initialize table-related attributes
        self.latest_df = None
        self.pt = None
        self._refresh_timer_id = None
          # Create the widget
        self.create_widget()
        
        # Initialize the display with current config values
        self.update_config_display()
        
    def create_widget(self):
        """Create the results table section with optimized spacing"""
        self.results_frame = tk.LabelFrame(self.parent_frame,
                                           text="Results",
                                           padx=4,
                                           pady=4,
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
            command=self.refresh_results_table,
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

        # Create cutoff controls
        self.create_cutoff_controls(left_buttons)
        
        # Create secret/fun buttons
        self.create_fun_buttons(button_row)

        # Create the results table
        self.create_results_table()
        
    def create_cutoff_controls(self, parent):
        """Create cutoff score entry and auto checkbox"""
        cutoff_frame = tk.Frame(parent, bg=BACKGROUND)
        cutoff_frame.pack(side=tk.LEFT, padx=(4, 0))

        tk.Label(cutoff_frame,
                 text="Cutoff Score:",
                 bg=BACKGROUND,
                 fg=LIGHT_TEXT,
                 font=("m6x11", 12)).pack(side=tk.LEFT, anchor="w", padx=(0, 5))
        
        self.cutoff_var = tk.StringVar()
        self.cutoff_entry = tk.Entry(cutoff_frame,
                                     textvariable=self.cutoff_var,
                                     font=("m6x11", 12))
        self.cutoff_entry.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=(0, 5))
        
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
        self.auto_cutoff_check.pack(side=tk.LEFT, padx=(5, 0))
        self.cutoff_var.trace_add("write", self.on_cutoff_changed)
        
    def create_fun_buttons(self, button_row):
        """Create secret button and fun category buttons"""
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
        self.secret_button.pack(side=tk.RIGHT, padx=4)

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
            command=lambda: self.main_window.run_fun_seed_search("LOL"),
        )
        self.lol_button.pack(side=tk.LEFT, padx=4)

        self.gross_button = tk.Button(
            self.fun_buttons_frame,
            text="GROSS Seeds 🤮",
            bg="#6BCF7F",  # Green
            fg="black",
            font=("m6x11", 10),
            command=lambda: self.main_window.run_fun_seed_search("GROSS"),
        )
        self.gross_button.pack(side=tk.LEFT, padx=4)

        self.nsfw_button = tk.Button(
            self.fun_buttons_frame,
            text="NSFW Seeds 🍆",
            bg="#9D4EDD",  # Purple
            fg=LIGHT_TEXT,
            font=("m6x11", 10),
            command=lambda: self.main_window.run_fun_seed_search("NSFW"),
        )
        self.nsfw_button.pack(side=tk.LEFT, padx=4)

        self.cool_button = tk.Button(
            self.fun_buttons_frame,
            text="COOL Seeds 😎",
            bg="#4ECDC4",  # Teal
            fg="black",
            font=("m6x11", 10),
            command=lambda: self.main_window.run_fun_seed_search("COOL"),
        )
        self.cool_button.pack(side=tk.LEFT, padx=4)
        
        # Track visibility state
        self.fun_buttons_visible = False
        
    def create_results_table(self):
        """Create the pandas table for displaying results"""
        # Create a dedicated container frame for the table to isolate grid geometry manager
        table_container = tk.Frame(self.results_frame, bg=BACKGROUND)
        table_container.pack(fill=tk.BOTH, expand=True)

        # Table with no wasted space
        self.pt = Table(table_container,
                        dataframe=pd.DataFrame(),
                        showtoolbar=False,
                        showstatusbar=False,
                        font="m6x11",
                        fontsize=13,
                        headerfont=("m6x11", 13))

        # Show the table with tight packing
        self.pt.show()
        
        # Set default precision for numeric columns
        if not hasattr(self.pt, 'columnformats'):
            self.pt.columnformats = {}
            self.pt.columnformats['default'] = {'precision': 0}

        # Initialize latest_df
        self.latest_df = None

        # Set up initial table refresh
        self._setup_initial_table()
        
    def _setup_initial_table(self):
        """Set up the results table to refresh immediately and then every 400ms."""
        self._refresh_timer_id = None
        
        def refresh_loop():
            if self._refresh_timer_id is not None: 
                # Only continue if not cancelled
                self.refresh_results_table()
                self._refresh_timer_id = self.main_window.root.after(400, refresh_loop)

        self.refresh_results_table()
        self._refresh_timer_id = self.main_window.root.after(400, refresh_loop)
        
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
            
            # Ensure minimum width for single character columns
            min_width = 60  # Minimum 60 pixels for readability
            header_width = max(header_width, min_width)

            # Set the width, use max of calculated width or existing width
            if col in self.pt.colwidths:
                self.pt.colwidths[col] = max(self.pt.colwidths[col], header_width)
            else:
                self.pt.colwidths[col] = header_width

        # Update column widths in pandastable
        self.pt.columnwidths = self.pt.colwidths.copy()        
        # Redraw the table
        self.pt.redraw()

    def update_results_table(self, dataframe):
        """Update results table with new data"""
        self.latest_df = dataframe
        if dataframe is not None and not dataframe.empty:
            # Ensure all columns are of a robust type for display
            display_df = dataframe.copy()
            for col in display_df.columns:
                if col == "Seed":
                    # Convert Seed column to string without padding
                    display_df[col] = display_df[col].astype(str)
                elif pd.api.types.is_integer_dtype(display_df[col]):
                    display_df[col] = display_df[col].fillna(0)  # Fill NaN for integers
                elif pd.api.types.is_float_dtype(display_df[col]):
                    display_df[col] = display_df[col].fillna(0).map(lambda x: f'{x:.2f}')  # Format floats

            self.pt.model.df = display_df
        else:
            self.pt.model.df = pd.DataFrame()

        try:
            self.pt.redraw()
            self._adjust_table_column_widths()
        except (IndexError, AttributeError):
            # Handle errors when clicking on empty table
            pass

    def refresh_results_table(self):
        """Reload the results table from the database and update the UI."""
        from models.database_model import DatabaseModel
        db_model = DatabaseModel()

        # Try to get the current config path from the controller first
        config_path = self.controller.get_current_config_path()

        # Fall back to last saved config if needed
        if not config_path:
            try:
                import json

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

    def cleanup(self):
        """Clean up resources when widget is destroyed"""
        if hasattr(self, '_refresh_timer_id') and self._refresh_timer_id:
            self.main_window.root.after_cancel(self._refresh_timer_id)

    def on_export_results(self):
        """Handle export results button clicks"""
        # Get the current config path from the controller first
        config_path = self.controller.get_current_config_path()

        # Fall back to last saved config if needed
        if not config_path:
            try:
                with open('user.ouija.conf', 'r') as f:
                    user_conf = json.load(f)
                config_path = user_conf.get('last_config_path')
            except Exception:
                config_path = None

        if not config_path:
            messagebox.showerror("Error", "No config loaded, cannot export.")
            return

        # Construct default filename from config name
        filename = config_path.replace(".ouija.conf", ".ouija.csv")

        # Show save file dialog
        filepath = filedialog.asksaveasfilename(
            initialfile=filename,
            defaultextension=".ouija.csv",
            filetypes=[("Ouija CSV", "*.ouija.csv"), ("CSV Files", "*.csv"),
                   ("All Files", "*.*")],
        )

        if filepath:
            # Export the results to CSV

            db_model = DatabaseModel()
            if db_model.connect(config_path) and db_model.table_exists():
                df = db_model.get_dataframe()
                if df is not None and not df.empty:
                    df.to_csv(filepath, index=False)
                    messagebox.showinfo("Export Successful",
                            f"Results exported to {filepath}")
                else:
                    messagebox.showinfo("Export Failed", "No results to export.")
            else:
                messagebox.showerror("Error", "Could not connect to database.")

    def on_delete_all_results(self):
        """Handle delete all results button clicks"""
        if messagebox.askyesno("Confirm Delete", 
                          "Are you sure you want to delete all results?"):
            self.controller.delete_all_results()

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

    def on_auto_cutoff_changed(self):
        """Handle auto cutoff checkbox changes"""
        if self.auto_cutoff_var.get():
            # Auto mode enabled
            self.cutoff_var.set("auto")
            self.cutoff_entry.config(state="disabled")
        else:
            # Auto mode disabled, restore last manual value or clear
            if hasattr(self, '_last_manual_cutoff'):
                self.cutoff_var.set(self._last_manual_cutoff)
            else:
                self.cutoff_var.set("")
            self.cutoff_entry.config(state="normal")
        # Note: cutoff setting is saved automatically by on_cutoff_changed when cutoff_var changes

    def on_secret_button_clicked(self):
        """Handle clicking the secret button - reveals fun category buttons"""
        if self.fun_buttons_visible:
            # Hide fun buttons
            self.fun_buttons_frame.pack_forget()
            self.secret_button.config(text="do not push this button!")
            self.fun_buttons_visible = False
        else:
            # Show fun buttons
            self.fun_buttons_frame.pack(side=tk.RIGHT, padx=(10, 0))
            self.secret_button.config(text="hide fun buttons")
            self.fun_buttons_visible = True
            
    def update_config_display(self):
        """Update cutoff controls when config changes"""
        config_model = self.controller.config_model
        
        # Update cutoff
        cutoff = getattr(config_model, 'cutoff', '')
        self.cutoff_var.set(cutoff)
        if str(cutoff).lower() == 'auto':
            self.auto_cutoff_var.set(True)
            self.cutoff_entry.config(state="disabled")
        else:
            self.auto_cutoff_var.set(False)
            self.cutoff_entry.config(state="normal")
