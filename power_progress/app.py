from __future__ import annotations

import calendar
from collections.abc import Callable
from datetime import date, datetime, timedelta
import math
import tkinter as tk
from tkinter import messagebox, ttk

from .countdown import (
    DATETIME_FORMAT,
    CountdownEvent,
    CountdownStore,
    countdown_snapshot,
)


class ClockTimePickerDialog(tk.Toplevel):
    CLOCK_SIZE = 320
    CENTER = CLOCK_SIZE // 2
    CLOCK_PADDING = 18
    OUTER_RADIUS = 122
    INNER_RADIUS = 82
    MINUTE_RADIUS = 112

    BACKGROUND = "#ffffff"
    SURFACE = "#eef2f7"
    SURFACE_MUTED = "#f3f4f6"
    ACCENT = "#2563eb"
    ACCENT_DARK = "#1d4ed8"
    TEXT = "#111827"
    TEXT_MUTED = "#6b7280"
    SELECTED_TEXT = "#ffffff"

    def __init__(self, parent: tk.Toplevel, initial_hour: int, initial_minute: int, on_select: Callable[[int, int], None]) -> None:
        super().__init__(parent)

        self.title("选择具体时间")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_select = on_select
        self.hour = initial_hour
        self.minute = initial_minute
        self.active_field = "hour"
        self.hour_text = tk.StringVar()
        self.minute_text = tk.StringVar()

        self._build_layout()
        self._refresh_display()
        self._draw_clock()

        self.update_idletasks()
        x = parent.winfo_rootx() + max((parent.winfo_width() - self.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - self.winfo_height()) // 2, 0)
        self.geometry(f"+{x}+{y}")

    def _build_layout(self) -> None:
        self.configure(bg=self.BACKGROUND)

        root = tk.Frame(self, bg=self.BACKGROUND, padx=20, pady=18)
        root.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(root, text="选择具体时间", bg=self.BACKGROUND, fg=self.TEXT, anchor="w", font=("Microsoft YaHei UI", 11, "bold"))
        title.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        display = tk.Frame(root, bg=self.BACKGROUND)
        display.grid(row=1, column=0, sticky="ew")
        display.columnconfigure(0, weight=1)
        display.columnconfigure(2, weight=1)

        self.hour_label = tk.Label(display, textvariable=self.hour_text, width=2, bg=self.ACCENT, fg=self.SELECTED_TEXT, font=("Times New Roman", 42), padx=18, pady=4)
        self.hour_label.grid(row=0, column=0, sticky="e")
        self.hour_label.bind("<Button-1>", lambda _event: self._set_active_field("hour"))

        tk.Label(display, text=":", bg=self.BACKGROUND, fg=self.TEXT, font=("Times New Roman", 36), padx=10).grid(row=0, column=1)

        self.minute_label = tk.Label(display, textvariable=self.minute_text, width=2, bg=self.SURFACE_MUTED, fg=self.TEXT, font=("Times New Roman", 42), padx=18, pady=4)
        self.minute_label.grid(row=0, column=2, sticky="w")
        self.minute_label.bind("<Button-1>", lambda _event: self._set_active_field("minute"))

        self.canvas = tk.Canvas(
            root,
            width=self.CLOCK_SIZE,
            height=self.CLOCK_SIZE,
            background=self.BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.grid(row=2, column=0, pady=(20, 16))
        self.canvas.bind("<Button-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag)

        actions = tk.Frame(root, bg=self.BACKGROUND)
        actions.grid(row=3, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)

        cancel = tk.Button(actions, text="取消", command=self.destroy, bd=0, bg=self.BACKGROUND, fg=self.ACCENT, activebackground=self.SURFACE_MUTED, activeforeground=self.ACCENT_DARK, font=("Microsoft YaHei UI", 11, "bold"), padx=10, pady=4)
        cancel.grid(row=0, column=1, padx=(0, 20))

        ok = tk.Button(actions, text="确定", command=self._confirm, bd=0, bg=self.BACKGROUND, fg=self.ACCENT, activebackground=self.SURFACE_MUTED, activeforeground=self.ACCENT_DARK, font=("Microsoft YaHei UI", 11, "bold"), padx=10, pady=4)
        ok.grid(row=0, column=2)

    def _set_active_field(self, field: str) -> None:
        self.active_field = field
        self._refresh_display()
        self._draw_clock()

    def _start_drag(self, event: tk.Event) -> None:
        self._update_from_pointer(event.x, event.y)

    def _drag(self, event: tk.Event) -> None:
        self._update_from_pointer(event.x, event.y)

    def _update_from_pointer(self, x: int, y: int) -> None:
        angle = math.atan2(y - self.CENTER, x - self.CENTER) + math.pi / 2
        if angle < 0:
            angle += math.tau

        if self.active_field == "hour":
            hour_on_ring = round(angle / math.tau * 12) % 12
            distance = math.hypot(x - self.CENTER, y - self.CENTER)
            self.hour = hour_on_ring + (12 if distance < (self.OUTER_RADIUS + self.INNER_RADIUS) / 2 else 0)
        else:
            self.minute = round(angle / math.tau * 60) % 60

        self._refresh_display()
        self._draw_clock()

    def _draw_clock(self) -> None:
        self.canvas.delete("all")
        center = self.CENTER
        self.canvas.create_oval(
            self.CLOCK_PADDING,
            self.CLOCK_PADDING,
            self.CLOCK_SIZE - self.CLOCK_PADDING,
            self.CLOCK_SIZE - self.CLOCK_PADDING,
            fill=self.SURFACE,
            outline="",
        )

        if self.active_field == "hour":
            self._draw_hour_ticks()
            endpoint = self._hour_endpoint()
        else:
            self._draw_minute_ticks()
            endpoint = self._minute_endpoint()

        self.canvas.create_line(center, center, endpoint[0], endpoint[1], fill=self.ACCENT, width=4, capstyle=tk.ROUND)
        self.canvas.create_oval(endpoint[0] - 26, endpoint[1] - 26, endpoint[0] + 26, endpoint[1] + 26, fill=self.ACCENT, outline="")
        self.canvas.create_oval(center - 5, center - 5, center + 5, center + 5, fill=self.ACCENT, outline="")

        if self.active_field == "hour":
            label = str(self.hour)
            x, y = endpoint
        else:
            label = f"{self.minute:02d}"
            x, y = endpoint
        self.canvas.create_text(x, y, text=label, fill=self.SELECTED_TEXT, font=("Times New Roman", 16, "bold"))

    def _draw_hour_ticks(self) -> None:
        for value in range(24):
            radius = self.OUTER_RADIUS if value < 12 else self.INNER_RADIUS
            index = value % 12
            x, y = self._point_for_index(index, radius, 12)
            if value == self.hour:
                continue
            self.canvas.create_text(x, y, text=str(value), fill=self.TEXT, font=("Times New Roman", 15))

    def _draw_minute_ticks(self) -> None:
        for value in range(0, 60, 5):
            x, y = self._point_for_index(value, self.MINUTE_RADIUS, 60)
            if value == self.minute:
                continue
            self.canvas.create_text(x, y, text=f"{value:02d}", fill=self.TEXT, font=("Times New Roman", 15))

    def _refresh_display(self) -> None:
        self.hour_text.set(f"{self.hour:02d}")
        self.minute_text.set(f"{self.minute:02d}")
        self.hour_label.configure(
            bg=self.ACCENT if self.active_field == "hour" else self.SURFACE_MUTED,
            fg=self.SELECTED_TEXT if self.active_field == "hour" else self.TEXT,
        )
        self.minute_label.configure(
            bg=self.ACCENT if self.active_field == "minute" else self.SURFACE_MUTED,
            fg=self.SELECTED_TEXT if self.active_field == "minute" else self.TEXT,
        )

    def _confirm(self) -> None:
        self.on_select(self.hour, self.minute)
        self.destroy()

    def _hour_endpoint(self) -> tuple[float, float]:
        radius = self.INNER_RADIUS if self.hour >= 12 else self.OUTER_RADIUS
        return self._point_for_index(self.hour % 12, radius, 12)

    def _minute_endpoint(self) -> tuple[float, float]:
        return self._point_for_index(self.minute, self.MINUTE_RADIUS, 60)

    def _point_for_index(self, index: int, radius: int, divisions: int) -> tuple[float, float]:
        angle = index / divisions * math.tau - math.pi / 2
        return self.CENTER + math.cos(angle) * radius, self.CENTER + math.sin(angle) * radius


class DateTimePickerDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, initial: datetime, on_select: Callable[[datetime], None]) -> None:
        super().__init__(parent)

        self.title("选择具体日期")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_select = on_select
        self.selected_date = initial.date()
        self.visible_year = initial.year
        self.visible_month = initial.month
        self.has_specific_time = initial.hour != 0 or initial.minute != 0
        self.selected_hour = initial.hour
        self.selected_minute = initial.minute
        self.time_button_text = tk.StringVar()
        self.day_buttons: list[tk.Button] = []

        self._build_layout()
        self._render_calendar()
        self._render_time_choice()

        self.update_idletasks()
        x = parent.winfo_rootx() + max((parent.winfo_width() - self.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - self.winfo_height()) // 2, 0)
        self.geometry(f"+{x}+{y}")

    def _build_layout(self) -> None:
        self.configure(bg="#ffffff")

        root = tk.Frame(self, bg="#ffffff", padx=16, pady=16)
        root.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(root, bg="#ffffff")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        tk.Button(header, text="<", width=4, command=self._previous_month, bg="#f3f4f6", fg="#111827", bd=0, activebackground="#e5e7eb").grid(row=0, column=0, sticky="w")
        self.month_label = tk.Label(header, text="", anchor="center", bg="#ffffff", fg="#111827", font=("Microsoft YaHei UI", 11, "bold"))
        self.month_label.grid(row=0, column=1, sticky="ew", padx=8)
        tk.Button(header, text=">", width=4, command=self._next_month, bg="#f3f4f6", fg="#111827", bd=0, activebackground="#e5e7eb").grid(row=0, column=2, sticky="e")

        calendar_frame = tk.Frame(root, bg="#ffffff")
        calendar_frame.grid(row=1, column=0, sticky="ew", pady=(12, 14))

        for column, name in enumerate(("一", "二", "三", "四", "五", "六", "日")):
            tk.Label(calendar_frame, text=name, anchor="center", bg="#ffffff", fg="#6b7280", width=4).grid(row=0, column=column, padx=2, pady=(0, 5))

        for row in range(6):
            for column in range(7):
                button = tk.Button(calendar_frame, text="", width=4, bd=0, bg="#f9fafb", fg="#111827", activebackground="#dbeafe", activeforeground="#111827", font=("Times New Roman", 10))
                button.grid(row=row + 1, column=column, padx=2, pady=2)
                self.day_buttons.append(button)

        time_frame = tk.Frame(root, bg="#ffffff")
        time_frame.grid(row=2, column=0, sticky="ew")
        time_frame.columnconfigure(0, weight=1)

        tk.Label(time_frame, text="默认 00:00", bg="#ffffff", fg="#6b7280").grid(row=0, column=0, sticky="w")
        self.time_button = tk.Button(time_frame, textvariable=self.time_button_text, command=self._open_clock_picker, bd=0, bg="#f3f4f6", fg="#111827", activebackground="#dbeafe", padx=12, pady=6)
        self.time_button.grid(row=0, column=1, sticky="e", padx=(14, 0))

        actions = tk.Frame(root, bg="#ffffff")
        actions.grid(row=3, column=0, sticky="e", pady=(16, 0))
        tk.Button(actions, text="取消", command=self.destroy, bd=0, bg="#ffffff", fg="#2563eb", activebackground="#f3f4f6", padx=10, pady=4).grid(row=0, column=0, padx=(0, 8))
        tk.Button(actions, text="确定", command=self._confirm, bd=0, bg="#ffffff", fg="#2563eb", activebackground="#f3f4f6", padx=10, pady=4).grid(row=0, column=1)

    def _render_calendar(self) -> None:
        self.month_label.configure(text=f"{self.visible_year} 年 {self.visible_month:02d} 月")
        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(self.visible_year, self.visible_month)
        days = [day for week in weeks for day in week]

        for index, button in enumerate(self.day_buttons):
            if index >= len(days):
                button.configure(text="", state=tk.DISABLED, command=lambda: None)
                continue

            day = days[index]
            is_current_month = day.month == self.visible_month
            is_selected = day == self.selected_date

            button.configure(
                text=str(day.day),
                state=tk.NORMAL if is_current_month else tk.DISABLED,
                bg="#2563eb" if is_selected else "#f9fafb",
                fg="#ffffff" if is_selected else "#111827",
                disabledforeground="#9ca3af",
                command=lambda selected=day: self._select_date(selected),
            )

    def _select_date(self, selected: date) -> None:
        self.selected_date = selected
        self._render_calendar()

    def _previous_month(self) -> None:
        if self.visible_month == 1:
            self.visible_year -= 1
            self.visible_month = 12
        else:
            self.visible_month -= 1
        self._render_calendar()

    def _next_month(self) -> None:
        if self.visible_month == 12:
            self.visible_year += 1
            self.visible_month = 1
        else:
            self.visible_month += 1
        self._render_calendar()

    def _render_time_choice(self) -> None:
        if self.has_specific_time:
            self.time_button_text.set(f"具体时间 {self.selected_hour:02d}:{self.selected_minute:02d}")
        else:
            self.time_button_text.set("设置具体时间")

    def _open_clock_picker(self) -> None:
        ClockTimePickerDialog(self, self.selected_hour, self.selected_minute, self._set_time)

    def _set_time(self, hour: int, minute: int) -> None:
        self.selected_hour = hour
        self.selected_minute = minute
        self.has_specific_time = True
        self._render_time_choice()

    def _confirm(self) -> None:
        hour = self.selected_hour if self.has_specific_time else 0
        minute = self.selected_minute if self.has_specific_time else 0
        selected = datetime(
            self.selected_date.year,
            self.selected_date.month,
            self.selected_date.day,
            hour,
            minute,
        )
        self.on_select(selected)
        self.destroy()


class CountdownApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("POWER PROGRESS")
        self.minsize(760, 480)
        self.geometry("860x560")

        self.store = CountdownStore()
        self.events = self._load_events()
        self.event_widgets: dict[str, dict[str, ttk.Label | ttk.Frame]] = {}

        self._configure_styles()
        self._build_layout()
        self._render_events()
        self._tick()

    def _configure_styles(self) -> None:
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.configure(bg="#f6f8fb")

        self.style.configure("Main.TFrame", background="#f6f8fb")
        self.style.configure("Panel.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        self.style.configure("Title.TLabel", background="#f6f8fb", foreground="#111827", font=("Times New Roman", 18, "bold"))
        self.style.configure("Muted.TLabel", background="#f6f8fb", foreground="#6b7280", font=("Microsoft YaHei UI", 10))
        self.style.configure("PanelTitle.TLabel", background="#ffffff", foreground="#111827", font=("Microsoft YaHei UI", 12, "bold"))
        self.style.configure("Time.TLabel", background="#ffffff", foreground="#0f766e", font=("Times New Roman", 18, "bold"))
        self.style.configure("Past.Time.TLabel", background="#ffffff", foreground="#b45309", font=("Times New Roman", 18, "bold"))
        self.style.configure("Meta.TLabel", background="#ffffff", foreground="#6b7280", font=("Microsoft YaHei UI", 9))
        self.style.configure("Danger.TButton", foreground="#991b1b")
        self.style.configure("Accent.TButton", foreground="#ffffff", background="#2563eb")
        self.style.map("Accent.TButton", background=[("active", "#1d4ed8")])

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="Main.TFrame", padding=24)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        ttk.Label(root, text="POWER PROGRESS", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(root, text="动态倒数日", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 16))

        body = ttk.Frame(root, style="Main.TFrame")
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_form(body)
        self._build_list(body)

    def _build_form(self, parent: ttk.Frame) -> None:
        form = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        form.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text="新建倒数日", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")

        ttk.Label(form, text="名称", background="#ffffff").grid(row=1, column=0, sticky="w", pady=(18, 4))
        self.title_var = tk.StringVar()
        title_entry = ttk.Entry(form, textvariable=self.title_var, width=28)
        title_entry.grid(row=2, column=0, sticky="ew")
        title_entry.focus_set()

        ttk.Label(form, text="目标时间", background="#ffffff").grid(row=3, column=0, sticky="w", pady=(14, 4))
        self.selected_target = (datetime.now() + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.target_var = tk.StringVar(value=self.selected_target.strftime(DATETIME_FORMAT))

        target_picker = ttk.Frame(form, style="Panel.TFrame")
        target_picker.grid(row=4, column=0, sticky="ew")
        target_picker.columnconfigure(0, weight=1)
        ttk.Entry(target_picker, textvariable=self.target_var, width=20, state="readonly").grid(row=0, column=0, sticky="ew")
        ttk.Button(target_picker, text="选择", command=self._open_target_picker).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(form, text="日期必选，具体时间可选；未设置时为 00:00", style="Meta.TLabel").grid(row=5, column=0, sticky="w", pady=(6, 16))
        ttk.Button(form, text="添加", style="Accent.TButton", command=self._add_event).grid(row=6, column=0, sticky="ew")

        storage = str(self.store.path)
        ttk.Label(form, text=f"数据保存于\n{storage}", style="Meta.TLabel", wraplength=230).grid(row=7, column=0, sticky="sw", pady=(28, 0))

    def _build_list(self, parent: ttk.Frame) -> None:
        list_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        list_panel.grid(row=0, column=1, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        ttk.Label(list_panel, text="倒数日列表", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")

        self.canvas = tk.Canvas(list_panel, highlightthickness=0, background="#ffffff")
        scrollbar = ttk.Scrollbar(list_panel, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas, style="Panel.TFrame")
        self.scroll_frame.columnconfigure(0, weight=1)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(14, 0))

        self.scroll_frame.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._sync_canvas_width)

    def _load_events(self) -> list[CountdownEvent]:
        try:
            return self.store.load()
        except Exception as exc:
            messagebox.showwarning("读取失败", f"无法读取倒数日数据，将从空列表开始。\n{exc}")
            return []

    def _render_events(self) -> None:
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        self.event_widgets.clear()

        if not self.events:
            empty = ttk.Label(
                self.scroll_frame,
                text="还没有倒数日",
                background="#ffffff",
                foreground="#6b7280",
                font=("Microsoft YaHei UI", 12),
                anchor="center",
                padding=36,
            )
            empty.grid(row=0, column=0, sticky="ew")
            return

        for row, event in enumerate(self.events):
            self._render_event(row, event)

    def _render_event(self, row: int, event: CountdownEvent) -> None:
        frame = ttk.Frame(self.scroll_frame, style="Panel.TFrame", padding=14)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)

        title = ttk.Label(frame, text=event.title, style="PanelTitle.TLabel")
        title.grid(row=0, column=0, sticky="w")

        target = ttk.Label(frame, text=f"目标：{event.target.strftime(DATETIME_FORMAT)}", style="Meta.TLabel")
        target.grid(row=1, column=0, sticky="w", pady=(5, 0))

        time_label = ttk.Label(frame, text="", style="Time.TLabel")
        time_label.grid(row=0, column=1, rowspan=2, sticky="e", padx=(18, 12))

        delete_button = ttk.Button(frame, text="删除", style="Danger.TButton", command=lambda event_id=event.id: self._delete_event(event_id))
        delete_button.grid(row=0, column=2, rowspan=2, sticky="e")

        self.event_widgets[event.id] = {"frame": frame, "time": time_label}

    def _add_event(self) -> None:
        title = self.title_var.get().strip()
        if not title:
            messagebox.showinfo("需要名称", "请先输入倒数日名称。")
            return

        self.events.append(CountdownEvent(title=title, target=self.selected_target))
        self.events.sort(key=lambda event: event.target)
        self._save_events()
        self.title_var.set("")
        self._render_events()
        self._tick()

    def _open_target_picker(self) -> None:
        DateTimePickerDialog(self, self.selected_target, self._set_selected_target)

    def _set_selected_target(self, target: datetime) -> None:
        self.selected_target = target
        self.target_var.set(target.strftime(DATETIME_FORMAT))

    def _delete_event(self, event_id: str) -> None:
        self.events = [event for event in self.events if event.id != event_id]
        self._save_events()
        self._render_events()

    def _save_events(self) -> None:
        try:
            self.store.save(self.events)
        except Exception as exc:
            messagebox.showerror("保存失败", f"无法保存倒数日数据。\n{exc}")

    def _tick(self) -> None:
        now = datetime.now()
        for event in self.events:
            widgets = self.event_widgets.get(event.id)
            if not widgets:
                continue
            snapshot = countdown_snapshot(event.target, now)
            time_label = widgets["time"]
            if isinstance(time_label, ttk.Label):
                time_label.configure(
                    text=snapshot.label(),
                    style="Past.Time.TLabel" if snapshot.is_past else "Time.TLabel",
                )
        self.after(1000, self._tick)

    def _sync_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_canvas_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)


def main() -> None:
    app = CountdownApp()
    app.mainloop()


if __name__ == "__main__":
    main()
