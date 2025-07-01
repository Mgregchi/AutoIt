# AutoIt – Auto Step Recorder

AutoIt is a cross-platform Python tool for recording and replaying mouse and keyboard actions. It features both a graphical user interface (GUI) and a command-line interface (CLI), making it easy to automate repetitive tasks or create reproducible demos.

## Features

- **Record** mouse and keyboard actions with precise timing.
- **Replay** recorded actions as many times as needed.
- **GUI**: User-friendly interface for recording and playback.
- **CLI**: Scriptable interface for advanced users.
- **Playback options**: Set repeat count and delay between repeats.
- **Cross-platform**: Works on Windows, macOS, and Linux (where dependencies are supported).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mgregchi/AutoIt.git
   cd AutoIt
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. *(Optional)* **Build a standalone executable** (requires PyInstaller):
   ```bash
   bash build.sh
   ```
   The executable will be created in the `dist/` directory.

## Usage

### Graphical User Interface (GUI)

Run the main GUI application:
```bash
python gui/app.py
```

- Click **Start Recording** to begin capturing actions.
- Use **F9** to pause/resume, **Esc** to stop recording.
- Click **Play Recording** to replay a saved session.
- Set repeat count and delay as needed.

### Command-Line Interface (CLI)

Run the CLI tool:
```bash
python cli/main.py
```

You will be prompted to:
- Record a new session (option 1)
- Play an existing session (option 2)

**Shortcuts during recording:**
- `F9`: Pause/Resume recording
- `Esc`: Stop recording

**Playback options:**
- Choose how many times to repeat and the delay between repeats.

### Recordings

- All recordings are saved as `.json` files in the `recordings/` directory.
- You can select and manage recordings from both the GUI and CLI.

## Dependencies

- MouseInfo
- PyAutoGUI
- PyGetWindow
- PyMsgBox
- pynput
- pyperclip
- PyRect
- PyScreeze
- pytweening
- six

(See `requirements.txt` for exact versions.)

## License

MIT License © 2025 C. Michael. A

## Credits

Created by Mgregchi  
[GitHub: Mgregchi](https://github.com/Mgregchi/AutoIt)