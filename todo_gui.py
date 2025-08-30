#!/usr/bin/env python3
"""
Tkinter Personal To-Do List Application (Final Project)
- Preset categories (General, Work, Personal, Urgent) + "Add Category…" button
- Due Date (YYYY-MM-DD), colored rows (completed/due soon/overdue)
- Dark theme
- Buttons always work (show a prompt if no row is selected)
- Shortcuts: Double-click row = Edit, Enter = Mark Completed, Delete = Delete
- NOW WITH: SF Pro Font, High DPI Awareness, and Web-like Font Sizes
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
import ctypes # <-- Import ctypes for DPI awareness

STORE_FILE = "tasks.json"
DATE_FMT = "%Y-%m-%d"
DEFAULT_CATEGORIES = ["General", "Work", "Personal", "Urgent"]

# ---------------- Theme ----------------
PALETTE = {
    "bg":        "#C6CFFF",   # off-white
    "panel":     "#C6CFFF",
    "text":      "#374151",   # dark gray
    "muted":     "#6b7280",
    "accent":    "#a78bfa",   # soft purple
    "accent_fg": "#ffffff",
    "entry_bg":  "#f3f4f6",
    "entry_fg":  "#374151",
    "focus":     "#c084fc",   # brighter purple
    "tv_bg":     "#ffffff",
    "tv_fg":     "#374151",
    "tv_head_bg":"#ede9fe",   # lavender header
    "tv_head_fg":"#4c1d95",
    "tv_sel_bg": "#ddd6fe",
    "tv_sel_fg": "#111827",
    "row_completed": "#bbf7d0",  # mint green
    "row_due_soon":  "#fef9c3",  # light yellow
    "row_overdue":   "#fecaca",  # soft red
}

def parse_date(raw: str) -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        d = datetime.strptime(raw, DATE_FMT).date()
        return d.strftime(DATE_FMT)
    except ValueError:
        return None

def days_until(yyyy_mm_dd: Optional[str]) -> Optional[int]:
    if not yyyy_mm_dd:
        return None
    try:
        d = datetime.strptime(yyyy_mm_dd, DATE_FMT).date()
        return (d - date.today()).days
    except ValueError:
        return None

@dataclass
class Task:
    title: str
    description: str
    category: str = "General"
    completed: bool = False
    due_date: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Task(
            title=d.get("title","").strip(),
            description=d.get("description","").strip(),
            category=(d.get("category","General") or "General").strip(),
            completed=bool(d.get("completed", False)),
            due_date=d.get("due_date") or None
        )

def load_tasks(filename: str = STORE_FILE) -> List[Task]:
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [Task.from_dict(x) for x in data]
    except Exception:
        pass
    return []

def save_tasks(tasks: List[Task], filename: str = STORE_FILE) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=2, ensure_ascii=False)

class TodoGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self._setup_dpi_awareness() # <-- Call the new DPI setup method

        self.title("Personal To-Do List")
        self.geometry("1400x700")  # Made wider to accommodate larger inputs
        self.minsize(1200, 600)
        self._apply_theme()

        self.tasks: List[Task] = load_tasks()
        self.categories = self._derive_categories()

        # ---------- Top: Add form ----------
        top = ttk.Frame(self, style="Panel.TFrame"); top.pack(fill="x", padx=15, pady=12)

        ttk.Label(top, text="Title", style="Label.TLabel").grid(row=0, column=0, sticky="w", pady=(0,5))
        self.var_title = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_title, width=30, style="Entry.TEntry").grid(row=1, column=0, padx=(0,20))

        ttk.Label(top, text="Description", style="Label.TLabel").grid(row=0, column=1, sticky="w", pady=(0,5))
        self.var_desc = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_desc, width=45, style="Entry.TEntry").grid(row=1, column=1, padx=(0,12))

        ttk.Label(top, text="Category", style="Label.TLabel").grid(row=0, column=2, sticky="w", pady=(0,5))
        self.var_cat = tk.StringVar(value=self.categories[0])
        self.cat_combo = ttk.Combobox(top, textvariable=self.var_cat,
                                      values=self.categories, state="readonly", width=18) # <-- Removed style
        self.cat_combo.grid(row=1, column=2, padx=(0,8))
        ttk.Button(top, text="Add Category…", style="TButton", command=self.add_category).grid(row=1, column=3, padx=(0,12))

        ttk.Label(top, text="Due (YYYY-MM-DD)", style="Label.TLabel").grid(row=0, column=4, sticky="w", pady=(0,5))
        self.var_due = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_due, width=18, style="Entry.TEntry").grid(row=1, column=4, padx=(0,12))

        ttk.Button(top, text="Add Task", style="Accent.TButton", command=self.add_task).grid(row=1, column=5)

        # ---------- Filters ----------
        filt = ttk.Frame(self, style="Panel.TFrame"); filt.pack(fill="x", padx=15, pady=(0,10))
        ttk.Label(filt, text="Status:", style="Muted.TLabel").pack(side="left")
        self.var_status = tk.StringVar(value="All")
        ttk.Combobox(filt, textvariable=self.var_status,
                     values=["All","Completed","Pending"], width=20, state="readonly").pack(side="left", padx=10) # <-- Removed style

        ttk.Label(filt, text="Category:", style="Muted.TLabel").pack(side="left")
        self.var_filter_cat = tk.StringVar(value="All")
        self.filter_combo = ttk.Combobox(filt, textvariable=self.var_filter_cat,
                     values=["All"] + self.categories, width=20, state="readonly") # <-- Removed style
        self.filter_combo.pack(side="left", padx=10)

        ttk.Label(filt, text="Search:", style="Muted.TLabel").pack(side="left", padx=(12,0))
        self.var_search = tk.StringVar()
        ttk.Entry(filt, textvariable=self.var_search, width=35, style="Entry.TEntry").pack(side="left", padx=(6,0))
        ttk.Button(filt, text="Apply", style="TButton", command=self.refresh).pack(side="left", padx=(8,0))
        ttk.Button(filt, text="Clear", style="TButton", command=self.clear_filters).pack(side="left", padx=(8,0))


        # ---------- Task list ----------
        cols = ("status","title","category","due","hint","description")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=16, style="Treeview")
        self.tree.heading("status", text="Status")
        self.tree.heading("title", text="Title")
        self.tree.heading("category", text="Category")
        self.tree.heading("due", text="Due")
        self.tree.heading("hint", text="Hint")
        self.tree.heading("description", text="Description")
        self.tree.column("status", width=140, anchor="w")
        self.tree.column("title", width=320, anchor="w")
        self.tree.column("category", width=160, anchor="w")
        self.tree.column("due", width=130, anchor="w")
        self.tree.column("hint", width=130, anchor="w")
        self.tree.column("description", width=380, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=15, pady=12)

        # row colors
        self.tree.tag_configure("completed", background=PALETTE["row_completed"], foreground=PALETTE["tv_fg"])
        self.tree.tag_configure("due_soon",  background=PALETTE["row_due_soon"],  foreground=PALETTE["tv_fg"])
        self.tree.tag_configure("overdue",   background=PALETTE["row_overdue"],   foreground=PALETTE["tv_fg"])

        # ---------- Buttons (always enabled) ----------
        btns = ttk.Frame(self, style="Panel.TFrame"); btns.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(btns, text="✓ Mark Completed", style="TButton", command=self.mark_completed).pack(side="left")
        ttk.Button(btns, text="✎ Edit",            style="TButton", command=self.edit_task).pack(side="left", padx=8)
        ttk.Button(btns, text="🗑 Delete",          style="TButton", command=self.delete_task).pack(side="left", padx=8)
        ttk.Button(btns, text="⟳ Refresh",         style="TButton", command=self.refresh).pack(side="left", padx=8)

        # Selection helpers
        self.tree.bind("<Double-1>", lambda e: self.edit_task())   # double-click row to edit
        self.bind("<Delete>",       lambda e: self.delete_task())
        self.bind("<Return>",       lambda e: self.mark_completed())

        self.refresh()

    # -------- DPI Scaling ----------
    def _setup_dpi_awareness(self):
        """
        Makes the application DPI-aware to prevent blurriness or incorrect
        scaling on high-resolution displays, particularly on Windows.
        """
        try:
            # This call is specific to Windows
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            # This will fail on non-Windows systems, which is fine.
            # macOS and most Linux DEs handle this better by default.
            pass

    # -------- Theme ----------
    def _apply_theme(self):
        self.configure(bg=PALETTE["bg"])
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Font definitions with web-like sizes, now bigger + bold
        font_family_fallbacks = ("SF Pro", "Helvetica", "Arial", "sans-serif")

        # Increase size and make bold
        base_font = (font_family_fallbacks, 16, "bold")        # Main body text
        label_font = (font_family_fallbacks, 15, "bold")       # Form labels
        button_font = (font_family_fallbacks, 16, "bold")      # Buttons
        accent_button_font = (font_family_fallbacks, 16, "bold")  # Accent buttons
        header_font = (font_family_fallbacks, 15, "bold")      # Table headers
        tree_font = (font_family_fallbacks, 15, "bold")        # Table content


        style.configure(".",
                        background=PALETTE["panel"],
                        foreground=PALETTE["text"],
                        font=base_font)

        style.configure("Panel.TFrame", background=PALETTE["panel"])

        style.configure("Label.TLabel",
                        background=PALETTE["panel"],
                        foreground=PALETTE["text"],
                        font=label_font)

        style.configure("Muted.TLabel",
                        background=PALETTE["panel"],
                        foreground=PALETTE["muted"],
                        font=label_font)

        # Increased padding for Entry widgets to match larger fonts
        style.configure("Entry.TEntry",
                        fieldbackground=PALETTE["entry_bg"],
                        foreground=PALETTE["entry_fg"],
                        insertcolor=PALETTE["text"],
                        font=base_font,
                        padding=(8, 6))  # Added padding for better visual appearance

        style.configure("TButton",
                        background=PALETTE["panel"],
                        foreground=PALETTE["text"],
                        font=button_font,
                        padding=(12, 8))  # Added padding for buttons

        style.configure("Accent.TButton",
                        background=PALETTE["accent"],
                        foreground=PALETTE["accent_fg"],
                        font=accent_button_font,
                        padding=(12, 8))  # Added padding for accent buttons

        # --- CORRECTED COMBOBOX STYLING ---
        # Configure the default TCombobox style for the entry part
        style.configure("TCombobox",
                        fieldbackground=PALETTE["entry_bg"],
                        foreground=PALETTE["entry_fg"],
                        background=PALETTE["panel"],
                        arrowcolor=PALETTE["text"],
                        selectbackground=PALETTE["entry_bg"],
                        selectforeground=PALETTE["entry_fg"],
                        font=base_font,
                        padding=(8, 6))

        # Explicitly set the font for the dropdown list part of the combobox
        self.option_add("*TCombobox*Listbox.font", base_font)
        # --- END CORRECTION ---

        style.configure("Treeview",
                        background=PALETTE["tv_bg"],
                        fieldbackground=PALETTE["tv_bg"],
                        foreground=PALETTE["tv_fg"],
                        rowheight=36,  # Increased row height for larger fonts
                        font=tree_font)

        style.configure("Treeview.Heading",
                        background=PALETTE["tv_head_bg"],
                        foreground=PALETTE["tv_head_fg"],
                        font=header_font,
                        padding=(8, 8))  # Added padding for headers

    # -------- Helpers ----------
    def _derive_categories(self) -> List[str]:
        cats = sorted({t.category for t in self.tasks if t.category})
        base = DEFAULT_CATEGORIES.copy()
        for c in cats:
            if c not in base:
                base.append(c)
        return base

    def _filtered_tasks(self):
        status = self.var_status.get()
        cat = self.var_filter_cat.get()
        data = self.tasks
        if status == "Completed":
            data = [t for t in data if t.completed]
        elif status == "Pending":
            data = [t for t in data if not t.completed]
        if cat and cat != "All":
            data = [t for t in data if t.category.lower() == cat.lower()]
        def s_key(t: Task):
            due_key = datetime.max
            if t.due_date:
                try:
                    due_key = datetime.strptime(t.due_date, DATE_FMT)
                except ValueError:
                    pass
            return (t.completed, due_key, t.category.lower(), t.title.lower())
        return sorted(data, key=s_key)

    def _current_index(self) -> Optional[int]:
        """Return selected row's original index (iid is the index we inserted)."""
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            # The iid we set is a string of the task's original index.
            return int(sel[0])
        except (ValueError, IndexError):
            return None

    # -------- Actions ----------
    def add_category(self):
        name = simpledialog.askstring("Add Category", "Category name:")
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if name not in self.categories:
            self.categories.append(name)
            self.cat_combo.config(values=self.categories)
            self.filter_combo.config(values=["All"] + self.categories)
            self.var_cat.set(name)

    def add_task(self):
        title = self.var_title.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title is required.")
            return
        desc = self.var_desc.get().strip()
        cat = (self.var_cat.get() or "General").strip()
        if cat not in self.categories:
            self.categories.append(cat)
        due_raw = self.var_due.get().strip()
        due = parse_date(due_raw) if due_raw else None
        if due_raw and not due:
            messagebox.showwarning("Validation", "Invalid Due Date. Use YYYY-MM-DD.")
            return
        self.tasks.append(Task(title=title, description=desc, category=cat, completed=False, due_date=due))
        save_tasks(self.tasks)
        self.var_title.set(""); self.var_desc.set(""); self.var_due.set("")
        self.cat_combo.config(values=self.categories)
        self.filter_combo.config(values=["All"] + self.categories)
        self.refresh()

    def mark_completed(self):
        idx = self._current_index()
        if idx is None:
            messagebox.showinfo("Select a task", "Click a task row first, then press Mark Completed.")
            return
        if 0 <= idx < len(self.tasks):
            if self.tasks[idx].completed:
                messagebox.showinfo("Info", "This task is already completed.")
                return
            self.tasks[idx].completed = True
            save_tasks(self.tasks)
            self.refresh()
        else:
             messagebox.showerror("Error", "Selected task index is out of range.")


    def edit_task(self):
        idx = self._current_index()
        if idx is None:
            messagebox.showinfo("Select a task", "Click a task row first, then press Edit.")
            return

        if not (0 <= idx < len(self.tasks)):
            messagebox.showerror("Error", "Invalid task selected.")
            return

        t = self.tasks[idx]
        new_title = simpledialog.askstring("Edit Title", "Title:", initialvalue=t.title)
        if new_title is not None and new_title.strip():
            t.title = new_title.strip()
        new_desc = simpledialog.askstring("Edit Description", "Description:", initialvalue=t.description)
        if new_desc is not None:
            t.description = new_desc.strip()
        new_cat = simpledialog.askstring("Edit Category", "Category:", initialvalue=t.category)
        if new_cat is not None and new_cat.strip():
            t.category = new_cat.strip()
            if t.category not in self.categories:
                self.categories.append(t.category)
        curr_due = t.due_date or ""
        new_due = simpledialog.askstring("Edit Due Date", "YYYY-MM-DD (empty = clear):", initialvalue=curr_due)
        if new_due is not None:
            new_due = new_due.strip()
            if new_due == "":
                t.due_date = None
            else:
                parsed = parse_date(new_due)
                if parsed:
                    t.due_date = parsed
                else:
                    messagebox.showwarning("Validation", "Invalid date. Keeping existing due date.")
        save_tasks(self.tasks)
        self.cat_combo.config(values=self.categories)
        self.filter_combo.config(values=["All"] + self.categories)
        self.refresh()

    def delete_task(self):
        idx = self._current_index()
        if idx is None:
            messagebox.showinfo("Select a task", "Click a task row first, then press Delete.")
            return

        if not (0 <= idx < len(self.tasks)):
            messagebox.showerror("Error", "Invalid task selected.")
            return

        t = self.tasks[idx]
        if messagebox.askyesno("Confirm", f"Delete '{t.title}'?"):
            self.tasks.pop(idx)
            save_tasks(self.tasks)
            self.refresh()

    def clear_filters(self):
        self.var_status.set("All")
        self.var_filter_cat.set("All")
        self.refresh()

    # -------- Render ----------
    def refresh(self):
        # clear list
        for item in self.tree.get_children():
            self.tree.delete(item)

        # map tasks to original indices (handles duplicates)
        from collections import defaultdict, deque
        key_map = defaultdict(deque)
        for i, t in enumerate(self.tasks):
            key_map[(t.title, t.description, t.category, t.completed, t.due_date)].append(i)

        for t in self._filtered_tasks():
            key = (t.title, t.description, t.category, t.completed, t.due_date)
            try:
                orig_idx = key_map[key].popleft()
            except IndexError:
                # Fallback just in case, though it should not happen with this logic
                try:
                    orig_idx = self.tasks.index(t)
                except ValueError:
                    continue # Should not happen

            due_text = t.due_date or "-"
            hint = ""
            eta = days_until(t.due_date)
            tags = []
            if t.completed:
                tags.append("completed")
            else:
                if eta is not None:
                    if eta < 0:
                        hint = f"OVERDUE {-eta}d"; tags.append("overdue")
                    elif eta == 0:
                        hint = "TODAY"; tags.append("due_soon")
                    elif eta <= 3:
                        hint = f"in {eta}d"; tags.append("due_soon")

            status = "✓ Completed" if t.completed else "• Pending"
            self.tree.insert("", "end", iid=str(orig_idx),
                             values=(status, t.title, t.category, due_text, hint, t.description),
                             tags=tuple(tags))

def main():
    app = TodoGUI()
    app.mainloop()

if __name__ == "__main__":
    main()