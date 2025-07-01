import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import json
import os
import pyautogui
from pynput import keyboard, mouse
from datetime import datetime

RECORDINGS_FOLDER = "recordings"
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)


def generate_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(RECORDINGS_FOLDER, f"recording_{timestamp}.json")


def show_toast(root, message, duration=2000):
    toast = tk.Toplevel(root)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.geometry(f"+{root.winfo_rootx() + 100}+{root.winfo_rooty() + 100}")
    label = ttk.Label(toast, text=message, background="#222", foreground="#fff", font=("Segoe UI", 12), padding=10)
    label.pack()
    toast.after(duration, toast.destroy)


class AutoStepApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoIt - Step Recorder")
        self.geometry("500x400")
        self.resizable(True, True)
        # self.iconbitmap("icon.ico")
        self.minsize(500, 420)

        self.recording = False
        self.paused = False
        self.events = []
        self.start_time = None
        self.filename = None
        self.screen_width, self.screen_height = pyautogui.size()

        self.repeat_count = tk.IntVar(value=1)
        self.repeat_delay = tk.DoubleVar(value=1.0)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both")

        self.create_menu()
        self.create_initial_screen()

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        menubar.add_command(label="About", command=self.show_about)

        helpmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="Help", command=self.show_help)
        helpmenu.add_command(label="Shortcuts", command=self.show_shortcuts)

    def show_about(self):
        messagebox.showinfo(
            "About", "Auto Step Recorder\nCreated by Mgregchi\nhttps://github.com/Mgregchi/AutoIt\n\n2025 © Mgregchi\nLicensed under the MIT License")

    def show_help(self):
        messagebox.showinfo(
            "Help", "Use Start Recording to record actions.\nUse Play Recording to replay.\nUse menus for info.")

    def show_shortcuts(self):
        msg = ("Recording shortcuts:\n"
               "- F9 : Pause/Resume recording\n"
               "- Esc: Stop recording\n\n"
               "Playback:\n"
               "- Select recording file and click Play")
        messagebox.showinfo("Shortcuts", msg)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def create_initial_screen(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Auto Step Recorder",
                  font=("Segoe UI", 18)).pack(pady=30)

        ttk.Button(self.main_frame, text="Start Recording",
                   command=self.start_recording_flow).pack(pady=10)
        ttk.Button(self.main_frame, text="Play Recording",
                   command=self.playback_flow).pack(pady=10)

    ############### RECORDING FLOW ################

    def start_recording_flow(self):
        self.filename = generate_filename()
        self.show_countdown(5, self.start_recording, on_cancel=self.create_initial_screen)

    def show_countdown(self, seconds, callback, on_cancel=None):
        self.clear_frame()
        self.countdown_cancelled = False
        self.countdown_label = ttk.Label(
            self.main_frame, text="", font=("Segoe UI", 48))
        self.countdown_label.pack(expand=True)
        cancel_btn = ttk.Button(self.main_frame, text="Cancel", command=self.cancel_countdown)
        cancel_btn.pack(pady=10)
        self._countdown_callback = callback
        self._countdown_on_cancel = on_cancel

        def countdown(n):
            if self.countdown_cancelled:
                if on_cancel:
                    self.after(0, on_cancel)
                return
            if n > 0:
                self.countdown_label.config(text=str(n))
                self.after(1000, countdown, n-1)
            else:
                self.countdown_label.config(text="0")
                self.after(500, lambda: self.after(0, callback))

        countdown(seconds)

    def cancel_countdown(self):
        self.countdown_cancelled = True

    def bind_recording_keys(self):
        self.unbind_all('<F9>')
        self.unbind_all('<Escape>')
        self.bind_all('<F9>', lambda e: self.toggle_pause())
        self.bind_all('<Escape>', lambda e: self.stop_recording())

    def unbind_recording_keys(self):
        self.unbind_all('<F9>')
        self.unbind_all('<Escape>')

    def start_recording(self):
        self.recording = True
        self.paused = False
        self.events = []
        self.screen_width, self.screen_height = pyautogui.size()
        self.start_time = time.time()

        self.clear_frame()
        # Top bar with back button
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill="x")
        back_btn = ttk.Button(top_frame, text="←", command=self.confirm_cancel_recording)
        back_btn.pack(side="left", padx=5, pady=5)
        ttk.Label(self.main_frame, text="Recording...",
                  font=("Segoe UI", 16)).pack(pady=10)

        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(pady=20)

        self.pause_btn = ttk.Button(
            controls_frame, text="Pause", command=self.toggle_pause)
        self.pause_btn.grid(row=0, column=0, padx=10)

        stop_btn = ttk.Button(controls_frame, text="Stop",
                              command=self.stop_recording)
        stop_btn.grid(row=0, column=1, padx=10)

        restart_btn = ttk.Button(
            self.main_frame, text="Restart Recording", command=self.restart_recording)
        restart_btn.pack(pady=5)

        self.log_text = tk.Text(self.main_frame, height=10, state="disabled")
        self.log_text.pack(padx=10, pady=10, fill="x")

        self.bind_recording_keys()
        threading.Thread(target=self.record, daemon=True).start()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause")
        self.log(f"{'⏸️ Paused' if self.paused else '▶️ Resumed'} recording.")

    def restart_recording(self):
        if self.recording:
            self.recording = False
        self.start_recording_flow()

    def confirm_cancel_recording(self):
        if messagebox.askyesno("Cancel Recording", "Cancel and discard this recording?" ):
            self.recording = False
            self.unbind_recording_keys()
            self.create_initial_screen()

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def elapsed_time(self):
        return time.time() - self.start_time

    def stop_recording(self):
        self.recording = False
        self.unbind_recording_keys()

    def record(self):
        self.log("🎙️ Recording started. Press F9 to pause/resume, Esc to stop.")

        def on_press(key):
            if not self.recording or self.paused:
                return
            if key == keyboard.Key.esc:
                self.recording = False
                return False
            if key == keyboard.Key.f9:
                self.paused = not self.paused
                self.pause_btn.config(
                    text="Resume" if self.paused else "Pause")
                self.log(
                    f"{'⏸️ Paused' if self.paused else '▶️ Resumed'} recording.")
                return
            try:
                k = key.char
            except AttributeError:
                k = str(key)
            self.events.append(
                {'type': 'key_press', 'time': self.elapsed_time(), 'key': k})

        def on_release(key):
            if not self.recording or self.paused:
                return
            try:
                k = key.char
            except AttributeError:
                k = str(key)
            self.events.append(
                {'type': 'key_release', 'time': self.elapsed_time(), 'key': k})

        def on_move(x, y):
            if not self.recording or self.paused:
                return
            self.events.append({'type': 'mouse_move', 'time': self.elapsed_time(),
                                'nx': x / self.screen_width, 'ny': y / self.screen_height})

        def on_click(x, y, button, pressed):
            if not self.recording or self.paused:
                return
            self.events.append({'type': 'mouse_click', 'time': self.elapsed_time(),
                                'nx': x / self.screen_width, 'ny': y / self.screen_height,
                                'button': str(button), 'pressed': pressed})

        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
        keyboard_listener = keyboard.Listener(
            on_press=on_press, on_release=on_release)

        mouse_listener.start()
        keyboard_listener.start()

        while self.recording:
            time.sleep(0.1)

        mouse_listener.stop()
        keyboard_listener.stop()
        mouse_listener.join()
        keyboard_listener.join()

        self.log("Recording stopped.")
        self.save_recording()

    def save_recording(self):
        meta = {
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'events': self.events
        }
        try:
            with open(self.filename, 'w') as f:
                json.dump(meta, f, indent=2)
            self.log(f"Saved recording to: {os.path.basename(self.filename)}")
            self.after(100, lambda: show_toast(self, "Recording completed!", 2000))
            self.after(2100, lambda: self.playback_flow(select_file=os.path.basename(self.filename)))
        except Exception as e:
            self.log(f"Error saving file: {e}")
            messagebox.showerror("Error", f"Could not save recording:\n{e}")
            self.create_initial_screen()

    ################## PLAYBACK FLOW #################

    def playback_flow(self, select_file=None):
        self.clear_frame()
        self.unbind_all('<F9>')
        self.unbind_all('<Escape>')
        self.bind_all('<Escape>', lambda e: self.create_initial_screen())
        # Top row: back
        top_row = ttk.Frame(self.main_frame)
        top_row.pack(fill="x", pady=5)
        back_btn = ttk.Button(top_row, text="←", command=self.create_initial_screen)
        back_btn.pack(side="left", padx=5)
        # Label
        ttk.Label(self.main_frame, text="Select recording to play",
                  font=("Segoe UI", 12)).pack(pady=2)
        # Scrollable file list
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill="x", padx=10)
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        self.recordings_listbox = tk.Listbox(list_frame, height=6, yscrollcommand=list_scroll.set)
        list_scroll.config(command=self.recordings_listbox.yview)
        self.recordings_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        self.recordings_listbox.bind("<<ListboxSelect>>", self.recording_selected)
        recordings = [f for f in os.listdir(RECORDINGS_FOLDER) if f.endswith(".json")]
        for rec in recordings:
            self.recordings_listbox.insert(tk.END, rec)
        self.controls_row = ttk.Frame(self.main_frame)
        self.repeat_label = ttk.Label(self.controls_row, text="Repeat count:")
        self.repeat_entry = ttk.Entry(self.controls_row, textvariable=self.repeat_count, width=5)
        repeat_help = ttk.Button(self.controls_row, text="?", width=2, command=lambda: self.show_field_help('repeat'))
        self.delay_label = ttk.Label(self.controls_row, text="Delay (sec):")
        self.delay_entry = ttk.Entry(self.controls_row, textvariable=self.repeat_delay, width=5)
        delay_help = ttk.Button(self.controls_row, text="?", width=2, command=lambda: self.show_field_help('delay'))
        self.repeat_label.grid(row=0, column=0, padx=2)
        self.repeat_entry.grid(row=0, column=1, padx=2)
        repeat_help.grid(row=0, column=2, padx=2)
        self.delay_label.grid(row=0, column=3, padx=2)
        self.delay_entry.grid(row=0, column=4, padx=2)
        delay_help.grid(row=0, column=5, padx=2)
        self.controls_row.pack_forget()  # Hide initially
        # Row for select custom, play button, and delete button
        btn_row = ttk.Frame(self.main_frame)
        btn_row.pack(fill="x", pady=5)
        select_icon = tk.PhotoImage(width=16, height=16)  # Placeholder icon
        select_btn = ttk.Button(btn_row, text="Select custom", image=select_icon, compound="left", command=self.select_playback_file)
        select_btn.image = select_icon
        select_btn.pack(side="left", padx=5)
        self.play_btn = ttk.Button(btn_row, text="Play Recording", command=self.play_selected_recording)
        self.play_btn.pack(side="left", padx=5)
        self.play_btn['state'] = 'disabled'
        self.delete_btn = ttk.Button(btn_row, text="Delete selection", command=self.delete_selected_recording)
        self.delete_btn.pack(side="left", padx=5)
        self.delete_btn.pack_forget()  # Hide initially
        # Log area (smaller, scrollable)
        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill="x", padx=10, pady=2)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical")
        self.play_log = tk.Text(log_frame, height=4, state="disabled", yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.play_log.yview)
        self.play_log.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        if select_file:
            try:
                idx = recordings.index(select_file)
                self.recordings_listbox.selection_set(idx)
                self.recordings_listbox.see(idx)
                self.filename = os.path.join(RECORDINGS_FOLDER, select_file)
                self.play_btn['state'] = 'normal'
                self.controls_row.pack(pady=5)
                self.log_play(f"Selected file: {select_file}")
            except ValueError:
                pass

    def show_field_help(self, field):
        if field == 'repeat':
            messagebox.showinfo("Repeat Count", "Number of times to repeat playback. Must be a positive integer.")
        elif field == 'delay':
            messagebox.showinfo("Delay", "Delay in seconds between repeats. Must be a non-negative number.")

    def recording_selected(self, event):
        selection = self.recordings_listbox.curselection()
        if not selection:
            self.filename = None
            self.play_btn['state'] = 'disabled'
            self.controls_row.pack_forget()
            self.delete_btn.pack_forget()
            return
        fname = self.recordings_listbox.get(selection[0])
        self.filename = os.path.join(RECORDINGS_FOLDER, fname)
        self.log_play(f"Selected file: {fname}")
        self.play_btn['state'] = 'normal'
        self.controls_row.pack_forget()
        self.controls_row.pack(before=self.play_log.master, fill="x", pady=5)
        self.delete_btn.pack(side="left", padx=5)

    def select_playback_file(self):
        file = filedialog.askopenfilename(initialdir=RECORDINGS_FOLDER,
                                          filetypes=[("JSON Files", "*.json")],
                                          title="Select Recording File")
        if file:
            fname = os.path.basename(file)
            # Add to list if not present
            if fname not in self.recordings_listbox.get(0, tk.END):
                self.recordings_listbox.insert(tk.END, fname)
            idx = self.recordings_listbox.get(0, tk.END).index(fname)
            self.recordings_listbox.selection_clear(0, tk.END)
            self.recordings_listbox.selection_set(idx)
            self.recordings_listbox.see(idx)
            self.filename = file
            self.log_play(f"Selected file: {fname}")
            self.play_btn['state'] = 'normal'
            self.controls_row.pack_forget()
            self.controls_row.pack(before=self.play_log.master, fill="x", pady=5)
            self.delete_btn.pack_forget()  # Hide delete when custom

    def play_selected_recording(self):
        if not self.filename:
            self.log_play("No recording selected!")
            messagebox.showwarning(
                "No selection", "Please select a recording from the list or choose a file.")
            return
        try:
            repeats = int(self.repeat_count.get())
            delay = float(self.repeat_delay.get())
            if repeats < 1 or delay < 0:
                raise ValueError
        except Exception:
            messagebox.showerror(
                "Input error", "Repeat count must be positive integer and delay must be non-negative number.")
            return
        self.show_countdown(5, lambda: self.start_playback_ui(repeats, delay), on_cancel=self.playback_flow)

    def start_playback_ui(self, repeat_count, repeat_delay):
        self.clear_frame()
        # Top bar with back button
        top_row = ttk.Frame(self.main_frame)
        top_row.pack(fill="x", pady=5)
        back_btn = ttk.Button(top_row, text="←", command=self.playback_flow)
        back_btn.pack(side="left", padx=5)
        # Controls: Pause/Resume, Stop
        controls = ttk.Frame(self.main_frame)
        controls.pack(pady=10)
        self.playback_paused = False
        self.pause_btn = ttk.Button(controls, text="Pause", command=self.toggle_playback_pause)
        self.pause_btn.grid(row=0, column=0, padx=5)
        stop_btn = ttk.Button(controls, text="Stop", command=self.stop_playback)
        stop_btn.grid(row=0, column=1, padx=5)
        # Log area
        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill="x", padx=10, pady=2)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical")
        self.play_log = tk.Text(log_frame, height=4, state="disabled", yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.play_log.yview)
        self.play_log.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        # Start playback in thread
        self._stop_playback = False
        threading.Thread(target=self.playback, args=(repeat_count, repeat_delay), daemon=True).start()

    def toggle_playback_pause(self):
        self.playback_paused = not self.playback_paused
        self.pause_btn.config(text="Resume" if self.playback_paused else "Pause")
        self.log_play("⏸️ Paused playback." if self.playback_paused else "▶️ Resumed playback.")

    def stop_playback(self):
        self._stop_playback = True
        self.log_play("⏹️ Playback stopped.")
        self.after(500, self.playback_flow)

    def playback(self, repeat_count, repeat_delay):
        self.log_play(f"Playback starting...")
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.log_play(f"Error loading recording: {e}")
            messagebox.showerror("Error", f"Could not load recording:\n{e}")
            self.play_btn['state'] = 'disabled'
            return

        current_w, current_h = pyautogui.size()
        recorded_w = data.get('screen_width')
        recorded_h = data.get('screen_height')
        events = data.get('events', [])

        if (recorded_w, recorded_h) != (current_w, current_h):
            self.log_play(
                f"⚠️ Resolution mismatch: Recorded {recorded_w}x{recorded_h}, Current {current_w}x{current_h}")
            res = messagebox.askyesno("Resolution Mismatch",
                                      "Screen resolution differs from recording. Continue playback?")
            if not res:
                self.log_play("Playback cancelled by user.")
                return

        for i in range(repeat_count):
            if self._stop_playback:
                break
            self.log_play(f"Playback iteration {i + 1} of {repeat_count}")
            last_time = 0
            for event in events:
                if self._stop_playback:
                    break
                while self.playback_paused:
                    time.sleep(0.1)
                    if self._stop_playback:
                        break
                delay_time = event['time'] - last_time
                time.sleep(delay_time)
                last_time = event['time']

                etype = event['type']
                if etype == 'mouse_move':
                    x = int(event['nx'] * current_w)
                    y = int(event['ny'] * current_h)
                    pyautogui.moveTo(x, y, duration=0)
                elif etype == 'mouse_click':
                    x = int(event['nx'] * current_w)
                    y = int(event['ny'] * current_h)
                    pyautogui.moveTo(x, y, duration=0)
                    btn = event['button'].split('.')[-1]
                    if event['pressed']:
                        pyautogui.mouseDown(button=btn)
                    else:
                        pyautogui.mouseUp(button=btn)
                elif etype == 'key_press':
                    try:
                        pyautogui.keyDown(event['key'])
                    except Exception:
                        pass
                elif etype == 'key_release':
                    try:
                        pyautogui.keyUp(event['key'])
                    except Exception:
                        pass

            if i < repeat_count - 1 and not self._stop_playback:
                self.log_play(
                    f"Waiting {repeat_delay} seconds before next repeat...")
                for _ in range(int(repeat_delay * 10)):
                    if self._stop_playback:
                        break
                    time.sleep(0.1)

        if not self._stop_playback:
            self.log_play("Playback finished.")
        self.after(1000, self.playback_flow)

    def log_play(self, msg):
        def update_log():
            if hasattr(self, "play_log") and self.play_log.winfo_exists():
                self.play_log.config(state="normal")
                self.play_log.insert(tk.END, msg + "\n")
                self.play_log.see(tk.END)
                self.play_log.config(state="disabled")
        self.after(0, update_log)

    def delete_selected_recording(self):
        selection = self.recordings_listbox.curselection()
        if not selection:
            return
        fname = self.recordings_listbox.get(selection[0])
        full_path = os.path.join(RECORDINGS_FOLDER, fname)
        if messagebox.askyesno("Delete Recording", f"Are you sure you want to delete '{fname}'?"):
            try:
                os.remove(full_path)
                self.recordings_listbox.delete(selection[0])
                self.log_play(f"Deleted file: {fname}")
                self.filename = None
                self.play_btn['state'] = 'disabled'
                self.controls_row.pack_forget()
                self.delete_btn.pack_forget()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete file:\n{e}")


if __name__ == "__main__":
    app = AutoStepApp()
    app.mainloop() 