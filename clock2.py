#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import time
import math
import subprocess


class ClockApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Circle Timer & Stopwatch')
        self.geometry('480x560')
        self.resizable(True, True)  # Allow minimize / maximize

        self.mode = 'timer'

        self.timer_total = 0
        self.timer_remaining = 0.0
        self.timer_running = False

        self.stopwatch_running = False
        self.stopwatch_elapsed = 0.0

        self.last_tick = None
        self.laps = []

        self._display_extent = 0.0
        self._target_extent = 0.0
        self._arc_width = 26

        self.create_ui()
        self.center_window()
        self.update_clock()

    # ---------------- UI ---------------- #

    def create_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        top = ttk.Frame(self)
        top.pack(fill='x', pady=10)

        self.mode_var = tk.StringVar(value='Timer')

        ttk.Radiobutton(
            top, text='Timer',
            value='Timer',
            variable=self.mode_var,
            command=self.on_mode_change
        ).pack(side='left', padx=(28, 12))

        ttk.Radiobutton(
            top, text='Stopwatch',
            value='Stopwatch',
            variable=self.mode_var,
            command=self.on_mode_change
        ).pack(side='left')

        self.canvas = tk.Canvas(
            self,
            width=400,
            height=400,
            bg='#FAFAFA',
            highlightthickness=0
        )
        self.canvas.pack(pady=6)

        cx, cy, r = 200, 200, 160
        shadow_offset = 6

        self.canvas.create_oval(
            cx-r+shadow_offset, cy-r+shadow_offset,
            cx+r+shadow_offset, cy+r+shadow_offset,
            fill='#E8EAF6', outline=''
        )

        self.bg_ring = self.canvas.create_oval(
            cx-r, cy-r, cx+r, cy+r,
            outline='#ECEFF1',
            width=self._arc_width
        )

        self.arc = self.canvas.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=90,
            extent=0,
            style='arc',
            width=self._arc_width,
            outline='#2979FF'
        )

        inner_r = r - self._arc_width - 8
        self.canvas.create_oval(
            cx-inner_r, cy-inner_r,
            cx+inner_r, cy+inner_r,
            fill='white',
            outline=''
        )

        self.time_text = self.canvas.create_text(
            cx, cy-8,
            text=self.format_time_timer(0),
            font=('Helvetica', 36, 'bold'),
            fill='#263238'
        )

        self.sub_text = self.canvas.create_text(
            cx, cy+36,
            text='Timer',
            font=('Helvetica', 12),
            fill='#546E7A'
        )

        controls = ttk.Frame(self)
        controls.pack(fill='x', pady=8)

        self.start_btn = ttk.Button(
            controls, text='Start', command=self.start
        )
        self.start_btn.pack(side='left', padx=(12, 6))

        self.pause_btn = ttk.Button(
            controls, text='Pause', command=self.pause
        )
        self.pause_btn.pack(side='left', padx=6)

        self.reset_btn = ttk.Button(
            controls, text='Reset', command=self.reset
        )
        self.reset_btn.pack(side='left')

        setframe = ttk.Frame(self)
        setframe.pack(fill='x', pady=6)

        ttk.Label(
            setframe,
            text='Set time (HH:MM:SS or MM:SS or SS):'
        ).pack(side='left', padx=(12, 6))

        self.set_entry = ttk.Entry(setframe, width=14)
        self.set_entry.pack(side='left')

        self.set_btn = ttk.Button(
            setframe, text='Set', command=self.set_time
        )
        self.set_btn.pack(side='left', padx=6)

        lapframe = ttk.Frame(self)
        lapframe.pack(fill='both', expand=True, pady=4, padx=8)

        self.lap_btn = ttk.Button(
            lapframe, text='Lap', command=self.lap
        )
        self.lap_btn.pack(side='left', padx=8, pady=4)

        self.lap_list = tk.Listbox(
            lapframe,
            height=6,
            activestyle='none'
        )
        self.lap_list.pack(side='left', fill='both', expand=True, padx=6, pady=4)

        self.protocol('WM_DELETE_WINDOW', self.on_close)

    # ---------------- Core Logic ---------------- #

    def start(self):
        if self.mode == 'timer':
            if self.timer_remaining <= 0:
                self.timer_remaining = float(self.timer_total)
            self.timer_running = True
        else:
            self.stopwatch_running = True

        self.last_tick = time.time()

    def pause(self):
        if self.mode == 'timer':
            self.timer_running = False
        else:
            self.stopwatch_running = False

    def reset(self):
        if self.mode == 'timer':
            self.timer_running = False
            self.timer_remaining = float(self.timer_total)
        else:
            self.stopwatch_running = False
            self.stopwatch_elapsed = 0.0
            self.laps.clear()
            self.lap_list.delete(0, 'end')

    def set_time(self):
        s = self.set_entry.get().strip()
        if not s:
            return

        parts = s.split(':')

        try:
            if len(parts) == 1:
                sec = int(parts[0])
            elif len(parts) == 2:
                sec = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                sec = (
                    int(parts[0]) * 3600 +
                    int(parts[1]) * 60 +
                    int(parts[2])
                )
            else:
                return
        except Exception:
            return

        if sec < 0:
            return

        self.timer_total = sec
        self.timer_remaining = float(sec)
        self.timer_running = False

        self.mode_var.set('Timer')
        self.on_mode_change()

    def lap(self):
        if self.mode == 'stopwatch' and self.stopwatch_running:
            t = self.stopwatch_elapsed
            self.laps.append(t)
            self.lap_list.insert('end', self.format_time_stopwatch(t))

    # ---------------- Update Loop ---------------- #

    def update_clock(self):
        now = time.time()

        if self.last_tick is None:
            self.last_tick = now

        dt = now - self.last_tick

        if self.mode == 'timer' and self.timer_running:
            self.timer_remaining -= dt
            if self.timer_remaining <= 0:
                self.timer_remaining = 0.0
                self.timer_running = False
                try:
                    subprocess.call(
                        ['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga']
                    )
                except Exception:
                    try:
                        self.bell()
                    except Exception:
                        pass

        if self.mode == 'stopwatch' and self.stopwatch_running:
            self.stopwatch_elapsed += dt

        self.last_tick = now

        if self.mode == 'timer':
            display = int(math.ceil(self.timer_remaining))
            pct = 1.0 - (
                self.timer_remaining / max(1.0, self.timer_total)
            )
            self.canvas.itemconfig(
                self.time_text,
                text=self.format_time_timer(display)
            )
        else:
            displayf = self.stopwatch_elapsed
            pct = min(self.stopwatch_elapsed / 3600.0, 1.0)
            self.canvas.itemconfig(
                self.time_text,
                text=self.format_time_stopwatch(displayf)
            )

        self._target_extent = pct * -360
        self._display_extent += (
            (self._target_extent - self._display_extent)
            * min(1.0, dt * 10.0)
        )

        self.canvas.itemconfig(
            self.arc,
            extent=int(self._display_extent)
        )

        self.after(33, self.update_clock)

    # ---------------- Helpers ---------------- #

    def format_time_timer(self, secs):
        if secs < 0:
            secs = 0

        if secs >= 3600:
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            return f"{h}:{m:02d}:{s:02d}"
        else:
            m = secs // 60
            s = secs % 60
            return f"{m:02d}:{s:02d}"

    def format_time_stopwatch(self, total_seconds):
        ms = int((total_seconds - int(total_seconds)) * 100)
        secs = int(total_seconds)

        if secs >= 3600:
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            return f"{h}:{m:02d}:{s:02d}.{ms:02d}"
        else:
            m = secs // 60
            s = secs % 60
            return f"{m:02d}:{s:02d}.{ms:02d}"

    def on_mode_change(self):
        m = self.mode_var.get()
        self.mode = 'timer' if m == 'Timer' else 'stopwatch'
        self.reset()
        self.canvas.itemconfig(
            self.sub_text,
            text=self.mode.capitalize()
        )

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

    def on_close(self):
        self.destroy()


if __name__ == '__main__':
    app = ClockApp()
    app.mainloop()

