"""
Criteria Widget for Ouija Seed Finder Application
Handles search criteria add/remove buttons and criteria list
"""
import tkinter as tk
from tkinter import messagebox
from utils.ui_utils import BACKGROUND, LIGHT_TEXT, BLUE, RED, DARK_BACKGROUND
from views.dialogs import ItemSelectorDialog
from utils.game_data import get_display_name


class CriteriaWidget:
    """Widget for managing search criteria"""
    
    def __init__(self, parent_frame, controller, main_window):
        self.parent_frame = parent_frame
        self.controller = controller
        self.main_window = main_window
        
        # Initialize variables
        self.criteria_list = None
        
        self.create_widget()
        
    def create_widget(self):
        """Create the criteria selection section with improved spacing"""
        self.criteria_frame = tk.LabelFrame(self.parent_frame,
                                            text="Search Criteria",
                                            padx=4,
                                            pady=4,
                                            bg=BACKGROUND,
                                            fg=LIGHT_TEXT,
                                            font=("m6x11", 14))
        self.criteria_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Criteria section - split into left (deck settings) and right (criteria list)
        criteria_left = tk.Frame(self.criteria_frame, bg=BACKGROUND)
        criteria_left.pack(side=tk.LEFT, fill=tk.Y, padx=4)

        criteria_right = tk.Frame(self.criteria_frame, bg=BACKGROUND)
        criteria_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4)

        # Criteria buttons in right side
        self.add_criteria_frame = tk.Frame(criteria_right, bg=BACKGROUND)
        self.add_criteria_frame.pack(fill=tk.X, pady=4)

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
        self.criteria_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Criteria action buttons
        self.criteria_buttons_frame = tk.Frame(criteria_right, bg=BACKGROUND)
        self.criteria_buttons_frame.pack(fill=tk.X, pady=4)

        tk.Button(self.criteria_buttons_frame,
                  text="Clear All",
                  command=self.on_clear_all,
                  bg=RED,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12)).pack(side=tk.RIGHT, padx=4)
        tk.Button(self.criteria_buttons_frame,
                  text="Remove Selected",
                  command=self.on_remove_selected,
                  bg=RED,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12)).pack(side=tk.RIGHT, padx=4)
        tk.Button(self.criteria_buttons_frame,
                  text="Edit Selected",
                  command=self.on_edit_selected,
                  bg=BLUE,
                  fg=LIGHT_TEXT,
                  font=("m6x11", 12)).pack(side=tk.RIGHT, padx=4)

    # Event handlers
    def on_add_need(self, category):
        """Add a need from the selected category"""
        # The True argument indicates to the dialog that the initial context is a 'Need'
        result = ItemSelectorDialog.show_dialog(self.main_window.root,
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
        result = ItemSelectorDialog.show_dialog(self.main_window.root,
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
            self.update_criteria_display()

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
            self.main_window.root,
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
        """Determine the category for a given item value"""
        from utils.game_data import AVAILABLE_ITEMS
        
        for category, items in AVAILABLE_ITEMS.items():
            if item_value in items:
                return category
        return "Unknown"

    def on_clear_all(self):
        """Clear all criteria"""
        if messagebox.askyesno("Confirm Clear", 
                              "Are you sure you want to clear all criteria?"):
            self.controller.clear_all_criteria()
            self.update_criteria_display()

    def update_criteria_display(self):
        """Update the criteria list display"""
        self.criteria_list.delete(0, tk.END)
        
        # Add needs
        for need in self.controller.config_model.needs_list:
            display_text = f"NEED: {get_display_name(need['value'])}"
            if 'desireByAnte' in need:
                display_text += f" by Ante {need['desireByAnte']}"
            self.criteria_list.insert(tk.END, display_text)
          
        # Add wants
        for want in self.controller.config_model.wants_list:
            display_text = f"WANT: {get_display_name(want['value'])}"
            self.criteria_list.insert(tk.END, display_text)
