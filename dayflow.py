import csv
import os
import uuid
import calendar
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox


# ============================================================
# CONFIG
# ============================================================

APP_NAME = "DayFlow — Personal Planner"

DATA_DIR = "planner_data"
TASKS_FILE = os.path.join(DATA_DIR, "tasks.csv")
PRODUCTIVITY_FILE = os.path.join(DATA_DIR, "productivity.csv")

TASK_FIELDS = [
    "id",
    "date",
    "title",
    "start_time",
    "end_time",
    "description",
    "priority",
    "status",
    "productivity",
    "review",
    "created_at",
]

PRODUCTIVITY_FIELDS = [
    "id",
    "date",
    "task_id",
    "rating",
    "comment",
    "created_at",
]


# ============================================================
# STORAGE
# ============================================================

def ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(TASKS_FILE):
        write_csv(TASKS_FILE, TASK_FIELDS, [])

    if not os.path.exists(PRODUCTIVITY_FILE):
        write_csv(PRODUCTIVITY_FILE, PRODUCTIVITY_FIELDS, [])


def read_csv(filename):
    if not os.path.exists(filename):
        return []

    try:
        with open(
            filename,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:
            return list(csv.DictReader(file))
    except Exception as exc:
        messagebox.showerror(
            "File Error",
            f"Could not read:\n{filename}\n\n{exc}"
        )
        return []


def write_csv(filename, fields, rows):
    try:
        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fields
            )
            writer.writeheader()
            writer.writerows(rows)

    except Exception as exc:
        messagebox.showerror(
            "File Error",
            f"Could not save:\n{filename}\n\n{exc}"
        )


# ============================================================
# HELPERS
# ============================================================

def new_id():
    return uuid.uuid4().hex[:10]


def parse_date(value):
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()
    except Exception:
        return None


def parse_time(value):
    value = str(value).strip().upper()

    formats = [
        "%I:%M %p",
        "%I:%M%p",
        "%H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt
            )
        except ValueError:
            pass

    return None


def time_to_minutes(value):
    parsed = parse_time(value)

    if not parsed:
        return None

    return parsed.hour * 60 + parsed.minute


def format_time(value):
    parsed = parse_time(value)

    if not parsed:
        return value

    return parsed.strftime("%I:%M %p")


def format_date(value):
    parsed = parse_date(value)

    if not parsed:
        return value

    return parsed.strftime("%A, %d %B %Y")


def duration_minutes(start, end):
    s = time_to_minutes(start)
    e = time_to_minutes(end)

    if s is None or e is None:
        return 0

    return max(0, e - s)


def duration_text(minutes):
    hours = minutes // 60
    mins = minutes % 60

    if hours and mins:
        return f"{hours}h {mins}m"

    if hours:
        return f"{hours}h"

    return f"{mins}m"


def priority_color(priority):
    return {
        "High": "#ef4444",
        "Medium": "#f59e0b",
        "Low": "#22c55e",
    }.get(priority, "#64748b")


def status_color(status):
    return {
        "Planned": "#3b82f6",
        "In Progress": "#f59e0b",
        "Completed": "#22c55e",
        "Cancelled": "#ef4444",
    }.get(status, "#64748b")


# ============================================================
# MAIN APP
# ============================================================

class DayFlow(tk.Tk):

    BG = "#0b1220"
    SIDEBAR = "#101a2d"
    PANEL = "#121f35"
    CARD = "#182842"
    CARD_2 = "#1d304e"
    BORDER = "#2a3d5c"

    TEXT = "#f8fafc"
    MUTED = "#94a3b8"

    BLUE = "#3b82f6"
    BLUE_DARK = "#2563eb"

    GREEN = "#22c55e"
    RED = "#ef4444"
    ORANGE = "#f59e0b"
    PURPLE = "#8b5cf6"

    HOUR_HEIGHT = 70
    TIME_WIDTH = 85

    def __init__(self):

        super().__init__()

        ensure_storage()

        self.title(APP_NAME)
        self.geometry("1500x900")
        self.minsize(1150, 700)
        self.configure(bg=self.BG)

        self.tasks = read_csv(TASKS_FILE)
        self.productivity = read_csv(PRODUCTIVITY_FILE)

        self.selected_date = date.today()

        self.calendar_year = date.today().year
        self.calendar_month = date.today().month

        self.current_view = "schedule"

        self.schedule_canvas = None
        self.current_time_line = None
        self.current_time_text = None

        self.setup_styles()
        self.create_ui()

        self.show_schedule()

    # ========================================================
    # STYLE
    # ========================================================

    def setup_styles(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "DayFlow.Treeview",
            background=self.CARD,
            foreground=self.TEXT,
            fieldbackground=self.CARD,
            bordercolor=self.BORDER,
            rowheight=42,
            font=("Segoe UI", 9)
        )

        style.configure(
            "DayFlow.Treeview.Heading",
            background=self.CARD_2,
            foreground=self.TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )

        style.map(
            "DayFlow.Treeview",
            background=[
                ("selected", "#214f8f")
            ],
            foreground=[
                ("selected", "white")
            ]
        )

        style.configure(
            "Vertical.TScrollbar",
            background=self.CARD,
            troughcolor=self.BG,
            bordercolor=self.BG,
            arrowcolor=self.MUTED
        )

        style.configure(
            "Horizontal.TScrollbar",
            background=self.CARD,
            troughcolor=self.BG,
            bordercolor=self.BG,
            arrowcolor=self.MUTED
        )

        style.configure(
            "DayFlow.TCombobox",
            fieldbackground=self.CARD,
            background=self.CARD,
            foreground=self.TEXT,
            arrowcolor=self.TEXT,
            padding=7
        )

        style.map(
            "DayFlow.TCombobox",
            fieldbackground=[
                ("readonly", self.CARD)
            ],
            foreground=[
                ("readonly", self.TEXT)
            ]
        )

    # ========================================================
    # UI
    # ========================================================

    def create_ui(self):

        # ----------------------------------------------------
        # TOP BAR
        # ----------------------------------------------------

        top = tk.Frame(
            self,
            bg=self.SIDEBAR,
            height=70
        )

        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(
            top,
            text="DayFlow",
            font=("Segoe UI", 22, "bold"),
            fg=self.TEXT,
            bg=self.SIDEBAR
        ).pack(
            side="left",
            padx=(25, 5)
        )

        tk.Label(
            top,
            text="Personal Planner",
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.SIDEBAR
        ).pack(side="left")

        tk.Button(
            top,
            text="＋ Add Task",
            command=self.add_task,
            bg=self.BLUE,
            fg="white",
            activebackground=self.BLUE_DARK,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=9,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        ).pack(
            side="right",
            padx=20
        )

        tk.Button(
            top,
            text="Today",
            command=self.go_today,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD_2,
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            font=("Segoe UI", 10),
            cursor="hand2"
        ).pack(
            side="right",
            padx=5
        )

        # ----------------------------------------------------
        # MAIN
        # ----------------------------------------------------

        main = tk.Frame(
            self,
            bg=self.BG
        )

        main.pack(
            fill="both",
            expand=True
        )

        self.create_sidebar(main)

        self.content = tk.Frame(
            main,
            bg=self.BG
        )

        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.create_content_header()

        self.body = tk.Frame(
            self.content,
            bg=self.BG
        )

        self.body.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

    # ========================================================
    # SIDEBAR
    # ========================================================

    def create_sidebar(self, parent):

        sidebar = tk.Frame(
            parent,
            bg=self.SIDEBAR,
            width=270
        )

        sidebar.pack(
            side="left",
            fill="y"
        )

        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="PLANNER",
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.SIDEBAR
        ).pack(
            anchor="w",
            padx=22,
            pady=(25, 12)
        )

        items = [
            ("📅  Calendar", self.show_calendar),
            ("🕐  Daily Schedule", self.show_schedule),
            ("📋  Scheduled Tasks", self.show_tasks),
            ("📊  Productivity", self.show_productivity),
        ]

        self.nav_buttons = []

        for text, command in items:

            btn = tk.Button(
                sidebar,
                text=text,
                command=command,
                anchor="w",
                bg=self.SIDEBAR,
                fg=self.MUTED,
                activebackground=self.CARD,
                activeforeground=self.TEXT,
                relief="flat",
                bd=0,
                padx=22,
                pady=12,
                font=("Segoe UI", 10),
                cursor="hand2"
            )

            btn.pack(fill="x")

            self.nav_buttons.append(btn)

        tk.Frame(
            sidebar,
            bg=self.BORDER,
            height=1
        ).pack(
            fill="x",
            padx=22,
            pady=22
        )

        tk.Label(
            sidebar,
            text="SELECTED DAY",
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.SIDEBAR
        ).pack(
            anchor="w",
            padx=22
        )

        self.sidebar_date = tk.Label(
            sidebar,
            text="",
            font=("Segoe UI", 11, "bold"),
            fg=self.TEXT,
            bg=self.SIDEBAR,
            wraplength=220,
            justify="left"
        )

        self.sidebar_date.pack(
            anchor="w",
            padx=22,
            pady=(6, 20)
        )

        self.side_stats = {}

        stats = [
            ("tasks", "Tasks"),
            ("planned", "Planned"),
            ("free", "Free time"),
            ("completed", "Completed"),
        ]

        for key, label in stats:

            row = tk.Frame(
                sidebar,
                bg=self.SIDEBAR
            )

            row.pack(
                fill="x",
                padx=22,
                pady=6
            )

            tk.Label(
                row,
                text=label,
                font=("Segoe UI", 9),
                fg=self.MUTED,
                bg=self.SIDEBAR
            ).pack(side="left")

            value = tk.Label(
                row,
                text="—",
                font=("Segoe UI", 9, "bold"),
                fg=self.TEXT,
                bg=self.SIDEBAR
            )

            value.pack(side="right")

            self.side_stats[key] = value

    # ========================================================
    # HEADER
    # ========================================================

    def create_content_header(self):

        header = tk.Frame(
            self.content,
            bg=self.BG,
            height=85
        )

        header.pack(
            fill="x",
            padx=20
        )

        header.pack_propagate(False)

        self.page_title = tk.Label(
            header,
            text="",
            font=("Segoe UI", 22, "bold"),
            fg=self.TEXT,
            bg=self.BG
        )

        self.page_title.pack(
            side="left",
            pady=22
        )

        self.header_controls = tk.Frame(
            header,
            bg=self.BG
        )

        self.header_controls.pack(
            side="right",
            pady=22
        )

    def clear_header_controls(self):

        for widget in self.header_controls.winfo_children():
            widget.destroy()

    def add_header_button(
        self,
        text,
        command
    ):

        tk.Button(
            self.header_controls,
            text=text,
            command=command,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD_2,
            relief="flat",
            bd=0,
            padx=14,
            pady=7,
            font=("Segoe UI", 9),
            cursor="hand2"
        ).pack(
            side="left",
            padx=3
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def set_active_nav(self, index):

        for i, button in enumerate(self.nav_buttons):

            if i == index:
                button.configure(
                    bg=self.CARD,
                    fg=self.TEXT
                )
            else:
                button.configure(
                    bg=self.SIDEBAR,
                    fg=self.MUTED
                )

    def clear_body(self):

        for widget in self.body.winfo_children():
            widget.destroy()

        self.schedule_canvas = None
        self.current_time_line = None
        self.current_time_text = None

    def go_today(self):

        self.selected_date = date.today()

        self.calendar_year = self.selected_date.year
        self.calendar_month = self.selected_date.month

        self.show_schedule()

    def previous_day(self):

        self.selected_date -= timedelta(days=1)

        self.calendar_year = self.selected_date.year
        self.calendar_month = self.selected_date.month

        self.show_schedule()

    def next_day(self):

        self.selected_date += timedelta(days=1)

        self.calendar_year = self.selected_date.year
        self.calendar_month = self.selected_date.month

        self.show_schedule()

    # ========================================================
    # CALENDAR
    # ========================================================

    def show_calendar(self):

        self.current_view = "calendar"
        self.set_active_nav(0)

        self.clear_header_controls()

        self.add_header_button(
            "‹ Previous",
            self.previous_month
        )

        self.add_header_button(
            "Today",
            self.go_calendar_today
        )

        self.add_header_button(
            "Next ›",
            self.next_month
        )

        self.page_title.configure(
            text=datetime(
                self.calendar_year,
                self.calendar_month,
                1
            ).strftime("%B %Y")
        )

        self.clear_body()

        frame = tk.Frame(
            self.body,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        frame.pack(
            fill="both",
            expand=True
        )

        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]

        for col, name in enumerate(weekdays):

            tk.Label(
                frame,
                text=name,
                font=("Segoe UI", 9, "bold"),
                fg=self.MUTED,
                bg=self.PANEL,
                pady=10
            ).grid(
                row=0,
                column=col,
                sticky="nsew"
            )

            frame.grid_columnconfigure(
                col,
                weight=1
            )

        weeks = calendar.monthcalendar(
            self.calendar_year,
            self.calendar_month
        )

        for row in range(
            1,
            len(weeks) + 1
        ):

            frame.grid_rowconfigure(
                row,
                weight=1
            )

        for row, week in enumerate(
            weeks,
            start=1
        ):

            for col, day_number in enumerate(week):

                if day_number == 0:
                    continue

                selected = date(
                    self.calendar_year,
                    self.calendar_month,
                    day_number
                )

                date_string = selected.strftime(
                    "%Y-%m-%d"
                )

                is_today = (
                    selected == date.today()
                )

                is_selected = (
                    selected == self.selected_date
                )

                bg = (
                    "#183968"
                    if is_selected
                    else "#172d4b"
                    if is_today
                    else self.PANEL
                )

                cell = tk.Frame(
                    frame,
                    bg=bg,
                    highlightbackground=self.BORDER,
                    highlightthickness=1,
                    cursor="hand2"
                )

                cell.grid(
                    row=row,
                    column=col,
                    sticky="nsew"
                )

                day_label = tk.Label(
                    cell,
                    text=str(day_number),
                    font=(
                        "Segoe UI",
                        11,
                        "bold"
                    ),
                    fg=(
                        self.BLUE
                        if is_today
                        else self.TEXT
                    ),
                    bg=bg,
                    cursor="hand2"
                )

                day_label.pack(
                    anchor="w",
                    padx=9,
                    pady=(8, 3)
                )

                tasks = [
                    t for t in self.tasks
                    if t.get("date") == date_string
                ]

                tasks.sort(
                    key=lambda t:
                    time_to_minutes(
                        t.get(
                            "start_time",
                            ""
                        )
                    ) or 0
                )

                for task in tasks[:3]:

                    completed = (
                        task.get("status")
                        == "Completed"
                    )

                    task_bg = (
                        "#16452f"
                        if completed
                        else self.CARD_2
                    )

                    title = task.get(
                        "title",
                        "Untitled"
                    )

                    if len(title) > 18:
                        title = title[:15] + "..."

                    label = tk.Label(
                        cell,
                        text=(
                            "✓ "
                            if completed
                            else "• "
                        ) + title,
                        font=("Segoe UI", 8),
                        fg=(
                            "#86efac"
                            if completed
                            else "#bfdbfe"
                        ),
                        bg=task_bg,
                        anchor="w",
                        padx=5,
                        pady=3,
                        cursor="hand2"
                    )

                    label.pack(
                        fill="x",
                        padx=6,
                        pady=1
                    )

                    label.bind(
                        "<Button-1>",
                        lambda e, d=selected:
                        self.open_date(d)
                    )

                if len(tasks) > 3:

                    tk.Label(
                        cell,
                        text=f"+ {len(tasks) - 3} more",
                        font=("Segoe UI", 8),
                        fg=self.MUTED,
                        bg=bg
                    ).pack(
                        anchor="w",
                        padx=8
                    )

                cell.bind(
                    "<Button-1>",
                    lambda e, d=selected:
                    self.open_date(d)
                )

                day_label.bind(
                    "<Button-1>",
                    lambda e, d=selected:
                    self.open_date(d)
                )

                cell.bind(
                    "<Double-Button-1>",
                    lambda e, d=selected:
                    self.add_task(
                        selected_date=d
                    )
                )

        self.refresh_sidebar()

    def previous_month(self):

        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1

        self.show_calendar()

    def next_month(self):

        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1

        self.show_calendar()

    def go_calendar_today(self):

        today = date.today()

        self.selected_date = today
        self.calendar_year = today.year
        self.calendar_month = today.month

        self.show_calendar()

    def open_date(self, selected):

        self.selected_date = selected

        self.calendar_year = selected.year
        self.calendar_month = selected.month

        self.show_schedule()

    # ========================================================
    # DAILY SCHEDULE
    # ========================================================

    def show_schedule(self):

        self.current_view = "schedule"
        self.set_active_nav(1)

        self.clear_header_controls()

        self.add_header_button(
            "‹",
            self.previous_day
        )

        self.add_header_button(
            "Today",
            self.go_today
        )

        self.add_header_button(
            "›",
            self.next_day
        )

        self.page_title.configure(
            text=format_date(
                self.selected_date.strftime(
                    "%Y-%m-%d"
                )
            )
        )

        self.clear_body()

        self.sidebar_date.configure(
            text=format_date(
                self.selected_date.strftime(
                    "%Y-%m-%d"
                )
            )
        )

        self.create_schedule()

        self.refresh_sidebar()

    # --------------------------------------------------------
    # OPTIMIZED CANVAS SCHEDULE
    # --------------------------------------------------------

    def create_schedule(self):

        outer = tk.Frame(
            self.body,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        outer.pack(
            fill="both",
            expand=True
        )

        toolbar = tk.Frame(
            outer,
            bg=self.PANEL,
            height=52
        )

        toolbar.pack(
            fill="x"
        )

        toolbar.pack_propagate(False)

        tk.Label(
            toolbar,
            text="FULL DAY TIMELINE",
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            side="left",
            padx=15
        )

        tk.Label(
            toolbar,
            text="Double-click FREE area to add a task",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            side="right",
            padx=15
        )

        canvas_frame = tk.Frame(
            outer,
            bg=self.BG
        )

        canvas_frame.pack(
            fill="both",
            expand=True
        )

        self.schedule_canvas = tk.Canvas(
            canvas_frame,
            bg=self.BG,
            highlightthickness=0,
            bd=0
        )

        scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=self.schedule_canvas.yview
        )

        self.schedule_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.schedule_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # Smooth mouse wheel
        self.schedule_canvas.bind(
            "<MouseWheel>",
            self.on_schedule_wheel
        )

        self.schedule_canvas.bind(
            "<Button-4>",
            lambda e:
            self.schedule_canvas.yview_scroll(
                -3,
                "units"
            )
        )

        self.schedule_canvas.bind(
            "<Button-5>",
            lambda e:
            self.schedule_canvas.yview_scroll(
                3,
                "units"
            )
        )

        self.draw_schedule_canvas()

        # Start near current time
        if self.selected_date == date.today():

            now_minutes = (
                datetime.now().hour * 60
                + datetime.now().minute
            )

            target = max(
                0,
                now_minutes - 120
            )

            self.after(
                100,
                lambda:
                self.schedule_canvas.yview_moveto(
                    target / 1440
                )
            )

    def on_schedule_wheel(self, event):

        if event.delta:

            amount = (
                -4
                if event.delta > 0
                else 4
            )

            self.schedule_canvas.yview_scroll(
                amount,
                "units"
            )

        return "break"

    def draw_schedule_canvas(self):

        canvas = self.schedule_canvas

        canvas.delete("all")

        width = max(
            900,
            canvas.winfo_width()
        )

        total_height = (
            24 * self.HOUR_HEIGHT
        )

        timeline_x = self.TIME_WIDTH

        # ----------------------------------------------------
        # Background
        # ----------------------------------------------------

        canvas.create_rectangle(
            0,
            0,
            width,
            total_height,
            fill=self.BG,
            outline=""
        )

        # ----------------------------------------------------
        # Hour lines
        # ----------------------------------------------------

        for hour in range(24):

            y = (
                hour * self.HOUR_HEIGHT
            )

            canvas.create_line(
                timeline_x,
                y,
                width,
                y,
                fill=self.BORDER,
                width=1
            )

            hour_text = datetime(
                2000,
                1,
                1,
                hour,
                0
            ).strftime("%I %p")

            canvas.create_text(
                timeline_x - 12,
                y + 8,
                text=hour_text,
                fill=self.MUTED,
                font=("Segoe UI", 9, "bold"),
                anchor="e"
            )

            # Half-hour guide
            half_y = (
                y
                + self.HOUR_HEIGHT / 2
            )

            canvas.create_line(
                timeline_x,
                half_y,
                width,
                half_y,
                fill="#17263c",
                dash=(3, 5)
            )

        # ----------------------------------------------------
        # FREE areas
        # ----------------------------------------------------

        tasks = self.get_selected_tasks()

        free_ranges = self.get_free_ranges(tasks)

        for start, end in free_ranges:

            y1 = (
                start / 60
            ) * self.HOUR_HEIGHT

            y2 = (
                end / 60
            ) * self.HOUR_HEIGHT

            if y2 - y1 >= 18:

                canvas.create_text(
                    timeline_x + 18,
                    y1 + 12,
                    text=(
                        "FREE  "
                        + format_minutes_label(
                            start
                        )
                        + " – "
                        + format_minutes_label(
                            end
                        )
                    ),
                    fill="#3f536f",
                    font=("Segoe UI", 8),
                    anchor="nw",
                    tags=("free",)
                )

        # ----------------------------------------------------
        # TASKS
        # ----------------------------------------------------

        self.draw_task_cards(
            canvas,
            tasks,
            width
        )

        # ----------------------------------------------------
        # Current time
        # ----------------------------------------------------

        if self.selected_date == date.today():

            self.draw_current_time()

        canvas.configure(
            scrollregion=(
                0,
                0,
                width,
                total_height
            )
        )

    def get_selected_tasks(self):

        date_string = self.selected_date.strftime(
            "%Y-%m-%d"
        )

        tasks = [
            t for t in self.tasks
            if t.get("date") == date_string
        ]

        tasks.sort(
            key=lambda t:
            time_to_minutes(
                t.get(
                    "start_time",
                    ""
                )
            ) or 0
        )

        return tasks

    def get_free_ranges(self, tasks):

        intervals = []

        for task in tasks:

            start = time_to_minutes(
                task.get(
                    "start_time",
                    ""
                )
            )

            end = time_to_minutes(
                task.get(
                    "end_time",
                    ""
                )
            )

            if (
                start is not None
                and end is not None
                and end > start
            ):
                intervals.append(
                    (start, end)
                )

        intervals.sort()

        merged = []

        for start, end in intervals:

            if not merged:
                merged.append(
                    [start, end]
                )

            elif start <= merged[-1][1]:

                merged[-1][1] = max(
                    merged[-1][1],
                    end
                )

            else:
                merged.append(
                    [start, end]
                )

        free = []

        current = 0

        for start, end in merged:

            if start > current:
                free.append(
                    (current, start)
                )

            current = max(
                current,
                end
            )

        if current < 1440:

            free.append(
                (current, 1440)
            )

        return free

    def draw_task_cards(
        self,
        canvas,
        tasks,
        width
    ):

        # ----------------------------------------------------
        # Detect columns for overlapping tasks
        # ----------------------------------------------------

        task_positions = []

        for task in tasks:

            start = time_to_minutes(
                task.get(
                    "start_time",
                    ""
                )
            )

            end = time_to_minutes(
                task.get(
                    "end_time",
                    ""
                )
            )

            if (
                start is None
                or end is None
                or end <= start
            ):
                continue

            task_positions.append({
                "task": task,
                "start": start,
                "end": end,
                "column": 0,
                "columns": 1
            })

        # Basic overlap layout
        for i, current in enumerate(
            task_positions
        ):

            used_columns = set()

            for previous in task_positions[:i]:

                if (
                    previous["start"]
                    < current["end"]
                    and
                    previous["end"]
                    > current["start"]
                ):

                    used_columns.add(
                        previous["column"]
                    )

            column = 0

            while column in used_columns:
                column += 1

            current["column"] = column

        # Find max columns per overlapping group
        for current in task_positions:

            max_columns = 1

            for other in task_positions:

                if (
                    other["start"]
                    < current["end"]
                    and
                    other["end"]
                    > current["start"]
                ):

                    max_columns = max(
                        max_columns,
                        other["column"] + 1
                    )

            current["columns"] = max_columns

        available_width = (
            width
            - self.TIME_WIDTH
            - 25
        )

        for item in task_positions:

            task = item["task"]

            start = item["start"]
            end = item["end"]

            y1 = (
                start / 60
            ) * self.HOUR_HEIGHT + 4

            y2 = (
                end / 60
            ) * self.HOUR_HEIGHT - 4

            card_height = max(
                35,
                y2 - y1
            )

            columns = item["columns"]

            column_width = (
                available_width
                / columns
            )

            x1 = (
                self.TIME_WIDTH
                + item["column"]
                * column_width
                + 7
            )

            x2 = (
                self.TIME_WIDTH
                + (item["column"] + 1)
                * column_width
                - 7
            )

            bg = (
                "#16452f"
                if task.get("status")
                == "Completed"
                else self.CARD_2
            )

            border = status_color(
                task.get(
                    "status",
                    "Planned"
                )
            )

            # Card
            card_id = canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=bg,
                outline=border,
                width=1,
                tags=(
                    "task",
                    f"task_{task['id']}"
                )
            )

            # Priority stripe
            canvas.create_rectangle(
                x1,
                y1,
                x1 + 5,
                y2,
                fill=priority_color(
                    task.get(
                        "priority",
                        "Medium"
                    )
                ),
                outline="",
                tags=(
                    "task",
                    f"task_{task['id']}"
                )
            )

            title = task.get(
                "title",
                "Untitled"
            )

            if task.get("status") == "Completed":
                title = "✓ " + title

            canvas.create_text(
                x1 + 14,
                y1 + 13,
                text=title,
                fill=(
                    "#86efac"
                    if task.get("status")
                    == "Completed"
                    else self.TEXT
                ),
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                tags=(
                    "task",
                    f"task_{task['id']}"
                )
            )

            if card_height >= 48:

                time_text = (
                    f"{format_time(task.get('start_time', ''))}"
                    f" → "
                    f"{format_time(task.get('end_time', ''))}"
                )

                canvas.create_text(
                    x1 + 14,
                    y1 + 31,
                    text=time_text,
                    fill=self.MUTED,
                    font=("Segoe UI", 8),
                    anchor="w",
                    tags=(
                        "task",
                        f"task_{task['id']}"
                    )
                )

            if card_height >= 75:

                desc = task.get(
                    "description",
                    ""
                )

                if desc:

                    if len(desc) > 75:
                        desc = desc[:72] + "..."

                    canvas.create_text(
                        x1 + 14,
                        y1 + 50,
                        text=desc,
                        fill="#cbd5e1",
                        font=("Segoe UI", 8),
                        anchor="nw",
                        width=max(
                            100,
                            x2 - x1 - 28
                        ),
                        tags=(
                            "task",
                            f"task_{task['id']}"
                        )
                    )

            if card_height >= 100:

                status = task.get(
                    "status",
                    "Planned"
                )

                canvas.create_text(
                    x1 + 14,
                    y2 - 12,
                    text=status,
                    fill=status_color(status),
                    font=("Segoe UI", 7, "bold"),
                    anchor="w",
                    tags=(
                        "task",
                        f"task_{task['id']}"
                    )
                )

            # Click handlers
            canvas.tag_bind(
                f"task_{task['id']}",
                "<Double-Button-1>",
                lambda e, tid=task["id"]:
                self.edit_task(tid)
            )

            canvas.tag_bind(
                f"task_{task['id']}",
                "<Button-3>",
                lambda e, tid=task["id"]:
                self.task_context_menu(
                    e,
                    tid
                )
            )

    # ========================================================
    # CURRENT TIME LINE
    # ========================================================

    def draw_current_time(self):

        if not self.schedule_canvas:
            return

        now = datetime.now()

        minutes = (
            now.hour * 60
            + now.minute
            + now.second / 60
        )

        y = (
            minutes / 60
        ) * self.HOUR_HEIGHT

        canvas = self.schedule_canvas

        self.current_time_line = (
            canvas.create_line(
                self.TIME_WIDTH,
                y,
                max(
                    self.TIME_WIDTH + 100,
                    canvas.winfo_width()
                ),
                y,
                fill=self.RED,
                width=2,
                tags="current_time"
            )
        )

        self.current_time_text = (
            canvas.create_text(
                self.TIME_WIDTH - 8,
                y,
                text=now.strftime(
                    "%I:%M %p"
                ),
                fill="white",
                font=("Segoe UI", 8, "bold"),
                anchor="e",
                tags="current_time"
            )
        )

        self.after(
            30000,
            self.update_current_time
        )

    def update_current_time(self):

        if (
            self.current_view != "schedule"
            or self.selected_date != date.today()
            or not self.schedule_canvas
        ):
            return

        now = datetime.now()

        minutes = (
            now.hour * 60
            + now.minute
            + now.second / 60
        )

        y = (
            minutes / 60
        ) * self.HOUR_HEIGHT

        try:

            self.schedule_canvas.coords(
                self.current_time_line,
                self.TIME_WIDTH,
                y,
                max(
                    self.TIME_WIDTH + 100,
                    self.schedule_canvas.winfo_width()
                ),
                y
            )

            self.schedule_canvas.coords(
                self.current_time_text,
                self.TIME_WIDTH - 8,
                y
            )

        except tk.TclError:
            return

        self.after(
            30000,
            self.update_current_time
        )

    # ========================================================
    # TASKS TAB
    # ========================================================

    def show_tasks(self):

        self.current_view = "tasks"
        self.set_active_nav(2)

        self.clear_header_controls()

        self.add_header_button(
            "＋ Add Task",
            self.add_task
        )

        self.page_title.configure(
            text="Scheduled Tasks"
        )

        self.clear_body()

        container = tk.Frame(
            self.body,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        container.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # FILTER BAR
        # ----------------------------------------------------

        filters = tk.Frame(
            container,
            bg=self.PANEL,
            height=65
        )

        filters.pack(
            fill="x",
            padx=15
        )

        filters.pack_propagate(False)

        tk.Label(
            filters,
            text="Search",
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            side="left"
        )

        search_var = tk.StringVar()

        search = tk.Entry(
            filters,
            textvariable=search_var,
            bg=self.CARD,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 9),
            width=28
        )

        search.pack(
            side="left",
            padx=(8, 18),
            ipady=7
        )

        tk.Label(
            filters,
            text="Status",
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            side="left"
        )

        status_var = tk.StringVar(
            value="All"
        )

        status_combo = ttk.Combobox(
            filters,
            textvariable=status_var,
            values=[
                "All",
                "Planned",
                "In Progress",
                "Completed",
                "Cancelled"
            ],
            state="readonly",
            style="DayFlow.TCombobox",
            width=15
        )

        status_combo.pack(
            side="left",
            padx=8
        )

        tk.Label(
            filters,
            text="Date",
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            side="left",
            padx=(15, 0)
        )

        date_filter_var = tk.StringVar(
            value="All Dates"
        )

        date_combo = ttk.Combobox(
            filters,
            textvariable=date_filter_var,
            values=[
                "All Dates",
                "Today",
                "Upcoming"
            ],
            state="readonly",
            style="DayFlow.TCombobox",
            width=15
        )

        date_combo.pack(
            side="left",
            padx=8
        )

        # ----------------------------------------------------
        # TREE
        # ----------------------------------------------------

        table_frame = tk.Frame(
            container,
            bg=self.PANEL
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        columns = (
            "date",
            "task",
            "time",
            "duration",
            "priority",
            "status",
            "productivity"
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="DayFlow.Treeview",
            selectmode="browse"
        )

        headings = {
            "date": "DATE",
            "task": "TASK",
            "time": "TIME",
            "duration": "DURATION",
            "priority": "PRIORITY",
            "status": "STATUS",
            "productivity": "PRODUCTIVITY"
        }

        widths = {
            "date": 125,
            "task": 280,
            "time": 180,
            "duration": 100,
            "priority": 100,
            "status": 125,
            "productivity": 120
        }

        for column in columns:

            tree.heading(
                column,
                text=headings[column]
            )

            tree.column(
                column,
                width=widths[column],
                anchor="w"
            )

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=tree.yview
        )

        xscroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=tree.xview
        )

        tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        tree.pack(
            side="top",
            fill="both",
            expand=True
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        tree.tag_configure(
            "completed",
            foreground="#86efac"
        )

        tree.tag_configure(
            "progress",
            foreground="#fbbf24"
        )

        tree.tag_configure(
            "cancelled",
            foreground="#f87171"
        )

        def refresh():

            for item in tree.get_children():
                tree.delete(item)

            search_text = (
                search_var.get()
                .strip()
                .lower()
            )

            selected_status = (
                status_var.get()
            )

            selected_date_filter = (
                date_filter_var.get()
            )

            sorted_tasks = sorted(
                self.tasks,
                key=lambda t: (
                    t.get("date", ""),
                    time_to_minutes(
                        t.get(
                            "start_time",
                            ""
                        )
                    ) or 0
                )
            )

            for task in sorted_tasks:

                title = task.get(
                    "title",
                    ""
                )

                description = task.get(
                    "description",
                    ""
                )

                if search_text:

                    searchable = (
                        title
                        + " "
                        + description
                    ).lower()

                    if search_text not in searchable:
                        continue

                status = task.get(
                    "status",
                    "Planned"
                )

                if (
                    selected_status != "All"
                    and status != selected_status
                ):
                    continue

                task_date = parse_date(
                    task.get(
                        "date",
                        ""
                    )
                )

                if selected_date_filter == "Today":

                    if task_date != date.today():
                        continue

                elif selected_date_filter == "Upcoming":

                    if (
                        not task_date
                        or task_date < date.today()
                    ):
                        continue

                duration = duration_minutes(
                    task.get(
                        "start_time",
                        ""
                    ),
                    task.get(
                        "end_time",
                        ""
                    )
                )

                productivity = task.get(
                    "productivity",
                    ""
                )

                productivity_text = (
                    f"{productivity}/10"
                    if productivity
                    else "—"
                )

                tag = ""

                if status == "Completed":
                    tag = "completed"
                elif status == "In Progress":
                    tag = "progress"
                elif status == "Cancelled":
                    tag = "cancelled"

                tree.insert(
                    "",
                    "end",
                    iid=task["id"],
                    values=(
                        task.get(
                            "date",
                            ""
                        ),
                        title,
                        (
                            f"{format_time(task.get('start_time', ''))}"
                            f" → "
                            f"{format_time(task.get('end_time', ''))}"
                        ),
                        duration_text(duration),
                        task.get(
                            "priority",
                            "Medium"
                        ),
                        status,
                        productivity_text
                    ),
                    tags=(tag,)
                )

        search_var.trace_add(
            "write",
            lambda *args: refresh()
        )

        status_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: refresh()
        )

        date_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: refresh()
        )

        def edit_selected(event=None):

            selection = tree.selection()

            if not selection:
                return

            self.edit_task(
                selection[0]
            )

        tree.bind(
            "<Double-Button-1>",
            edit_selected
        )

        # Right click
        tree.bind(
            "<Button-3>",
            lambda e:
            self.table_context_menu(
                e,
                tree
            )
        )

        refresh()

        # Buttons below
        action_bar = tk.Frame(
            container,
            bg=self.PANEL,
            height=52
        )

        action_bar.pack(
            fill="x",
            padx=15,
            pady=(0, 12)
        )

        tk.Button(
            action_bar,
            text="Edit Selected",
            command=lambda:
            edit_selected(),
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD_2,
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(
            side="left"
        )

        tk.Button(
            action_bar,
            text="Change Status",
            command=lambda:
            self.change_selected_status(tree),
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD_2,
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(
            side="left",
            padx=8
        )

        tk.Button(
            action_bar,
            text="Delete",
            command=lambda:
            self.delete_selected_task(tree),
            bg="#351a22",
            fg="#fca5a5",
            activebackground="#4a202b",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(
            side="left"
        )

        self.refresh_sidebar()

    # ========================================================
    # STATUS
    # ========================================================

    def change_selected_status(self, tree):

        selection = tree.selection()

        if not selection:
            messagebox.showinfo(
                "Select Task",
                "Please select a task first."
            )
            return

        task_id = selection[0]

        task = next(
            (
                t for t in self.tasks
                if t["id"] == task_id
            ),
            None
        )

        if not task:
            return

        window = tk.Toplevel(self)

        window.title(
            "Change Status"
        )

        window.geometry(
            "350x230"
        )

        window.configure(
            bg=self.PANEL
        )

        window.transient(self)
        window.grab_set()
        window.resizable(False, False)

        tk.Label(
            window,
            text="Task Status",
            font=("Segoe UI", 16, "bold"),
            fg=self.TEXT,
            bg=self.PANEL
        ).pack(
            pady=(25, 5)
        )

        tk.Label(
            window,
            text=task.get(
                "title",
                ""
            ),
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.PANEL,
            wraplength=280
        ).pack(
            pady=(0, 15)
        )

        status_var = tk.StringVar(
            value=task.get(
                "status",
                "Planned"
            )
        )

        combo = ttk.Combobox(
            window,
            textvariable=status_var,
            values=[
                "Planned",
                "In Progress",
                "Completed",
                "Cancelled"
            ],
            state="readonly",
            style="DayFlow.TCombobox",
            width=22
        )

        combo.pack(
            pady=5
        )

        def save():

            new_status = status_var.get()

            task["status"] = new_status

            if new_status != "Completed":

                task["productivity"] = ""
                task["review"] = ""

            write_csv(
                TASKS_FILE,
                TASK_FIELDS,
                self.tasks
            )

            window.destroy()

            self.show_tasks()

        tk.Button(
            window,
            text="Save Status",
            command=save,
            bg=self.BLUE,
            fg="white",
            activebackground=self.BLUE_DARK,
            relief="flat",
            bd=0,
            padx=20,
            pady=9,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        ).pack(
            pady=18
        )

    # ========================================================
    # CONTEXT MENUS
    # ========================================================

    def task_context_menu(
        self,
        event,
        task_id
    ):

        menu = tk.Menu(
            self,
            tearoff=0,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.BLUE,
            activeforeground="white"
        )

        menu.add_command(
            label="Edit Task",
            command=lambda:
            self.edit_task(task_id)
        )

        menu.add_command(
            label="Change Status",
            command=lambda:
            self.quick_status(task_id)
        )

        menu.add_separator()

        menu.add_command(
            label="Delete Task",
            command=lambda:
            self.delete_task(task_id)
        )

        try:
            menu.tk_popup(
                event.x_root,
                event.y_root
            )
        finally:
            menu.grab_release()

    def table_context_menu(
        self,
        event,
        tree
    ):

        row = tree.identify_row(
            event.y
        )

        if not row:
            return

        tree.selection_set(row)

        menu = tk.Menu(
            self,
            tearoff=0,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.BLUE,
            activeforeground="white"
        )

        menu.add_command(
            label="Edit Task",
            command=lambda:
            self.edit_task(row)
        )

        menu.add_command(
            label="Change Status",
            command=lambda:
            self.change_selected_status(tree)
        )

        menu.add_separator()

        menu.add_command(
            label="Delete Task",
            command=lambda:
            self.delete_task(row)
        )

        try:
            menu.tk_popup(
                event.x_root,
                event.y_root
            )
        finally:
            menu.grab_release()

    def quick_status(self, task_id):

        task = next(
            (
                t for t in self.tasks
                if t["id"] == task_id
            ),
            None
        )

        if not task:
            return

        statuses = [
            "Planned",
            "In Progress",
            "Completed",
            "Cancelled"
        ]

        current = task.get(
            "status",
            "Planned"
        )

        next_index = (
            statuses.index(current) + 1
        ) % len(statuses)

        new_status = statuses[next_index]

        task["status"] = new_status

        write_csv(
            TASKS_FILE,
            TASK_FIELDS,
            self.tasks
        )

        self.show_schedule()

    # ========================================================
    # DELETE
    # ========================================================

    def delete_selected_task(self, tree):

        selection = tree.selection()

        if not selection:
            messagebox.showinfo(
                "Select Task",
                "Please select a task first."
            )
            return

        self.delete_task(
            selection[0]
        )

    def delete_task(self, task_id):

        task = next(
            (
                t for t in self.tasks
                if t["id"] == task_id
            ),
            None
        )

        if not task:
            return

        confirm = messagebox.askyesno(
            "Delete Task",
            f"Delete '{task.get('title', 'Untitled')}'?"
        )

        if not confirm:
            return

        self.tasks = [
            t for t in self.tasks
            if t["id"] != task_id
        ]

        self.productivity = [
            p for p in self.productivity
            if p.get("task_id") != task_id
        ]

        write_csv(
            TASKS_FILE,
            TASK_FIELDS,
            self.tasks
        )

        write_csv(
            PRODUCTIVITY_FILE,
            PRODUCTIVITY_FIELDS,
            self.productivity
        )

        if self.current_view == "tasks":
            self.show_tasks()
        else:
            self.show_schedule()

    # ========================================================
    # TASK DIALOG
    # ========================================================

    def add_task(
        self,
        selected_date=None,
        start_hour=None
    ):

        self.open_task_dialog(
            selected_date=(
                selected_date
                or self.selected_date
            ),
            start_hour=start_hour
        )

    def edit_task(self, task_id):

        task = next(
            (
                t for t in self.tasks
                if t["id"] == task_id
            ),
            None
        )

        if task:
            self.open_task_dialog(
                task=task
            )

    def open_task_dialog(
        self,
        selected_date=None,
        start_hour=None,
        task=None
    ):

        editing = task is not None

        if selected_date is None:

            if task:
                selected_date = parse_date(
                    task.get(
                        "date",
                        ""
                    )
                )
            else:
                selected_date = self.selected_date

        window = tk.Toplevel(self)

        window.title(
            "Edit Task"
            if editing
            else "Schedule Task"
        )

        window.geometry(
            "580x690"
        )

        window.configure(
            bg=self.PANEL
        )

        window.transient(self)
        window.grab_set()
        window.resizable(False, False)

        tk.Label(
            window,
            text=(
                "Edit Task"
                if editing
                else "Schedule Task"
            ),
            font=("Segoe UI", 18, "bold"),
            fg=self.TEXT,
            bg=self.PANEL
        ).pack(
            anchor="w",
            padx=28,
            pady=(25, 3)
        )

        tk.Label(
            window,
            text="Set the exact time and details for this task.",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            anchor="w",
            padx=28,
            pady=(0, 15)
        )

        form = tk.Frame(
            window,
            bg=self.PANEL
        )

        form.pack(
            fill="both",
            expand=True,
            padx=28
        )

        # TITLE
        self.form_label(
            form,
            "Task"
        )

        title_var = tk.StringVar(
            value=(
                task.get(
                    "title",
                    ""
                )
                if task
                else ""
            )
        )

        title_entry = tk.Entry(
            form,
            textvariable=title_var,
            bg=self.CARD,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 10)
        )

        title_entry.pack(
            fill="x",
            ipady=9,
            pady=(5, 13)
        )

        # DATE + PRIORITY
        row1 = tk.Frame(
            form,
            bg=self.PANEL
        )

        row1.pack(
            fill="x",
            pady=(0, 13)
        )

        left = tk.Frame(
            row1,
            bg=self.PANEL
        )

        left.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.form_label(
            left,
            "Date"
        )

        date_var = tk.StringVar(
            value=(
                task.get(
                    "date",
                    ""
                )
                if task
                else selected_date.strftime(
                    "%Y-%m-%d"
                )
            )
        )

        tk.Entry(
            left,
            textvariable=date_var,
            bg=self.CARD,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 10)
        ).pack(
            fill="x",
            ipady=8,
            pady=(5, 0)
        )

        right = tk.Frame(
            row1,
            bg=self.PANEL
        )

        right.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

        self.form_label(
            right,
            "Priority"
        )

        priority_var = tk.StringVar(
            value=(
                task.get(
                    "priority",
                    "Medium"
                )
                if task
                else "Medium"
            )
        )

        ttk.Combobox(
            right,
            textvariable=priority_var,
            values=[
                "Low",
                "Medium",
                "High"
            ],
            state="readonly",
            style="DayFlow.TCombobox"
        ).pack(
            fill="x",
            pady=(5, 0)
        )

        # TIME
        row2 = tk.Frame(
            form,
            bg=self.PANEL
        )

        row2.pack(
            fill="x",
            pady=(0, 3)
        )

        left = tk.Frame(
            row2,
            bg=self.PANEL
        )

        left.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.form_label(
            left,
            "Start Time"
        )

        if task:

            start_default = format_time(
                task.get(
                    "start_time",
                    ""
                )
            )

        elif start_hour is not None:

            start_default = datetime(
                2000,
                1,
                1,
                start_hour,
                0
            ).strftime(
                "%I:%M %p"
            )

        else:
            start_default = "09:00 AM"

        start_var = tk.StringVar(
            value=start_default
        )

        tk.Entry(
            left,
            textvariable=start_var,
            bg=self.CARD,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 10)
        ).pack(
            fill="x",
            ipady=8,
            pady=(5, 0)
        )

        right = tk.Frame(
            row2,
            bg=self.PANEL
        )

        right.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

        self.form_label(
            right,
            "End Time"
        )

        if task:

            end_default = format_time(
                task.get(
                    "end_time",
                    ""
                )
            )

        elif start_hour is not None:

            end_hour = min(
                23,
                start_hour + 1
            )

            end_default = datetime(
                2000,
                1,
                1,
                end_hour,
                0
            ).strftime(
                "%I:%M %p"
            )

        else:
            end_default = "10:00 AM"

        end_var = tk.StringVar(
            value=end_default
        )

        tk.Entry(
            right,
            textvariable=end_var,
            bg=self.CARD,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 10)
        ).pack(
            fill="x",
            ipady=8,
            pady=(5, 0)
        )

        tk.Label(
            form,
            text="Time format: 09:30 AM, 02:00 PM, etc.",
            font=("Segoe UI", 8),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            anchor="w",
            pady=(5, 13)
        )

        # DESCRIPTION
        self.form_label(
            form,
            "Description"
        )

        description = tk.Text(
            form,
            height=9,
            bg=self.CARD,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            selectbackground=self.BLUE,
            relief="flat",
            bd=0,
            wrap="word",
            font=("Segoe UI", 10),
            padx=10,
            pady=10
        )

        description.pack(
            fill="both",
            expand=True,
            pady=(5, 15)
        )

        if task:

            description.insert(
                "1.0",
                task.get(
                    "description",
                    ""
                )
            )

        # STATUS WHEN EDITING
        status_var = tk.StringVar(
            value=(
                task.get(
                    "status",
                    "Planned"
                )
                if task
                else "Planned"
            )
        )

        if editing:

            self.form_label(
                form,
                "Status"
            )

            ttk.Combobox(
                form,
                textvariable=status_var,
                values=[
                    "Planned",
                    "In Progress",
                    "Completed",
                    "Cancelled"
                ],
                state="readonly",
                style="DayFlow.TCombobox"
            ).pack(
                fill="x",
                pady=(5, 15)
            )

        # BUTTONS
        buttons = tk.Frame(
            form,
            bg=self.PANEL
        )

        buttons.pack(
            fill="x",
            pady=(0, 20)
        )

        def save():

            title = title_var.get().strip()
            date_value = date_var.get().strip()
            start = start_var.get().strip().upper()
            end = end_var.get().strip().upper()
            desc = description.get(
                "1.0",
                "end-1c"
            ).strip()

            priority = priority_var.get()

            if not title:

                messagebox.showwarning(
                    "Missing Task",
                    "Please enter a task name.",
                    parent=window
                )
                return

            valid_date = parse_date(
                date_value
            )

            if not valid_date:

                messagebox.showwarning(
                    "Invalid Date",
                    "Use YYYY-MM-DD.",
                    parent=window
                )
                return

            start_minutes = time_to_minutes(
                start
            )

            end_minutes = time_to_minutes(
                end
            )

            if (
                start_minutes is None
                or end_minutes is None
            ):

                messagebox.showwarning(
                    "Invalid Time",
                    "Example: 09:30 AM",
                    parent=window
                )
                return

            if end_minutes <= start_minutes:

                messagebox.showwarning(
                    "Invalid Time Range",
                    "End time must be after start time.",
                    parent=window
                )
                return

            # Overlap warning
            overlaps = []

            for existing in self.tasks:

                if editing and (
                    existing["id"]
                    == task["id"]
                ):
                    continue

                if existing.get(
                    "date"
                ) != date_value:
                    continue

                es = time_to_minutes(
                    existing.get(
                        "start_time",
                        ""
                    )
                )

                ee = time_to_minutes(
                    existing.get(
                        "end_time",
                        ""
                    )
                )

                if (
                    es is not None
                    and ee is not None
                    and start_minutes < ee
                    and end_minutes > es
                ):
                    overlaps.append(
                        existing
                    )

            if overlaps:

                names = "\n".join(
                    f"• {x.get('title', 'Untitled')} "
                    f"({format_time(x.get('start_time', ''))} - "
                    f"{format_time(x.get('end_time', ''))})"
                    for x in overlaps
                )

                proceed = messagebox.askyesno(
                    "Time Conflict",
                    "This task overlaps with:\n\n"
                    + names
                    + "\n\nSave anyway?",
                    parent=window
                )

                if not proceed:
                    return

            if editing:

                task["date"] = date_value
                task["title"] = title
                task["start_time"] = format_time(
                    start
                )
                task["end_time"] = format_time(
                    end
                )
                task["description"] = desc
                task["priority"] = priority
                task["status"] = status_var.get()

            else:

                self.tasks.append({
                    "id": new_id(),
                    "date": date_value,
                    "title": title,
                    "start_time": format_time(
                        start
                    ),
                    "end_time": format_time(
                        end
                    ),
                    "description": desc,
                    "priority": priority,
                    "status": "Planned",
                    "productivity": "",
                    "review": "",
                    "created_at": datetime.now().isoformat()
                })

            write_csv(
                TASKS_FILE,
                TASK_FIELDS,
                self.tasks
            )

            self.selected_date = valid_date

            self.calendar_year = valid_date.year
            self.calendar_month = valid_date.month

            window.destroy()

            self.show_schedule()

        tk.Button(
            buttons,
            text="Cancel",
            command=window.destroy,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD_2,
            relief="flat",
            bd=0,
            padx=18,
            pady=9,
            cursor="hand2"
        ).pack(
            side="right"
        )

        tk.Button(
            buttons,
            text="Save Task",
            command=save,
            bg=self.BLUE,
            fg="white",
            activebackground=self.BLUE_DARK,
            relief="flat",
            bd=0,
            padx=20,
            pady=9,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        ).pack(
            side="right",
            padx=8
        )

        title_entry.focus_set()

    def form_label(
        self,
        parent,
        text
    ):

        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            anchor="w"
        )

    # ========================================================
    # PRODUCTIVITY
    # ========================================================

    def show_productivity(self):

        self.current_view = "productivity"
        self.set_active_nav(3)

        self.clear_header_controls()

        self.page_title.configure(
            text="Productivity"
        )

        self.clear_body()

        completed = [
            t for t in self.tasks
            if t.get("status")
            == "Completed"
        ]

        ratings = []

        for task in completed:

            try:
                ratings.append(
                    float(
                        task.get(
                            "productivity",
                            ""
                        )
                    )
                )
            except Exception:
                pass

        average = (
            sum(ratings) / len(ratings)
            if ratings
            else 0
        )

        total = len(self.tasks)

        completion = (
            len(completed)
            / total
            * 100
            if total
            else 0
        )

        planned = sum(
            duration_minutes(
                t.get(
                    "start_time",
                    ""
                ),
                t.get(
                    "end_time",
                    ""
                )
            )
            for t in self.tasks
        )

        completed_time = sum(
            duration_minutes(
                t.get(
                    "start_time",
                    ""
                ),
                t.get(
                    "end_time",
                    ""
                )
            )
            for t in completed
        )

        top = tk.Frame(
            self.body,
            bg=self.PANEL
        )

        top.pack(
            fill="x"
        )

        cards = tk.Frame(
            top,
            bg=self.PANEL
        )

        cards.pack(
            fill="x",
            padx=15,
            pady=15
        )

        self.stat_card(
            cards,
            "TOTAL TASKS",
            str(total),
            self.BLUE
        )

        self.stat_card(
            cards,
            "COMPLETED",
            str(len(completed)),
            self.GREEN
        )

        self.stat_card(
            cards,
            "COMPLETION",
            f"{completion:.0f}%",
            self.PURPLE
        )

        self.stat_card(
            cards,
            "AVG PRODUCTIVITY",
            (
                f"{average:.1f}/10"
                if average
                else "—"
            ),
            self.ORANGE
        )

        tk.Label(
            top,
            text=(
                f"Planned time: "
                f"{duration_text(planned)}"
                f"     •     "
                f"Completed time: "
                f"{duration_text(completed_time)}"
            ),
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.PANEL
        ).pack(
            anchor="w",
            padx=30,
            pady=(0, 18)
        )

        review_frame = tk.Frame(
            self.body,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        review_frame.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            review_frame,
            text="Completed Tasks & Reviews",
            font=("Segoe UI", 13, "bold"),
            fg=self.TEXT,
            bg=self.PANEL
        ).pack(
            anchor="w",
            padx=20,
            pady=18
        )

        canvas = tk.Canvas(
            review_frame,
            bg=self.PANEL,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            review_frame,
            orient="vertical",
            command=canvas.yview
        )

        inner = tk.Frame(
            canvas,
            bg=self.PANEL
        )

        inner.bind(
            "<Configure>",
            lambda e:
            canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window(
            (0, 0),
            window=inner,
            anchor="nw"
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        for task in reversed(completed):

            card = tk.Frame(
                inner,
                bg=self.CARD,
                highlightbackground=self.BORDER,
                highlightthickness=1
            )

            card.pack(
                fill="x",
                padx=20,
                pady=6
            )

            left = tk.Frame(
                card,
                bg=self.CARD
            )

            left.pack(
                side="left",
                fill="both",
                expand=True,
                padx=15,
                pady=12
            )

            tk.Label(
                left,
                text=task.get(
                    "title",
                    ""
                ),
                font=("Segoe UI", 10, "bold"),
                fg=self.TEXT,
                bg=self.CARD
            ).pack(
                anchor="w"
            )

            tk.Label(
                left,
                text=(
                    format_date(
                        task.get(
                            "date",
                            ""
                        )
                    )
                    + " • "
                    + format_time(
                        task.get(
                            "start_time",
                            ""
                        )
                    )
                    + " → "
                    + format_time(
                        task.get(
                            "end_time",
                            ""
                        )
                    )
                ),
                font=("Segoe UI", 8),
                fg=self.MUTED,
                bg=self.CARD
            ).pack(
                anchor="w",
                pady=(3, 5)
            )

            if task.get("review"):

                tk.Label(
                    left,
                    text=task["review"],
                    font=("Segoe UI", 9),
                    fg="#cbd5e1",
                    bg=self.CARD,
                    wraplength=700,
                    justify="left"
                ).pack(
                    anchor="w"
                )

            tk.Label(
                card,
                text=(
                    task.get(
                        "productivity",
                        "—"
                    )
                    + "/10"
                ),
                font=("Segoe UI", 16, "bold"),
                fg=self.ORANGE,
                bg=self.CARD
            ).pack(
                side="right",
                padx=25
            )

    def stat_card(
        self,
        parent,
        label,
        value,
        color
    ):

        card = tk.Frame(
            parent,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            height=85
        )

        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        card.pack_propagate(False)

        tk.Frame(
            card,
            bg=color,
            width=4
        ).pack(
            side="left",
            fill="y"
        )

        inner = tk.Frame(
            card,
            bg=self.CARD
        )

        inner.pack(
            fill="both",
            expand=True,
            padx=12
        )

        tk.Label(
            inner,
            text=label,
            font=("Segoe UI", 8, "bold"),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(
            anchor="w",
            pady=(12, 2)
        )

        tk.Label(
            inner,
            text=value,
            font=("Segoe UI", 15, "bold"),
            fg=self.TEXT,
            bg=self.CARD
        ).pack(
            anchor="w"
        )

    # ========================================================
    # SIDEBAR STATS
    # ========================================================

    def refresh_sidebar(self):

        if not hasattr(
            self,
            "side_stats"
        ):
            return

        date_string = self.selected_date.strftime(
            "%Y-%m-%d"
        )

        tasks = [
            t for t in self.tasks
            if t.get("date") == date_string
        ]

        planned = sum(
            duration_minutes(
                t.get(
                    "start_time",
                    ""
                ),
                t.get(
                    "end_time",
                    ""
                )
            )
            for t in tasks
        )

        completed = sum(
            1
            for t in tasks
            if t.get("status")
            == "Completed"
        )

        intervals = []

        for task in tasks:

            start = time_to_minutes(
                task.get(
                    "start_time",
                    ""
                )
            )

            end = time_to_minutes(
                task.get(
                    "end_time",
                    ""
                )
            )

            if (
                start is not None
                and end is not None
                and end > start
            ):

                intervals.append(
                    (start, end)
                )

        intervals.sort()

        merged = []

        for start, end in intervals:

            if not merged:

                merged.append(
                    [start, end]
                )

            elif start <= merged[-1][1]:

                merged[-1][1] = max(
                    merged[-1][1],
                    end
                )

            else:

                merged.append(
                    [start, end]
                )

        busy = sum(
            end - start
            for start, end in merged
        )

        free = max(
            0,
            1440 - busy
        )

        self.side_stats["tasks"].configure(
            text=str(len(tasks))
        )

        self.side_stats["planned"].configure(
            text=duration_text(planned)
        )

        self.side_stats["free"].configure(
            text=duration_text(free)
        )

        self.side_stats["completed"].configure(
            text=str(completed)
        )


# ============================================================
# TIME LABEL HELPER
# ============================================================

def format_minutes_label(minutes):

    minutes = int(minutes) % 1440

    hour = minutes // 60
    minute = minutes % 60

    dt = datetime(
        2000,
        1,
        1,
        hour,
        minute
    )

    return dt.strftime(
        "%I:%M %p"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app = DayFlow()

    app.mainloop()
