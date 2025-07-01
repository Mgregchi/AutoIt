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


class AutoStepApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Step Recorder")
        self.geometry("520x420")
        self.resizable(True, True)
        self.minsize(400, 300)

        self.recording = False
        self.paused = False
        self.events = []
        self.start_time = None
        self.filename = None
        self.screen_width, self.screen_height = pyautogui.size()

        self.repeat_count = tk.IntVar(value=1)
        self.repeat_delay = tk.DoubleVar(value=1.0)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.create_menu()
        self.create_initial_screen()

        # Countdown cancel flag
        self.countdown_cancelled = False

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
            "About", "Auto Step Recorder\nCreated by Mgregchi\nhttps://github.com/Mgregchi/AutoStepRecorder\n\n2025 © Mgregchi\nLicensed under the MIT License")

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
        self.countdown_cancelled = False
        self.show_countdown(5, self.start_recording, cancelable=True)

    def show_countdown(self, seconds, callback, cancelable=False):
        self.clear_frame()
        self.countdown_label = ttk.Label(
            self.main_frame, text="", font=("Segoe UI", 48))
        self.countdown_label.pack(expand=True)

        if cancelable:
            cancel_btn = ttk.Button(
                self.main_frame, text="Cancel", command=self.cancel_countdown)
            cancel_btn.pack()

        self.countdown_cancelled = False

        def countdown(n):
            if self.countdown_cancelled:
                self.create_initial_screen()
                return
            if n > 0:
                self.countdown_label.config(text=str(n))
                self.after(1000, countdown, n-1)
            else:
                callback()

        countdown(seconds)

    def cancel_countdown(self):
        self.countdown_cancelled = True

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

        back_btn = ttk.Button(self.main_frame, text="Back",
                              command=self.back_to_main_from_recording)
        back_btn.pack(pady=5)

        self.log_text = tk.Text(self.main_frame, height=10, state="disabled")
        self.log_text.pack(padx=10, pady=10, fill="x")

        threading.Thread(target=self.record, daemon=True).start()

    def back_to_main_from_recording(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to cancel recording?"):
            self.recording = False
            self.create_initial_screen()

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

    def stop_recording(self):
        self.recording = False

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

        # Show toast message and go to playback screen
        self.toast("Recording completed!")
        self.playback_flow()
        # Select newly recorded file in playback list and enable play button
        newfile = os.path.basename(self.filename)
        self.select_recording_in_list(newfile)

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

    def toast(self, message, duration=2000):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.geometry("+{}+{}".format(self.winfo_rootx() +
                       150, self.winfo_rooty() + 150))
        ttk.Label(toast, text=message, relief="solid", padding=10).pack()
        toast.after(duration, toast.destroy)

    ################## PLAYBACK FLOW #################

    def playback_flow(self):
        self.clear_frame()

        # Back button at top left
        back_btn = ttk.Button(self.main_frame, text="Back",
                              command=self.create_initial_screen)
        back_btn.place(x=10, y=10)  # Position at top left

        ttk.Label(self.main_frame, text="Select a recording to play",
                  # Adjusted pady to account for back button
                  font=("Segoe UI", 14)).pack(pady=(40, 10))

        self.recordings_listbox = tk.Listbox(self.main_frame, height=8)
        self.recordings_listbox.pack(padx=20, pady=5, fill="x")
        self.recordings_listbox.bind(
            "<<ListboxSelect>>", self.recording_selected)

        recordings = [f for f in os.listdir(
            RECORDINGS_FOLDER) if f.endswith(".json")]
        for rec in recordings:
            self.recordings_listbox.insert(tk.END, rec)

        ttk.Button(self.main_frame, text="Or select manually",
                   command=self.select_playback_file).pack(pady=5)

        self.playback_controls_frame = ttk.Frame(self.main_frame)
        self.playback_controls_frame.pack(pady=10, fill="x")

        ttk.Label(self.playback_controls_frame, text="Repeat Count:").grid(
            row=0, column=0, padx=5, sticky="e")
        self.repeat_entry = ttk.Entry(
            self.playback_controls_frame, textvariable=self.repeat_count, width=5)
        self.repeat_entry.grid(row=0, column=1, padx=5)

        ttk.Label(self.playback_controls_frame, text="Delay Between Repeats (sec):").grid(
            row=1, column=0, padx=5, sticky="e")
        self.delay_entry = ttk.Entry(
            self.playback_controls_frame, textvariable=self.repeat_delay, width=5)
        self.delay_entry.grid(row=1, column=1, padx=5)

        self.play_btn = ttk.Button(
            self.main_frame, text="Play Recording", command=self.play_selected_recording)
        self.play_btn.pack(pady=10)
        self.play_btn['state'] = 'disabled'

        self.play_log = tk.Text(self.main_frame, height=8, state="disabled")
        self.play_log.pack(padx=10, pady=10, fill="both", expand=True)

        self.selected_playback_file = None

    def select_recording_in_list(self, filename):
        self.recordings_listbox.selection_clear(0, tk.END)
        list_items = self.recordings_listbox.get(0, tk.END)
        if filename in list_items:
            idx = list_items.index(filename)
            self.recordings_listbox.selection_set(idx)
            self.recordings_listbox.activate(idx)
        else:
            self.recordings_listbox.insert(tk.END, filename)
            self.recordings_listbox.selection_set(tk.END)
        self.selected_playback_file = os.path.join(RECORDINGS_FOLDER, filename)
        self.play_btn['state'] = 'normal'
        self.log_play(f"Selected file: {filename}")  # Log to confirm selection

    def select_playback_file(self):
        f = filedialog.askopenfilename(title="Select Recording File",
                                       filetypes=[("JSON Files", "*.json")],
                                       initialdir=RECORDINGS_FOLDER)
        if f:
            basename = os.path.basename(f)
            self.select_recording_in_list(basename)
            # Log to confirm manual selection
            self.log_play(f"Manually selected file: {basename}")

    def recording_selected(self, event=None):
        selection = self.recordings_listbox.curselection()
        if not selection:
            self.play_btn['state'] = 'disabled'
            return
        idx = selection[0]
        filename = self.recordings_listbox.get(idx)
        self.selected_playback_file = os.path.join(RECORDINGS_FOLDER, filename)
        self.play_btn['state'] = 'normal'

    def play_selected_recording(self):
        if not self.selected_playback_file:
            messagebox.showwarning(
                "No Selection", "Please select a recording first.")
            return

        try:
            repeat_count = max(1, int(self.repeat_count.get()))
        except Exception:
            messagebox.showerror(
                "Error", "Repeat Count must be a positive integer.")
            return
        try:
            repeat_delay = max(0, float(self.repeat_delay.get()))
        except Exception:
            messagebox.showerror(
                "Error", "Delay Between Repeats must be a number >= 0.")
            return

        self.countdown_cancelled = False
        self.show_countdown(5, lambda: self.playback_start(
            repeat_count, repeat_delay), cancelable=True)

    def playback_start(self, repeat_count, repeat_delay):
        self.play_log.config(state="normal")
        self.play_log.delete("1.0", tk.END)
        self.play_log.config(state="disabled")

        threading.Thread(target=self.playback, args=(
            repeat_count, repeat_delay), daemon=True).start()

    def log_play(self, msg):
        self.play_log.config(state="normal")
        self.play_log.insert(tk.END, msg + "\n")
        self.play_log.see(tk.END)
        self.play_log.config(state="disabled")

    def playback(self, repeat_count, repeat_delay):
        try:
            with open(self.selected_playback_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.log_play(f"Error loading recording: {e}")
            return

        rec_screen_w = data.get('screen_width', 1280)
        rec_screen_h = data.get('screen_height', 720)
        events = data.get('events', [])

        curr_w, curr_h = pyautogui.size()

        self.log_play(
            f"Playing '{os.path.basename(self.selected_playback_file)}' {repeat_count} times...")

        for i in range(repeat_count):
            if self.countdown_cancelled:
                self.log_play("Playback cancelled.")
                return

            last_time = 0
            for event in events:
                delay_time = event['time'] - last_time
                time.sleep(delay_time)
                last_time = event['time']

                etype = event['type']
                if etype == 'mouse_move':
                    x = int(event['nx'] * curr_w)
                    y = int(event['ny'] * curr_h)
                    pyautogui.moveTo(x, y, duration=0)
                elif etype == 'mouse_click':
                    x = int(event['nx'] * curr_w)
                    y = int(event['ny'] * curr_h)
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
    try:
        # app.iconbitmap("icon.ico")
        app.mainloop()
    except KeyboardInterrupt as e:
        print("KeyboardInterrupt detected.")
    import sys
    sys.exit(0)  # Ensure clean exit on close
