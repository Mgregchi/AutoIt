import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import json
import os
import pyautogui
from pynput import keyboard, mouse

RECORDINGS_FOLDER = "recordings"
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)


class AutoStepGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Step Recorder")
        self.geometry("400x350")
        self.resizable(False, False)

        # Variables
        self.filename = None
        self.recording = False
        self.paused = False
        self.events = []
        self.start_time = None
        self.screen_width, self.screen_height = pyautogui.size()

        # UI Setup
        self.create_widgets()

    def create_widgets(self):
        # Buttons
        self.btn_record = tk.Button(
            self, text="Start Recording", command=self.start_recording)
        self.btn_record.pack(pady=10)

        self.btn_play = tk.Button(
            self, text="Play Recording", command=self.start_playback)
        self.btn_play.pack(pady=10)

        self.btn_select = tk.Button(
            self, text="Select Recording File", command=self.select_file)
        self.btn_select.pack(pady=10)

        # Repeat count
        tk.Label(self, text="Repeat Count:").pack()
        self.repeat_var = tk.StringVar(value="1")
        self.repeat_entry = tk.Entry(
            self, textvariable=self.repeat_var, width=5)
        self.repeat_entry.pack()

        # Delay between repeats
        tk.Label(self, text="Delay Between Repeats (sec):").pack()
        self.delay_var = tk.StringVar(value="1")
        self.delay_entry = tk.Entry(self, textvariable=self.delay_var, width=5)
        self.delay_entry.pack()

        # Log text area
        self.log_text = tk.Text(self, height=10, width=45, state="disabled")
        self.log_text.pack(pady=10)

        # Info label
        self.info_label = tk.Label(
            self, text="F9: Pause/Resume recording | Esc: Stop recording")
        self.info_label.pack(pady=5)

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def select_file(self):
        filetypes = [("JSON Files", "*.json")]
        f = filedialog.askopenfilename(
            initialdir=RECORDINGS_FOLDER, filetypes=filetypes)
        if f:
            self.filename = f
            self.log(f"Selected file: {os.path.basename(f)}")

    def start_recording(self):
        if self.recording:
            self.log("Already recording!")
            return
        self.recording = True
        self.paused = False
        self.events = []
        self.filename = None
        self.log("🕐 Switching window - Recording starts in 5 seconds...")
        threading.Thread(target=self.record).start()

    def record(self):
        self.screen_width, self.screen_height = pyautogui.size()
        time.sleep(5)
        self.start_time = time.time()
        self.log("🎙️ Recording started. Press F9 to pause/resume, Esc to stop.")

        def on_press(key):
            if not self.recording or self.paused:
                return
            if key == keyboard.Key.esc:
                self.recording = False
                return False
            if key == keyboard.Key.f9:
                self.paused = not self.paused
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
        # Ask for filename if none selected
        if not self.filename:
            ts = time.strftime("%Y%m%d_%H%M%S")
            self.filename = os.path.join(
                RECORDINGS_FOLDER, f"recording_{ts}.json")
        meta = {
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'events': self.events
        }
        with open(self.filename, 'w') as f:
            json.dump(meta, f, indent=2)
        self.log(f"Saved recording to: {os.path.basename(self.filename)}")

    def elapsed_time(self):
        return time.time() - self.start_time

    def start_playback(self):
        if self.recording:
            self.log("Cannot play while recording!")
            return

        if not self.filename:
            self.log("No recording file selected!")
            messagebox.showwarning(
                "No file", "Please select a recording file first.")
            return

        self.log("🕐 Playback starts in 5 seconds...")
        threading.Thread(target=self.playback).start()

    def playback(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.log(f"Error loading file: {e}")
            return

        current_w, current_h = pyautogui.size()
        recorded_w = data.get('screen_width')
        recorded_h = data.get('screen_height')
        events = data.get('events', [])

        if (recorded_w, recorded_h) != (current_w, current_h):
            self.log(
                f"⚠️ Resolution mismatch: Recorded {recorded_w}x{recorded_h}, Current {current_w}x{current_h}")
            res = messagebox.askyesno(
                "Resolution Mismatch", "Screen resolution differs from recording. Continue playback?")
            if not res:
                self.log("Playback cancelled by user.")
                return

        try:
            repeat_count = int(self.repeat_var.get())
        except ValueError:
            repeat_count = 1
        try:
            repeat_delay = float(self.delay_var.get())
        except ValueError:
            repeat_delay = 1.0

        time.sleep(5)
        self.log(f"Starting playback x{repeat_count}")

        for i in range(repeat_count):
            self.log(f"Playback iteration {i + 1}/{repeat_count}")
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
                    button = 'left' if 'left' in event['button'] else 'right'
                    if event['pressed']:
                        pyautogui.mouseDown(button=button)
                    else:
                        pyautogui.mouseUp(button=button)
                elif etype == 'key_press':
                    key = event['key']
                    try:
                        if len(key) == 1:
                            pyautogui.keyDown(key)
                        else:
                            pyautogui.keyDown(key.replace('Key.', '').lower())
                    except:
                        pass
                elif etype == 'key_release':
                    key = event['key']
                    try:
                        if len(key) == 1:
                            pyautogui.keyUp(key)
                        else:
                            pyautogui.keyUp(key.replace('Key.', '').lower())
                    except:
                        pass

            if i < repeat_count - 1:
                self.log(
                    f"Waiting {repeat_delay} seconds before next iteration...")
                time.sleep(repeat_delay)

        self.log("✅ Playback finished.")


if __name__ == "__main__":
    app = AutoStepGUI()
    app.mainloop()
