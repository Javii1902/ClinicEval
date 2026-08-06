import ctypes
import math
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk


def get_monitor_work_area(x, y):
    # Tk's winfo_screenwidth()/winfo_screenheight() don't reliably reflect
    # which monitor a window is actually on in a multi-monitor Windows
    # setup - they're effectively primary-monitor dimensions, with no
    # account for a secondary monitor's position (which can even have
    # negative coordinates if it sits to the left of/above the primary).
    # Clamping tooltip placement against them plants the tooltip back on
    # the primary monitor's coordinate space regardless of where the app
    # window and cursor actually are. Asking Windows directly for the
    # monitor containing this point gives its real bounds. Returns
    # (left, top, right, bottom) of that monitor's work area (screen minus
    # taskbar), or None if unavailable (e.g. not running on Windows).
    try:
        MONITOR_DEFAULTTONEAREST = 2

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        point = wintypes.POINT(int(x), int(y))
        hmonitor = ctypes.windll.user32.MonitorFromPoint(point, MONITOR_DEFAULTTONEAREST)

        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            return None

        rect = info.rcWork
        return (rect.left, rect.top, rect.right, rect.bottom)
    except (AttributeError, OSError, ValueError):
        return None


class SearchableCombobox(ttk.Frame):
    def __init__(
        self,
        parent,
        textvariable,
        values=None,
        width=50,
        on_select=None,
        on_focus_out=None,
        scroll_canvas=None,
    ):
        super().__init__(parent)

        self.textvariable = textvariable
        self.all_values = list(values or [])
        self.filtered_values = list(self.all_values)
        self.on_select_callback = on_select
        self.on_focus_out_callback = on_focus_out
        self.scroll_canvas = scroll_canvas
        self.listbox_visible = False
        self.suspend_trace = False

        self.entry = ttk.Entry(self, textvariable=self.textvariable, width=width)
        self.entry.pack(side="left", fill="x", expand=True)

        self.button = ttk.Button(self, text="▼", width=2, command=self.toggle_dropdown)
        self.button.pack(side="left", padx=(4, 0))

        self.dropdown = tk.Toplevel(self)
        self.dropdown.withdraw()
        self.dropdown.overrideredirect(True)
        self.dropdown.transient(self.winfo_toplevel())

        self.listbox_frame = ttk.Frame(self.dropdown, borderwidth=1, relief="solid")
        self.listbox_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(self.listbox_frame, height=8, exportselection=False)
        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.entry.bind("<KeyRelease>", self.on_keyrelease)
        self.entry.bind("<Down>", self.on_down_key)
        self.entry.bind("<Up>", self.on_up_key)
        self.entry.bind("<Return>", self.on_return_key)
        self.entry.bind("<Escape>", self.on_escape_key)
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.handle_focus_out)

        self.button.bind("<FocusOut>", self.handle_focus_out)

        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_click)
        self.listbox.bind("<ButtonRelease-1>", self.on_listbox_click)
        self.listbox.bind("<Return>", self.on_listbox_return)
        self.listbox.bind("<Escape>", self.on_listbox_escape)
        self.listbox.bind("<FocusOut>", self.handle_focus_out)

        self.textvariable.trace_add("write", self.on_textvariable_changed)

        self.update_listbox(self.all_values)

    def set_values(self, values):
        self.all_values = list(values or [])
        self.filter_values(self.textvariable.get())

    def on_textvariable_changed(self, *args):
        if self.suspend_trace:
            return
        self.filter_values(self.textvariable.get())

    def filter_values(self, typed_text):
        typed = (typed_text or "").strip().lower()

        if not typed:
            self.filtered_values = list(self.all_values)
        else:
            self.filtered_values = [
                value for value in self.all_values
                if typed in value.lower()
            ]

        self.update_listbox(self.filtered_values)

        if self.entry.focus_get() == self.entry:
            if self.filtered_values and self.is_anchor_visible():
                self.show_dropdown()
            else:
                self.hide_dropdown()

    def update_listbox(self, values):
        self.listbox.delete(0, tk.END)
        for value in values:
            self.listbox.insert(tk.END, value)

        if values:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)

    def toggle_dropdown(self):
        if self.listbox_visible:
            self.hide_dropdown()
        else:
            self.filter_values(self.textvariable.get())
            if self.filtered_values and self.is_anchor_visible():
                self.show_dropdown()
            self.entry.focus_set()

    def is_anchor_visible(self):
        if not self.scroll_canvas:
            return True

        try:
            self.scroll_canvas.update_idletasks()
            self.entry.update_idletasks()

            canvas_top = self.scroll_canvas.winfo_rooty()
            canvas_bottom = canvas_top + self.scroll_canvas.winfo_height()

            entry_top = self.entry.winfo_rooty()
            entry_bottom = entry_top + self.entry.winfo_height()

            return (
                entry_bottom >= canvas_top and
                entry_top <= canvas_bottom
            )
        except tk.TclError:
            return False

    def reposition_dropdown(self):
        if not self.listbox_visible:
            return

        if not self.is_anchor_visible():
            self.hide_dropdown()
            return

        try:
            self.update_idletasks()

            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            width = self.winfo_width()
            height = min(max(len(self.filtered_values), 1), 8) * 20 + 4

            self.dropdown.geometry(f"{width}x{height}+{x}+{y}")
            self.dropdown.lift()
        except tk.TclError:
            self.hide_dropdown()

    def show_dropdown(self, event=None):
        if not self.filtered_values or not self.is_anchor_visible():
            self.hide_dropdown()
            return

        self.listbox_visible = True
        self.dropdown.deiconify()
        self.reposition_dropdown()

    def hide_dropdown(self, event=None):
        self.dropdown.withdraw()
        self.listbox_visible = False

    def on_focus_in(self, event=None):
        self.filter_values(self.textvariable.get())

    def handle_focus_out(self, event=None):
        self.after(150, self._delayed_focus_out)

    def _delayed_focus_out(self):
        focused_widget = self.winfo_toplevel().focus_get()

        if focused_widget in (self.entry, self.button, self.listbox):
            return

        self.hide_dropdown()

        if self.on_focus_out_callback:
            self.on_focus_out_callback()

    def on_keyrelease(self, event):
        ignored = {"Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R"}
        if event.keysym in ignored:
            return
        self.filter_values(self.textvariable.get())

    def on_down_key(self, event):
        if self.filtered_values and self.is_anchor_visible():
            self.show_dropdown()
            self.listbox.focus_set()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            return "break"

    def on_up_key(self, event):
        if self.listbox_visible:
            current = self.listbox.curselection()
            if current:
                index = max(0, current[0] - 1)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                self.listbox.activate(index)
                self.listbox.see(index)
            return "break"

    def on_return_key(self, event):
        if self.listbox_visible and self.filtered_values:
            self.select_active_listbox_item()
            return "break"

    def on_escape_key(self, event):
        self.hide_dropdown()
        return "break"

    def on_listbox_click(self, event=None):
        self.select_active_listbox_item()

    def on_listbox_return(self, event=None):
        self.select_active_listbox_item()
        return "break"

    def on_listbox_escape(self, event=None):
        self.hide_dropdown()
        self.entry.focus_set()
        return "break"

    def select_active_listbox_item(self):
        current = self.listbox.curselection()
        if not current:
            return

        selected = self.listbox.get(current[0])

        self.suspend_trace = True
        self.textvariable.set(selected)
        self.suspend_trace = False

        self.hide_dropdown()
        self.entry.focus_set()
        self.entry.icursor(tk.END)

        if self.on_select_callback:
            self.on_select_callback()

    def get(self):
        return self.textvariable.get()

    def set(self, value):
        self.suspend_trace = True
        self.textvariable.set(value)
        self.suspend_trace = False
        self.filter_values(value)


class SelectionEditPopup(tk.Toplevel):
    def __init__(self, parent, title, prompt, values, initial_value, on_apply, allow_typing=True):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.on_apply = on_apply
        self.value_var = tk.StringVar(value=initial_value or "")
        self.allow_typing = allow_typing

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=prompt).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        if allow_typing:
            self.combo = SearchableCombobox(frame, textvariable=self.value_var, values=values, width=50)
            self.combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            self.combo.entry.focus_set()
            self.combo.entry.selection_range(0, tk.END)
            self.combo.entry.bind("<Return>", lambda e: self.apply())
        else:
            self.combo = ttk.Combobox(frame, textvariable=self.value_var, values=values, state="readonly", width=50)
            self.combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            self.combo.focus_set()
            self.combo.selection_range(0, tk.END)

        ttk.Button(frame, text="Save", command=self.apply).grid(row=2, column=1, sticky="e", padx=(8, 0))
        ttk.Button(frame, text="Cancel", command=self.destroy).grid(row=2, column=0, sticky="e")
        frame.columnconfigure(0, weight=1)

    def apply(self):
        value = self.value_var.get().strip()
        self.on_apply(value)
        self.destroy()


class QuestionTemplatePopup(tk.Toplevel):
    def __init__(self, parent, title, templates, selected_templates, on_apply):
        super().__init__(parent)
        self.title(title)
        self.geometry("900x520")
        self.minsize(520, 320)
        self.transient(parent)
        self.grab_set()

        self.on_apply = on_apply
        self.rows = []

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Select template comments:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(body, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.scrollable = ttk.Frame(self.canvas)

        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        for template in templates:
            self.add_template_row(template, template in selected_templates)

        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(button_frame, text="Apply", command=self.apply).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="right")

    def add_template_row(self, template_text, is_selected):
        var = tk.BooleanVar(value=is_selected)
        row_frame = ttk.Frame(self.scrollable, padding=(4, 6))
        row_frame.pack(fill="x", expand=True, anchor="w")

        cb = ttk.Checkbutton(row_frame, variable=var)
        cb.pack(side="left", anchor="n", padx=(0, 8))

        lbl = ttk.Label(row_frame, text=template_text, justify="left", wraplength=700, cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True, anchor="w")

        def toggle(_event=None):
            var.set(not var.get())

        row_frame.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)
        self.rows.append({"text": template_text, "var": var, "label": lbl})

    def on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)
        wrap = max(220, event.width - 70)
        for row in self.rows:
            row["label"].configure(wraplength=wrap)

    def apply(self):
        selected = [row["text"] for row in self.rows if row["var"].get()]
        self.on_apply(selected)
        self.destroy()


class MultiSelectPopup(tk.Toplevel):
    def __init__(self, parent, title, options, selected_values, on_apply):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x420")
        self.minsize(320, 260)
        self.transient(parent)
        self.grab_set()

        self.on_apply = on_apply
        self.rows = []

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        top_button_frame = ttk.Frame(container)
        top_button_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(top_button_frame, text="Select All", command=self.select_all).pack(side="left")
        ttk.Button(top_button_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=(6, 0))

        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(body, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.scrollable = ttk.Frame(self.canvas)

        self.scrollable.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        for option in options:
            self.add_option_row(option, option in selected_values)

        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(button_frame, text="Apply", command=self.apply).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="right")

    def add_option_row(self, option_text, is_selected):
        var = tk.BooleanVar(value=is_selected)
        row_frame = ttk.Frame(self.scrollable, padding=(4, 6))
        row_frame.pack(fill="x", expand=True, anchor="w")

        cb = ttk.Checkbutton(row_frame, variable=var)
        cb.pack(side="left", anchor="n", padx=(0, 8))

        lbl = ttk.Label(row_frame, text=option_text, justify="left", wraplength=300, cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True, anchor="w")

        def toggle(_event=None):
            var.set(not var.get())

        row_frame.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)

        self.rows.append({"text": option_text, "var": var, "label": lbl})

    def on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)
        wrap = max(180, event.width - 70)
        for row in self.rows:
            row["label"].configure(wraplength=wrap)

    def select_all(self):
        for row in self.rows:
            row["var"].set(True)

    def clear_all(self):
        for row in self.rows:
            row["var"].set(False)

    def apply(self):
        selected = [row["text"] for row in self.rows if row["var"].get()]
        self.on_apply(selected)
        self.destroy()


class CanvasTooltip:
    """Hover tooltip for a tk.Canvas. Call set_regions() after each redraw with a
    list of hit-test dicts: {"type": "rect"|"circle"|"wedge", ..., "lines": [...]}."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.regions = []
        self.tooltip_window = None
        self.label = None
        self.active_region_id = None

        canvas.bind("<Motion>", self.on_motion)
        canvas.bind("<Leave>", self.on_leave)

    def set_regions(self, regions):
        self.regions = regions or []

    def find_region(self, x, y):
        for region in self.regions:
            region_type = region["type"]
            if region_type == "rect":
                x0, y0, x1, y1 = region["bbox"]
                if x0 <= x <= x1 and y0 <= y <= y1:
                    return region
            elif region_type == "circle":
                cx, cy, r = region["circle"]
                if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                    return region
            elif region_type == "wedge":
                cx, cy, r, start_angle, extent = region["wedge"]
                dx, dy = x - cx, y - cy
                if (dx ** 2 + dy ** 2) ** 0.5 > r:
                    continue
                angle = math.degrees(math.atan2(-dy, dx)) % 360
                start = start_angle % 360
                end = (start_angle + extent) % 360
                in_wedge = (start <= angle <= end) if start <= end else (angle >= start or angle <= end)
                if in_wedge:
                    return region
        return None

    def on_motion(self, event):
        region = self.find_region(event.x, event.y)
        if region is None:
            self.hide()
            return

        region_id = region.get("id", id(region))
        if region_id != self.active_region_id or self.tooltip_window is None:
            self.active_region_id = region_id
            self.show(event, region["lines"])
        else:
            self.reposition(event)

    def on_leave(self, _event=None):
        self.hide()

    def show(self, event, lines):
        if self.tooltip_window is None:
            self.tooltip_window = tk.Toplevel(self.canvas)
            self.tooltip_window.overrideredirect(True)
            try:
                self.tooltip_window.attributes("-topmost", True)
            except tk.TclError:
                pass
            self.label = tk.Label(
                self.tooltip_window,
                justify="left",
                background="#333333",
                foreground="white",
                font=("Segoe UI", 9),
                padx=8,
                pady=6,
            )
            self.label.pack()

        self.label.config(text="\n".join(lines))
        self.reposition(event)
        self.tooltip_window.deiconify()

    def reposition(self, event):
        if self.tooltip_window is None:
            return

        gap = 16
        cursor_x = self.canvas.winfo_rootx() + event.x
        cursor_y = self.canvas.winfo_rooty() + event.y

        # Force the tooltip to lay out against its current text so its real
        # size is known before deciding which side of the cursor it fits on.
        self.tooltip_window.update_idletasks()
        tooltip_width = self.tooltip_window.winfo_reqwidth()
        tooltip_height = self.tooltip_window.winfo_reqheight()

        monitor_bounds = get_monitor_work_area(cursor_x, cursor_y)
        if monitor_bounds:
            screen_left, screen_top, screen_right, screen_bottom = monitor_bounds
        else:
            # Non-Windows or the API call failed for some reason - fall back
            # to the old single-screen approximation rather than crashing.
            screen_left, screen_top = 0, 0
            screen_right = self.canvas.winfo_screenwidth()
            screen_bottom = self.canvas.winfo_screenheight()

        x = cursor_x + gap
        if x + tooltip_width > screen_right:
            # Doesn't fit to the right - flip to the left of the cursor instead.
            x = cursor_x - tooltip_width - gap
        x = max(screen_left, min(x, screen_right - tooltip_width))

        y = cursor_y + gap
        if y + tooltip_height > screen_bottom:
            # Doesn't fit below - flip to above the cursor instead.
            y = cursor_y - tooltip_height - gap
        y = max(screen_top, min(y, screen_bottom - tooltip_height))

        self.tooltip_window.geometry(f"+{x}+{y}")

    def hide(self):
        self.active_region_id = None
        if self.tooltip_window is not None:
            self.tooltip_window.withdraw()
