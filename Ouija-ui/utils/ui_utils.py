"""
UI Utilities for Ouija Seed Finder
"""
import tkinter as tk


class Tooltip:
    """Custom tooltip implementation for UI elements"""

    def __init__(self, widget, text):
        """Initialize tooltip for a widget
        
        Args:
            widget: The widget to attach tooltip to
            text: The tooltip text to display
        """
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Display the tooltip"""
        if self.tooltip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")

        # Create tooltip label with slightly larger font
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#333333", foreground="white",
                         relief="solid", borderwidth=1,
                         font=("m6x11", 13))  # Increase from 12 to 13
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def add_tooltip(widget, text):
    """Add a tooltip to a widget
    
    Args:
        widget: The widget to add tooltip to
        text: The tooltip text to display
    """
    return Tooltip(widget, text)


# Color constants for UI
BLUE = "#008DFB"
RED = "#F94C3E"
GREEN = "#4CAF50"
BACKGROUND = "#394D53"
DARK_BACKGROUND = "#2E3B42"
LIGHT_TEXT = "white"


class ScrollableFrame(tk.Frame):
    """A scrollable frame container"""

    def __init__(self, container, *args, **kwargs):
        """Initialize scrollable frame
        
        Args:
            container: Parent widget
            *args, **kwargs: Additional arguments passed to Frame constructor
        """
        tk.Frame.__init__(self, container, *args, **kwargs)

        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        # Configure canvas to use scrollbar
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window in the canvas for the scrollable frame
        canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure canvas to resize with the window
        def _configure_canvas(event):
            # Update the width of the canvas window
            self.canvas.itemconfig(canvas_frame, width=event.width)

        self.canvas.bind("<Configure>", _configure_canvas)

        # Configure scrollbar
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def bind_mousewheel(self):
        """Bind mousewheel to scroll the frame"""

        def _on_mousewheel(event):
            # Handle different platforms
            if event.num == 5 or event.delta < 0:  # Scroll down
                self.canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:  # Scroll up
                self.canvas.yview_scroll(-1, "units")

        # Bind for different platforms
        self.scrollable_frame.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
        self.scrollable_frame.bind_all("<Button-4>", _on_mousewheel)  # Linux up
        self.scrollable_frame.bind_all("<Button-5>", _on_mousewheel)  # Linux down

    def unbind_mousewheel(self):
        """Unbind mousewheel"""
        self.scrollable_frame.unbind_all("<MouseWheel>")
        self.scrollable_frame.unbind_all("<Button-4>")
        self.scrollable_frame.unbind_all("<Button-5>")


class StatusBar(tk.Frame):
    """Status bar for displaying application status messages"""

    def __init__(self, master):
        """Initialize the status bar
        
        Args:
            master: Parent widget
        """
        tk.Frame.__init__(self, master)        
        # Main status label (left-aligned) with extra padding for emojis
        self.status_label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                     bg=DARK_BACKGROUND, fg=LIGHT_TEXT, font=("m6x11", 12))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Right-aligned metrics label (for search speed, etc.)
        # Reduce width from 20 to 15 characters
        self.metrics_label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.E,
                                      bg=DARK_BACKGROUND, fg=LIGHT_TEXT, width=15, font=("m6x11", 12))
        self.metrics_label.pack(side=tk.RIGHT, fill=tk.NONE)

        # Initialize with default values
        self.set_status("Ready")
        self.set_metrics("⏱️Ready!")

    def set_status(self, text):
        """Set the main status text (left-aligned)
        
        Args:
            text: Status message to display
        """
        self.status_label.config(text=text)
        self.update_idletasks()

    def set_metrics(self, text):
        """Set the metrics text (right-aligned)
        
        Args:
            text: Metrics to display
        """
        self.metrics_label.config(text=text)
        self.update_idletasks()
