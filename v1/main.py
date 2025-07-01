import time
import json
import os
from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Listener as KeyboardListener, Key

# Globals
events = []
recording = False
start_time = None
recordings_folder = "recordings"

# Ensure the recordings folder exists
os.makedirs(recordings_folder, exist_ok=True)


def get_time():
    return time.time() - start_time


def on_click(x, y, button, pressed):
    if not recording:
        return
    events.append({
        'type': 'mouse_click',
        'time': get_time(),
        'x': x,
        'y': y,
        'button': button.name,
        'pressed': pressed
    })


def on_move(x, y):
    if not recording:
        return
    events.append({
        'type': 'mouse_move',
        'time': get_time(),
        'x': x,
        'y': y
    })


def on_press(key):
    global recording
    if key == Key.esc:
        # Stop recording
        recording = False
        return False
    if not recording:
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


def record():
    global recording, start_time, events
    events = []
    recording = True
    start_time = time.time()
    print("Recording... Press ESC to stop.")

    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
    keyboard_listener = keyboard.Listener(on_press=on_press)

    mouse_listener.start()
    keyboard_listener.start()

    # Wait for keyboard to finish (ESC)
    keyboard_listener.join()
    recording = False

    # Stop mouse listener as well
    mouse_listener.stop()
    mouse_listener.join()

    # Ask for filename
    filename = input(
        "Enter filename to save (without extension, leave blank for auto): ").strip()
    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}"

    filepath = os.path.join(recordings_folder, filename + ".json")

    with open(filepath, 'w') as f:
        json.dump(events, f, indent=2)

    print(f"\n✅ Recording saved as: {filepath}")


def list_recordings():
    files = [f for f in os.listdir(recordings_folder) if f.endswith(".json")]
    if not files:
        print("No recordings found.")
    else:
        print("Available recordings:")
        for i, f in enumerate(files):
            print(f"{i+1}: {f}")
    return files


def load_recording():
    files = list_recordings()
    if not files:
        return None
    choice = input(
        "Enter file number to load or press Enter to cancel: ").strip()
    if not choice.isdigit():
        return None
    index = int(choice) - 1
    if 0 <= index < len(files):
        filepath = os.path.join(recordings_folder, files[index])
        with open(filepath, 'r') as f:
            return json.load(f)
    else:
        print("Invalid choice.")
        return None


def play(events):
    print("Playing back...")
    mouse_ctrl = MouseController()
    keyboard_ctrl = KeyboardController()

    last_time = 0
    for event in events:
        delay = event['time'] - last_time
        time.sleep(delay)
        last_time = event['time']

        if event['type'] == 'mouse_move':
            mouse_ctrl.position = (event['x'], event['y'])

        elif event['type'] == 'mouse_click':
            mouse_ctrl.position = (event['x'], event['y'])
            btn = Button.left if event['button'] == 'left' else Button.right
            if event['pressed']:
                mouse_ctrl.press(btn)
            else:
                mouse_ctrl.release(btn)

        elif event['type'] == 'key_press':
            try:
                keyboard_ctrl.press(event['key'])
                keyboard_ctrl.release(event['key'])
            except:
                pass


if __name__ == "__main__":
    print("Choose mode:")
    print("1 - Record a new session")
    print("2 - Play an existing session")

    choice = input("Enter choice (1/2): ").strip()
    if choice == "1":
        record()
    elif choice == "2":
        loaded = load_recording()
        if loaded:
            play(loaded)
        else:
            print("No valid recording selected.")
    else:
        print("Invalid choice.")
