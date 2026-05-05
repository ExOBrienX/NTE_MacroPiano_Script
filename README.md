# NTE Piano Macro - MIDI to Keyboard Converter

🎵 **Convert MIDI files to keyboard macros for the piano in "Never to Evernees" (NTE)**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🌟 Features

- ✅ **Full Polyphony**: Support for chords and simultaneous notes
- ✅ **Automatic Detection**: Key signature and octave ranges
- ✅ **Real-time Controls**: F5/F6/F7/F8 for speed and playback control
- ✅ **Multi-language Interface**: Spanish and English support
- ✅ **File Selector**: Easy MIDI file selection via command line
- ✅ **Smart Chord Handling**: Groups notes by modifiers (Ctrl/Shift) for accurate playback

## 🎼 Note Mapping

| MIDI Note | Note | Key | Modifier | Description |
|-----------|------|-----|----------|-------------|
| 0 | C (Do) | A/S/Q | None | Natural note |
| 2 | D (Re) | S/W | None | Natural note |
| 3 | Eb (Mib) | D/E | Ctrl | Flat |
| 4 | E (Mi) | D/E | None | Natural note |
| 5 | F (Fa) | F/R | None | Natural note |
| 6 | F# (Fa#) | F/R | Shift | Sharp |
| 7 | G (Sol) | G/T | None | Natural note |
| 8 | G# (Sol#) | G/T | Shift | Sharp |
| 9 | A (La) | H/Y | None | Natural note |
| 10 | Bb (Sib) | J/U | Ctrl | Flat |
| 11 | B (Si) | J/U | None | Natural note |

## 🚀 Installation

### Requirements
- Python 3.7 or higher
- Windows 10/11 (for keyboard input simulation)

### Install Dependencies
```bash
pip install mido pynput pydirectinput
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### Verify Installation
```bash
python -c "import mido, pydirectinput, pynput; print('✅ All dependencies installed')"
```

## 🎮 Usage

### Basic Usage
```bash
python NTEscript.py
```

The script will:
1. Ask you to select your language (Spanish/English)
2. Show available MIDI files in the current directory
3. Let you select a file to play
4. Start playback with a 5-second countdown

### Controls
- **F5**: Normal speed (1x)
- **F6**: Slow speed (0.4x) - debug mode
- **F7**: Pause / Resume
- **F8**: Stop playback

### File Requirements
- Place your `.mid` files in the same directory as the script
- The script automatically detects key signatures and adjusts octaves
- Supports complex MIDI files with multiple tracks

## 📁 Project Structure

```
NTE Piano Macro/
├── NTEscript.py          # Main script with GUI
├── requirements.txt      # Python dependencies
├── README.md            # This file (English)
├── Orange.mid           # Example MIDI file
└── LICENSE              # MIT License
```

## 🔧 Troubleshooting

### Common Issues

**"No .mid files found"**
- Place MIDI files in the same directory as the script
- Ensure files have `.mid` extension

**"Import errors"**
```bash
pip install --upgrade mido pynput pydirectinput
```

**"Keys not working in game"**
- Make sure you're focused on the game window
- Some games have anti-macro protection
- Try running as administrator

**"Notes sound wrong"**
- The script automatically detects key signatures
- Check the transposition output in the console
- Complex MIDI files might need manual adjustment

### Debug Mode
Use F6 to switch to slow mode (0.4x speed) to see individual note presses.

## 🌐 Multi-language Support

The script supports both Spanish and English:
- Interface prompts
- Status messages
- Error messages
- Control instructions

Language is selected at startup.

## 📊 Technical Details

- **Input Method**: pydirectinput for reliable keyboard simulation
- **Polyphony**: Groups notes by modifier to prevent conflicts
- **Timing**: Smart sleep with speed control
- **Key Detection**: Krumhansl-Schmuckler algorithm for key finding
- **Octave Mapping**: Automatic octave range detection and adjustment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

- Use at your own risk
- Some games may detect automated input as cheating
- Test in single-player or with permission
- The author is not responsible for any consequences

## 🙏 Acknowledgments

- Built with [mido](https://mido.readthedocs.io/) for MIDI processing
- Uses [pynput](https://pynput.readthedocs.io/) for keyboard listening
- [pydirectinput](https://github.com/learncodebygaming/pydirectinput) for input simulation

---

**Enjoy playing your favorite songs in NTE! 🎹**