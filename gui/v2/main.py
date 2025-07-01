import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import json
import os
import pyautogui
from pynput import keyboard, mouse

RECORDINGS_FOLDER = "recordings"
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)


class AutoStepApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Step Recorder")
        self.geometry("500x400")
        self.resizable(False, False)

        # State variables
        self.recording = False
        self.paused = False
        self.events = []
        self.start_time = None
        self.filename = None
        self.screen_width, self.screen_height = pyautogui.size()

        # Playback settings
        self.repeat_count = tk.IntVar(value=1)
        self.repeat_delay = tk.DoubleVar(value=1.0)

        # Widgets containers
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both")

        self.create_menu()
        self.create_initial_screen()

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        helpmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About", command=self.show_about)
        helpmenu.add_command(label="Shortcuts", command=self.show_shortcuts)

    def show_about(self):
        messagebox.showinfo(
            "About", "Auto Step Recorder\nCreated by Mgregchi\nhttps://github.com/Mgregchi/AutoStepRecorder\n\n2025 © Mgregchi\nLicensed under the MIT License")

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
        # Ask user where to save recording
        file = filedialog.asksaveasfilename(
            initialdir=RECORDINGS_FOLDER,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Recording As"
        )
        if not file:
            return
        self.filename = file
        self.show_countdown(5, self.start_recording)

    def show_countdown(self, seconds, callback):
        self.clear_frame()
        self.countdown_label = ttk.Label(
            self.main_frame, text="", font=("Segoe UI", 48))
        self.countdown_label.pack(expand=True)

        def countdown(n):
            if n > 0:
                self.countdown_label.config(text=str(n))
                self.after(1000, countdown, n-1)
            else:
                callback()

        countdown(seconds)

    def start_recording(self):
        self.recording = True
        self.paused = False
        self.events = []
        self.screen_width, self.screen_height = pyautogui.size()
        self.start_time = time.time()

        self.clear_frame()
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
        restart_btn.pack(pady=10)

        self.log_text = tk.Text(self.main_frame, height=10, state="disabled")
        self.log_text.pack(padx=10, pady=10, fill="x")

        # Start listeners in background thread
        threading.Thread(target=self.record).start()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause")
        self.log(f"{'⏸️ Paused' if self.paused else '▶️ Resumed'} recording.")

    def restart_recording(self):
        if self.recording:
            self.recording = False
        self.start_recording_flow()

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def elapsed_time(self):
        return time.time() - self.start_time

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
        self.create_initial_screen()

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
        except Exception as e:
            self.log(f"Error saving file: {e}")
            messagebox.showerror("Error", f"Could not save recording:\n{e}")

    ################## PLAYBACK FLOW #################

    def playback_flow(self):
        self.clear_frame()

        ttk.Label(self.main_frame, text="Select a recording to play",
                  font=("Segoe UI", 14)).pack(pady=10)

        # Listbox with recordings
        self.recordings_listbox = tk.Listbox(self.main_frame, height=8)
        self.recordings_listbox.pack(padx=20, fill="x")

        # Load recordings from folder
        recordings = [f for f in os.listdir(
            RECORDINGS_FOLDER) if f.endswith(".json")]
        for rec in recordings:
            self.recordings_listbox.insert(tk.END, rec)

        select_btn = ttk.Button(
            self.main_frame, text="Select Recording File", command=self.select_playback_file)
        select_btn.pack(pady=5)

        # Repeat count and delay
        frm = ttk.Frame(self.main_frame)
        frm.pack(pady=10)

        ttk.Label(frm, text="Repeat Count:").grid(
            row=0, column=0, padx=5, sticky="e")
        ttk.Entry(frm, textvariable=self.repeat_count,
                  width=5).grid(row=0, column=1, padx=5)

        ttk.Label(frm, text="Delay Between Repeats (sec):").grid(
            row=1, column=0, padx=5, sticky="e")
        ttk.Entry(frm, textvariable=self.repeat_delay,
                  width=5).grid(row=1, column=1, padx=5)

        play_btn = ttk.Button(
            self.main_frame, text="Play Recording", command=self.play_selected_recording)
        play_btn.pack(pady=10)

        self.play_log = tk.Text(self.main_frame, height=8, state="disabled")
        self.play_log.pack(padx=10, pady=5, fill="x")

    def select_playback_file(self):
        file = filedialog.askopenfilename(initialdir=RECORDINGS_FOLDER,
                                          filetypes=[("JSON Files", "*.json")],
                                          title="Select Recording File")
        if file:
            # If file is outside recordings folder, add it to listbox (if not already)
            fname = os.path.basename(file)
            if fname not in self.recordings_listbox.get(0, tk.END):
                self.recordings_listbox.insert(tk.END, fname)
            idx = self.recordings_listbox.get(0, tk.END).index(fname)
            self.recordings_listbox.selection_clear(0, tk.END)
            self.recordings_listbox.selection_set(idx)
            self.filename = file
            self.log_play(f"Selected file: {fname}")

    def play_selected_recording(self):
        selection = self.recordings_listbox.curselection()
        if not selection:
            self.log_play("No recording selected!")
            messagebox.showwarning(
                "No selection", "Please select a recording from the list or choose a file.")
            return

        fname = self.recordings_listbox.get(selection[0])
        self.filename = os.path.join(RECORDINGS_FOLDER, fname)

        try:
            repeats = int(self.repeat_count.get())
            delay = float(self.repeat_delay.get())
        except Exception:
            messagebox.showerror(
                "Input error", "Repeat count must be integer and delay must be number.")
            return

        threading.Thread(target=self.playback, args=(repeats, delay)).start()

    def log_play(self, msg):
        self.play_log.config(state="normal")
        self.play_log.insert(tk.END, msg + "\n")
        self.play_log.see(tk.END)
        self.play_log.config(state="disabled")

    def playback(self, repeat_count, repeat_delay):
        self.log_play(f"Playback starting in 5 seconds...")
        time.sleep(5)

        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.log_play(f"Error loading recording: {e}")
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
            self.log_play(f"Playback iteration {i + 1} of {repeat_count}")
            last_time = 0
            for event in events:
                delay = event['time'] - last_time
                if delay > 0:
                    time.sleep(delay)
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
            if i < repeat_count - 1:
                self.log_play(
                    f"Waiting {repeat_delay} seconds before next repeat...")
                time.sleep(repeat_delay)

        self.log_play("Playback finished.")


if __name__ == "__main__":
    app = AutoStepApp()
    app.mainloop()
