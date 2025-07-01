import pyautogui
import time
import json
import os
import tkinter as tk
from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Listener as KeyboardListener, Key

# Globals
events = []
recording = False
paused = False
start_time = None
screen_width, screen_height = 0, 0
recordings_folder = "recordings"

# Ensure recordings folder exists
os.makedirs(recordings_folder, exist_ok=True)


def get_screen_resolution_():
    root = tk.Tk()
    root.withdraw()
    return root.winfo_screenwidth(), root.winfo_screenheight()


def get_screen_resolution():
    return pyautogui.size()


def get_time():
    return time.time() - start_time


def on_click(x, y, button, pressed):
    global screen_width, screen_height
    if not recording or paused:
        return
    events.append({
        'type': 'mouse_click',
        'time': get_time(),
        'nx': x / screen_width,
        'ny': y / screen_height,
        'button': button.name,
        'pressed': pressed
    })


def on_move(x, y):
    global screen_width, screen_height
    if not recording or paused:
        return
    events.append({
        'type': 'mouse_move',
        'time': get_time(),
        'nx': x / screen_width,
        'ny': y / screen_height
    })


def on_press(key):
    global recording, paused
    if key == Key.esc:
        recording = False
        return False  # stop listener
    if key == Key.f9:
        paused = not paused
        print(f"{'⏸️ Paused' if paused else '▶️ Resumed'} recording.")
        return

    if not recording or paused:
        return

    try:
        k = key.char
    except AttributeError:
        k = str(key)
    events.append({
        'type': 'key_press',
        'time': get_time(),
        'key': k
    })


def on_release(key):
    if not recording or paused:
        return
    try:
        k = key.char
    except AttributeError:
        k = str(key)
    events.append({
        'type': 'key_release',
        'time': get_time(),
        'key': k
    })


def record():
    global recording, start_time, events, paused, screen_width, screen_height
    events = []
    paused = False
    recording = True

    print("🕐 You have 5 seconds to switch to the window you want to record...")
    time.sleep(5)

    screen_width, screen_height = get_screen_resolution()
    start_time = time.time()
    print("🎙️  Recording started. Press F9 to pause/resume, Esc to stop.")

    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
    keyboard_listener = keyboard.Listener(
        on_press=on_press, on_release=on_release)

    mouse_listener.start()
    keyboard_listener.start()
    keyboard_listener.join()  # Waits for ESC key to stop recording

    recording = False
    mouse_listener.stop()
    mouse_listener.join()

    filename = input("Enter filename to save (blank = auto): ").strip()
    if not filename:
        filename = "recording_" + time.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(recordings_folder, filename + ".json")

    meta = {
        'screen_width': screen_width,
        'screen_height': screen_height,
        'events': events
    }

    with open(filepath, 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"\n✅ Saved recording to: {filepath}")


def list_recordings():
    files = [f for f in os.listdir(recordings_folder) if f.endswith(".json")]
    if not files:
        print("⚠️ No recordings found.")
    else:
        print("📂 Available Recordings:")
        for i, f in enumerate(files):
            print(f"  {i+1}: {f}")
    return files


def load_recording():
    files = list_recordings()
    if not files:
        return None
    choice = input("Enter file number to play or blank to cancel: ").strip()
    if not choice.isdigit():
        return None
    index = int(choice) - 1
    if 0 <= index < len(files):
        filepath = os.path.join(recordings_folder, files[index])
        with open(filepath, 'r') as f:
            return json.load(f)
    else:
        print("❌ Invalid selection.")
        return None


def play(data):
    current_w, current_h = get_screen_resolution()
    recorded_w = data.get('screen_width')
    recorded_h = data.get('screen_height')
    events = data.get('events', [])

    if (recorded_w, recorded_h) != (current_w, current_h):
        print(f"⚠️ Resolution mismatch:")
        print(f"   Recorded: {recorded_w}x{recorded_h}")
        print(f"   Current : {current_w}x{current_h}")
        choice = input("Proceed anyway? (y/n): ").strip().lower()
        if choice != 'y':
            return

    repeat_count = input(
        "🔁 How many times to repeat playback? (default 1): ").strip()
    repeat_delay = input(
        "⏱️ Delay between repeats (seconds, default 1): ").strip()
    try:
        repeat_count = int(repeat_count) if repeat_count else 1
        repeat_delay = float(repeat_delay) if repeat_delay else 1.0
    except ValueError:
        print("❌ Invalid input. Using defaults.")
        repeat_count, repeat_delay = 1, 1.0

    print("🕐 Prepare... Playback starts in 5 seconds.")
    time.sleep(5)

    mouse_ctrl = MouseController()
    keyboard_ctrl = KeyboardController()

    for cycle in range(repeat_count):
        print(f"▶️ Playing iteration {cycle+1} of {repeat_count}")
        last_time = 0
        for event in events:
            delay = event['time'] - last_time
            if delay > 0:
                time.sleep(delay)
            last_time = event['time']

            if event['type'] == 'mouse_move':
                nx = event.get('nx')
                ny = event.get('ny')
                if nx is not None and ny is not None:
                    x = int(nx * current_w)
                    y = int(ny * current_h)
                    mouse_ctrl.position = (x, y)

            elif event['type'] == 'mouse_click':
                nx = event.get('nx')
                ny = event.get('ny')
                if nx is not None and ny is not None:
                    x = int(nx * current_w)
                    y = int(ny * current_h)
                    mouse_ctrl.position = (x, y)
                btn = Button.left if event['button'] == 'left' else Button.right
                if event['pressed']:
                    mouse_ctrl.press(btn)
                else:
                    mouse_ctrl.release(btn)

            elif event['type'] == 'key_press':
                try:
                    keyboard_ctrl.press(event['key'])
                except Exception:
                    pass

            elif event['type'] == 'key_release':
                try:
                    keyboard_ctrl.release(event['key'])
                except Exception:
                    pass

        if cycle < repeat_count - 1:
            print(f"⏳ Waiting {repeat_delay} seconds before next loop...")
            time.sleep(repeat_delay)

    print("✅ Playback complete.")


if __name__ == "__main__":
    print("== Auto Step Recorder ==")
    print("1 - Record a new session")
    print("2 - Play an existing session")

    choice = input("Enter choice (1/2): ").strip()
    if choice == "1":
        record()
    elif choice == "2":
        data = load_recording()
        if data:
            play(data)
        else:
            print("❌ No recording selected.")
    else:
        print("Invalid option.")


# 🧪 To Test
# Run the script: python auto_step.py

# Choose option 1 to record.

# Wait 5s, then record mouse/keyboard actions.

# Press F9 to pause/resume, Esc to finish.

# Choose option 2 to play a saved recording.

# Enter repeat count and delay if desired.
