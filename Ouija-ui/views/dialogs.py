"""
Dialog Windows for Ouija Seed Finder
"""

import tkinter as tk
from tkinter import ttk

from utils.game_data import AVAILABLE_ITEMS, JOKER_EDITIONS, get_internal_name
from utils.ui_utils import BLUE, RED, GREEN, BACKGROUND


class ItemSelectorDialog(tk.Toplevel):
    """Dialog window for selecting an item (joker, tarot, etc.)"""

    def __init__(
            self,
            parent,
            title,
            category="Jokers",
            is_need=True,
            edit_mode=False,
            existing_item=None,
    ):
        """Initialize the dialog window

        Args:
            parent: Parent window
            title: Dialog title
            category: Item category to choose from ("Jokers", "Tarots", etc.)
            is_need: Whether this item is a Need (required) or Want
            edit_mode: Whether this is an edit operation
            existing_item: Existing item data to pre-fill (for edit mode)
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("700x750")  # Initial size
        self.resizable(True, True)  # Allow resizing
        self.configure(bg=BACKGROUND)
        self.category = category
        self.is_need = is_need  # Initial context from MainWindow
        self.selected_item = None
        self.result = None  # Will store the final result on selection
        self.is_rank_or_suit = self.category in ["Ranks", "Suits"]
        self.edit_mode = edit_mode
        self.existing_item = existing_item
        # Main container frame
        self.main_frame = tk.Frame(self, bg=BACKGROUND)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Title showing the current category
        category_label = tk.Label(
            self.main_frame,
            text=f"Selecting: {category}",
            font=("m6x11", 16),
            bg=BACKGROUND,
            fg="white",
        )
        category_label.pack(fill="x", padx=10, pady=10)

        # Search field
        self.search_frame = tk.Frame(self.main_frame, bg=BACKGROUND)
        self.search_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(self.search_frame, text="Search:", bg=BACKGROUND, fg="white").pack(
            side="left", padx=10
        )
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_items)
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10)

        # Items listbox with scrollbar
        self.items_frame = tk.LabelFrame(
            self.main_frame, text="Items", bg=BACKGROUND, fg="white"
        )
        self.items_frame.pack(fill="x", expand=True, padx=10, pady=10)

        self.listbox_frame = tk.Frame(self.items_frame, bg=BACKGROUND)
        self.listbox_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.item_scrollbar = tk.Scrollbar(self.listbox_frame)
        self.item_scrollbar.pack(side="right", fill="y")

        # This is the main scrollable component - only the items list scrolls
        self.items_listbox = tk.Listbox(
            self.listbox_frame,
            yscrollcommand=self.item_scrollbar.set,
            selectmode="single",
            height=15,
            exportselection=False,
            bg="#2E3B42",
            fg="white",
        )
        self.items_listbox.pack(side="left", fill="both", expand=True)
        self.item_scrollbar.config(command=self.items_listbox.yview)

        # Ante selection for needs (non-Rank/Suit) OR Need/Want for Rank/Suit
        if self.is_rank_or_suit:
            self.need_want_frame = tk.LabelFrame(
                self.main_frame, text="Desire Type", bg=BACKGROUND, fg="white"
            )
            self.need_want_frame.pack(side=tk.LEFT, fill="y", padx=5, pady=5)

            self.is_need_for_rank_suit_var = tk.BooleanVar(
                value=self.is_need
            )  # Default from initial context

            need_want_container = tk.Frame(self.need_want_frame, bg=BACKGROUND)
            need_want_container.pack(fill="x", padx=5, pady=5)

            rb_need = ttk.Radiobutton(
                need_want_container,
                text="Need",
                variable=self.is_need_for_rank_suit_var,
                value=True,
            )
            rb_need.grid(row=0, column=0, padx=5, pady=2, sticky="w")

            rb_want = ttk.Radiobutton(
                need_want_container,
                text="Want",
                variable=self.is_need_for_rank_suit_var,
                value=False,
            )
            rb_want.grid(row=1, column=0, padx=5, pady=2, sticky="w")

        elif self.is_need:  # Only show ante for non-Rank/Suit if context is 'Need'
            self.ante_frame = tk.LabelFrame(
                self.main_frame, text="Required by Ante", bg=BACKGROUND, fg="white"
            )
            self.ante_frame.pack(side=tk.LEFT, fill="y", padx=5, pady=5)

            self.ante_var = tk.IntVar(value=1)  # Default to Ante 1 for needs
            ante_container = tk.Frame(self.ante_frame, bg=BACKGROUND)
            ante_container.pack(side=tk.LEFT, fill="y", padx=5, pady=5)

            # Create four rows of ante buttons with clearer spacing
            for ante in range(1, 9):
                rb = ttk.Radiobutton(
                    ante_container,
                    text=f"Ante {ante}",
                    variable=self.ante_var,
                    value=ante,
                )
                rb.grid(
                    row=(ante - 1) % 4,
                    column=(ante - 1) // 4,
                    padx=5,
                    pady=2,
                    sticky="w",
                )
            nah = ttk.Radiobutton(
                ante_container,
                text=f"Not required, just Want.",
                variable=self.ante_var,
                value=0,
            )
            nah.grid(row=5, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        # Edition frame for jokers (better organized)
        if category == "Jokers":  # Only show edition options for Jokers
            self.edition_frame = tk.LabelFrame(
                self.main_frame, text="Edition", bg=BACKGROUND, fg="white"
            )
            self.edition_frame.pack(side=tk.LEFT, fill="y", padx=5, pady=5)

            self.edition_var = tk.StringVar(value="No_Edition")

            edition_container = tk.Frame(self.edition_frame, bg=BACKGROUND)
            edition_container.pack(fill="x", padx=5, pady=5)

            for i, edition in enumerate(JOKER_EDITIONS):
                rb = ttk.Radiobutton(
                    edition_container,
                    text=edition,
                    variable=self.edition_var,
                    value=edition,
                )
                rb.grid(row=i, column=0, padx=5, pady=2, sticky="w")
        # Buttons
        self.button_frame = tk.Frame(self.main_frame, bg=BACKGROUND)
        self.button_frame.pack(side=tk.BOTTOM, fill="x", padx=10, pady=10)

        self.select_button = tk.Button(
            self.button_frame,
            text="Select",
            command=self.on_select,
            width=15,
            height=2,
            bg=BLUE,
            fg="white",
        )
        self.select_button.pack(side="right", padx=25, pady=10)

        self.cancel_button = tk.Button(
            self.button_frame,
            text="Cancel",
            command=self.destroy,
            width=15,
            height=2,
            bg=RED,
            fg="white",
        )
        self.cancel_button.pack(side="left", padx=25, pady=10)
        # Initialize items list with the pre-selected category
        self.update_items_list()

        # If in edit mode, pre-select the existing item and set other values
        if edit_mode and existing_item:
            # Pre-select item in the list
            self.pre_select_existing_item(existing_item)

            # Set Ante value for standard items
            if (
                    not self.is_rank_or_suit
                    and self.is_need
                    and "desireByAnte" in existing_item
            ):
                self.ante_var.set(existing_item["desireByAnte"])

            # Set Need/Want for Rank/Suit
            if self.is_rank_or_suit:
                self.is_need_for_rank_suit_var.set(self.is_need)

            # Set edition for Jokers
            if self.category == "Jokers" and "jokeredition" in existing_item:
                self.edition_var.set(existing_item["jokeredition"])

        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Set focus to search entry for immediate typing
        self.search_entry.focus_set()

    def filter_items(self, *args):
        """Filter the items list based on the search term"""
        self.update_items_list()

    def update_items_list(self):
        """Update the items listbox with filtered items"""
        self.items_listbox.delete(0, tk.END)
        search_term = self.search_var.get().lower()

        for item in AVAILABLE_ITEMS.get(self.category, []):
            if search_term == "" or search_term in item.lower():
                self.items_listbox.insert(tk.END, item)

    def pre_select_existing_item(self, existing_item):
        """Pre-select the existing item in the list for editing

        Args:
            existing_item: The existing item data
        """
        # Get the display name from the internal value
        from utils.game_data import get_display_name

        item_value = existing_item.get("value", "")
        display_name = get_display_name(item_value)

        # Find and select the item in the list
        for i in range(self.items_listbox.size()):
            if self.items_listbox.get(i) == display_name:
                self.items_listbox.selection_set(i)
                self.items_listbox.see(i)
                break

    def on_select(self):
        """Handle item selection"""
        if not self.items_listbox.curselection():
            return False

        selected_index = self.items_listbox.curselection()[0]
        selected_item_display_name = self.items_listbox.get(selected_index)

        internal_value = get_internal_name(selected_item_display_name)
        item_payload = {"value": internal_value}  # Base payload

        # Add edition info ONLY for Jokers
        if self.category == "Jokers" and hasattr(self, "edition_var"):
            edition = self.edition_var.get()
            item_payload["jokeredition"] = edition

        is_item_actually_a_need = False  # Default to Want

        if self.is_rank_or_suit:
            is_item_actually_a_need = self.is_need_for_rank_suit_var.get()
            self.result = {
                "payload": item_payload,
                "type": "RankOrSuit",
                "is_need": is_item_actually_a_need,
            }
        else:  # Standard item (Jokers, Tarots, Vouchers, Tags, Spectrals)
            if hasattr(
                    self, "ante_var"
            ):  # ante_frame was created (i.e., self.is_need was true at init)
                desire_by_ante = self.ante_var.get()
                if desire_by_ante > 0:
                    item_payload["desireByAnte"] = desire_by_ante
                    is_item_actually_a_need = True

            self.result = {
                "payload": item_payload,
                "type": "Standard",
                "is_need": is_item_actually_a_need,
            }

        self.destroy()  # I'M BACK! The missing line that makes dialogs actually close!
        return True

    @staticmethod
    def show_dialog(
            parent,
            title,
            category="Jokers",
            is_need=True,
            edit_mode=False,
            existing_item=None,
    ):
        """Show the dialog and return the result

        Args:
            parent: Parent window
            title: Dialog title
            category: Item category to choose from
            is_need: Whether this item is a Need
            edit_mode: Whether this is an edit operation
            existing_item: Existing item data to pre-fill (for edit mode)

        Returns:
            Dict with the selected item details or None if cancelled
        """
        dialog = ItemSelectorDialog(
            parent, title, category, is_need, edit_mode, existing_item
        )
        parent.wait_window(dialog)
        return getattr(dialog, "result", None)