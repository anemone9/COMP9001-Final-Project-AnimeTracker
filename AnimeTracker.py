"""
AnimeTracker GUI

This program provides a simple graphical interface for tracking anime
watching progress. Users can add, delete, search, view statistics,
and get genre-based recommendations.
"""

import json
import os
from collections import Counter
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = 'anime_data.json'
VALID_STATUS = ("planned", "watching", "completed", "dropped")

class Anime:
    """Represents a single anime entry."""

    def __init__(self, title, year=None, genres=None, status="planned", rating=None):
        self.title = title.strip()
        self.year = int(year) if year else None
        self.genres = [g.strip() for g in (genres or []) if g.strip()]
        self.status = status.strip().lower() if status else "planned"
        # rating should be an integer between 0 and 5
        self.rating = int(rating) if (str(rating).isdigit()) and 0 <= int(rating) <= 5 else None
        
    def to_dict(self):
        # Return this object as a JSON-serializable dictionary
        return {
            "title": self.title,
            "year": self.year,
            "genres": self.genres,
            "status": self.status,
            "rating": self.rating
        }
    
    def from_dict(d):
        """Create an Anime instance from a dictionary."""
        return Anime(
            d.get("title", ""),
            d.get("year", "Unknown"),
            d.get("genres", []),
            d.get("status", "planned"),
            d.get("rating"),
        )
    

class AnimeTracker:
    """Handles operations, statistics, and recommendations."""

    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.animes = []
        self.load()


    # -----------------------------------------------------------------------
    # File I/O
    # -----------------------------------------------------------------------
    def load(self):
        """Load anime data from JSON file or create an empty file."""

        if not os.path.exists(self.filename):
            self.animes = []
            self.save()
            return
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.animes = [Anime.from_dict(x) for x in data]
        except (OSError, json.JSONDecodeError):
            messagebox.showwarning("Warning", "Data file corrupted, reset to empty.")
            self.animes = []
            self.save()
    
    def save(self):
        """Save anime data to JSON file."""

        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump([a.to_dict() for a in self.animes], f, indent=4)
        except OSError:
            messagebox.showerror("Error", "Failed to save data file.")

    
    # -----------------------------------------------------------------------
    # Operations
    # -----------------------------------------------------------------------
    def add_anime(self, anime: Anime):
        """Add a new anime entry, ensuring no duplicates titles."""
        if any(a.title.lower() == anime.title.lower() for a in self.animes):
            messagebox.showwarning("Warning", "Anime already exists.")
            return False
        self.animes.append(anime)
        self.save()
        return True
    
    def delete_by_title(self, title: str):
        """Delete an anime by title (case-insensitive)."""
        before = len(self.animes)
        self.animes = [a for a in self.animes if a.title.lower() != title.lower()]
        if len(self.animes) < before:
            self.save()
            return True
        
        messagebox.showwarning("Warning", "Anime not found.")
        return False
    

    # -----------------------------------------------------------------------
    # Search / statistics / recommendation
    # -----------------------------------------------------------------------
    def search(self, kw: str):
        """Return a list of anime that match keyword in title or genres."""
        kw = kw.strip().lower()
        if not kw:
            return self.animes.copy()
        
        res = []
        for a in self.animes:
            if kw in a.title.lower() or any(kw in g.lower() for g in a.genres):
                res.append(a)
        return res
    
    def stats(self):
        """Compute total count, average rating, and top 3 genres."""
        total = len(self.animes)
        ratings = [a.rating for a in self.animes if a.rating is not None]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        genre_counter = Counter()
        for a in self.animes:
            genre_counter.update(a.genres)
        top_genres = genre_counter.most_common(3) # List of (genre, count), high to low
        
        return total, avg_rating, top_genres
    
    def recommend(self, top_n=3):
        """Recommend anime titles based on most liked genres."""
        liked = Counter() # Counter({genre: count}); The genre of animes rated 4 or 5
        for a in self.animes:
            if a.rating is not None and a.rating >= 4:
                liked.update(a.genres)
        if not liked:
            return []
        fav = [g for g, _ in liked.most_common()]

        # simple built-in catalog for demo purposes
        CATALOG = {
            "Action": ["Attack on Titan", "Chainsaw Man", "Cyberpunk: Edgerunners"],
            "Fantasy": ["Re:Zero", "Mushoku Tensei", "Frieren: Beyond Journey's End"],
            "School": ["Too Many Losing Heroines!", "Kaguya-sama: Love is War", "Horimiya"],
            "Band": ["K-ON", "MyGO!!!!!", "Girls Band Cry"]
        }
        recs = []
        for g in fav:
            if g in CATALOG:
                recs.extend(CATALOG[g])

        # remove duplicates and exclude existing titles
        existing = {a.title.lower() for a in self.animes}
        unique = []
        for r in recs:
            if r.lower() not in existing and r not in unique:
                unique.append(r)
        return unique[:top_n]
    

# ---------------------------------------------------------------------------
# GUI implementation using Tkinter
# ---------------------------------------------------------------------------
class AnimeTrackerGUI(tk.Tk):
    """Main window for AnimeTracker GUI."""

    def __init__(self):
        super().__init__()
        self.title("AnimeTracker - GUI")
        self.geometry("1000x650")
        self.minsize(950, 650) # minimum size can see 'delete' button

        self.tracker = AnimeTracker()
        self._sort_state = {"col": "title", "reverse": False}

        # header label
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(8, 0))
        header_label = ttk.Label(
            header_frame,
            text="🌸 AnimeTracker 🌸",
            font=("Helvetica", 22, "bold"),
            foreground="#ff69b4",
            anchor="center",
        )
        header_label.pack(fill="x")

        self._build_form()
        self._build_toolbar()
        self._build_table()
        self._refresh_table(self.tracker.animes)


    # --------------------------- build UI ---------------------------------
    def _build_form(self):
        """Create the top input form for adding/deleting entries."""
        frm = ttk.Frame(self, padding=(10, 8))
        frm.pack(fill="x")

        ttk.Label(frm, text="Title").grid(row=0, column=0, sticky="w")
        self.var_title = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_title, width=28).grid(row=1, column=0, padx=(0, 10))

        ttk.Label(frm, text="Year").grid(row=0, column=1, sticky="w")
        self.var_year = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_year, width=10).grid(row=1, column=1, padx=(0, 10))

        ttk.Label(frm, text="Genres (comma)").grid(row=0, column=2, sticky="w")
        self.var_genres = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_genres, width=28).grid(row=1, column=2, padx=(0, 10))

        ttk.Label(frm, text="Status").grid(row=0, column=3, sticky="w")
        self.var_status = tk.StringVar(value=VALID_STATUS[0])
        ttk.Combobox(frm, textvariable=self.var_status, values=VALID_STATUS,
                     width=14, state="readonly").grid(row=1, column=3, padx=(0, 10))

        ttk.Label(frm, text="Rating (0-5)").grid(row=0, column=4, sticky="w")
        self.var_rating = tk.StringVar()
        ttk.Combobox(frm, textvariable=self.var_rating,
                     values=("", "0", "1", "2", "3", "4", "5"),
                     width=8, state="readonly").grid(row=1, column=4, padx=(0, 10))

        ttk.Button(frm, text="Add", command=self.on_add).grid(row=1, column=5, padx=(0, 6))
        ttk.Button(frm, text="Delete", command=self.on_delete).grid(row=1, column=6)

    def _build_toolbar(self):
        """Create the toolbar for search, refresh, stats, and recommendation."""
        bar = ttk.Frame(self, padding=(10, 0))
        bar.pack(fill="x")

        ttk.Label(bar, text="Search").pack(side="left")
        self.var_search = tk.StringVar()
        ent = ttk.Entry(bar, textvariable=self.var_search, width=40)
        ent.pack(side="left", padx=(6, 6))
        ent.bind("<Return>", lambda e: self.on_search())

        ttk.Button(bar, text="Go", command=self.on_search).pack(side="left")
        ttk.Button(bar, text="Refresh", command=self.on_refresh).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Stats", command=self.on_stats).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Recommend", command=self.on_recommend).pack(side="left", padx=(6, 0))

    def _build_table(self):
        """Create the central Treeview table for displaying anime."""
        cols = ("title", "year", "genres", "status", "rating")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

        # column headers with sorting
        for col in cols:
            self.tree.heading(col, text=col.title(), command=lambda c=col: self._sort_by(c))

        self.tree.column("title", width=220, anchor="w")
        self.tree.column("year", width=60, anchor="center")
        self.tree.column("genres", width=260, anchor="w")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("rating", width=60, anchor="center")

        self.tree.bind("<Double-1>", self.on_row_double_click)

        # optional theme setup
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass


    # --------------------------- helpers ----------------------------------
    def _refresh_table(self, items):
        """Refresh the table with the given list of Anime objects."""
        self.tree.delete(*self.tree.get_children())
        for a in items:
            self.tree.insert("", "end", values=(
                a.title,
                a.year if a.year is not None else "",
                ", ".join(a.genres),
                a.status,
                "" if a.rating is None else a.rating,
            ))

    def _current_selection_title(self):
        """Return title of the currently selected row."""
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        return vals[0] if vals else None
    
    def _sort_by(self, col):
        """Sort table rows by the selected column."""
        reverse = not self._sort_state["reverse"] if self._sort_state["col"] == col else False
        self._sort_state = {"col": col, "reverse": reverse}

        def key_func(a: Anime):
            if col == "title":
                return a.title.lower()
            if col == "year":
                return (a.year is None, a.year or 0)
            if col == "genres":
                return ", ".join(a.genres).lower()
            if col == "status":
                return a.status
            if col == "rating":
                return (a.rating is None, -(a.rating or 0))
            return a.title.lower()

        sorted_items = sorted(self.tracker.animes, key=key_func, reverse=reverse)
        self._refresh_table(sorted_items)


    # --------------------------- event handlers ---------------------------
    def on_add(self):
        """Handle Add button click."""
        title = self.var_title.get().strip()
        if not title:
            messagebox.showinfo("Info", "Title cannot be empty.")
            return

        year = self.var_year.get().strip()
        genres = [g.strip() for g in self.var_genres.get().split(",") if g.strip()]
        status = self.var_status.get().strip().lower() or "planned"
        rating = self.var_rating.get().strip()
        rating = int(rating) if rating.isdigit() else None

        if status not in VALID_STATUS:
            messagebox.showwarning("Warning", f"Status must be one of {', '.join(VALID_STATUS)}.")
            return
        try:
            y = int(year) if year else None
        except ValueError:
            messagebox.showwarning("Warning", "Year must be an integer or blank.")
            return

        ok = self.tracker.add_anime(Anime(title, y, genres, status, rating))
        if not ok:
            messagebox.showinfo("Info", "Duplicate title, not added.")
            return

        self.on_refresh()
        self.var_title.set("")
        self.var_year.set("")
        self.var_genres.set("")
        self.var_status.set(VALID_STATUS[0])
        self.var_rating.set("")
        messagebox.showinfo("Success", "Anime added successfully.")

    def on_delete(self):
        """Handle Delete button click."""
        title = self._current_selection_title() or self.var_title.get().strip()
        if not title:
            messagebox.showinfo("Info", "Select a row or enter a title to delete.")
            return
        if not messagebox.askyesno("Confirm", f"Delete '{title}'?"):
            return
        
        ok = self.tracker.delete_by_title(title)
        if ok:
            self.on_refresh()
            messagebox.showinfo("Deleted", "Anime deleted.")
        else:
            messagebox.showinfo("Info", "Title not found.")

    def on_search(self):
        """Handle Search button click."""
        kw = self.var_search.get()
        res = self.tracker.search(kw)
        self._refresh_table(res)

    def on_refresh(self):
        """Reload and display all anime."""
        self._refresh_table(self.tracker.animes)

    def on_stats(self):
        """Display overall statistics in a message box."""
        total, avg, top = self.tracker.stats()
        lines = [
            f"Total: {total}",
            f"Average Rating: {avg if avg is not None else '-'}",
            "Top Genres:",
        ]
        if top:
            for g, c in top:
                lines.append(f"  - {g}: {c}")
        else:
            lines.append("  - None")
        messagebox.showinfo("Statistics", "\n".join(lines))

    def on_recommend(self):
        """Display recommendations based on user preferences."""
        recs = self.tracker.recommend(top_n=3)
        if not recs:
            messagebox.showinfo("Recommend", "Please rate some anime ≥4 to enable recommendations.")
            return
        messagebox.showinfo("Recommend", "You might like:\n" + "\n".join(f"- {r}" for r in recs))

    def on_row_double_click(self, _event):
        """When a row is double-clicked, fill form fields with its data."""
        item = self.tree.selection()
        if not item:
            return
        vals = self.tree.item(item[0], "values")
        if not vals:
            return
        
        title, year, genres, status, rating = vals
        self.var_title.set(title)
        self.var_year.set(year)
        self.var_genres.set(genres)
        self.var_status.set(status)
        self.var_rating.set("" if str(rating).strip() == "" else str(rating))

# ---------------------------------------------------------------------------
# Run the application
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = AnimeTrackerGUI()
    app.mainloop()