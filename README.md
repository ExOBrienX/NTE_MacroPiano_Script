# NTE Piano Macro

Plays MIDI files on the in-game pianos of **Neverness to Everness** (NTE) by turning each note into the keyboard input the game expects.

Pick a `.mid` file, sit at a piano in the game, and the script performs the song for you, chords included.

## Features

- **Full polyphony.** Chords and simultaneous notes are grouped by modifier key (Ctrl / Shift) so they are pressed together without conflicts.
- **Automatic key detection.** Finds the song's key with the Krumhansl-Schmuckler algorithm and transposes it to fit the game's keyboard.
- **Automatic octave range.** Shifts the song into the octaves the in-game piano can play.
- **Live controls.** Change speed, pause, resume or stop while the song is playing.
- **Spanish and English interface**, chosen at startup.

## Requirements

- Windows 10 or 11
- Python 3.7 or newer

## Quick start

On Windows, double-click `Start.bat`. It installs the dependencies and launches the script.

Or from a terminal:

```bash
pip install -r requirements.txt
```

```bash
python NTEscript.py
```

Then:

1. Choose your language.
2. Choose a MIDI file from the list. Any `.mid` file placed next to the script shows up; `Orange.mid` is included as an example.
3. Switch to the game and sit at a piano. Playback starts after a 5-second countdown.

## Controls

| Key | Action |
|---|---|
| F5 | Normal speed (1x) |
| F6 | Slow speed (0.4x), useful to check individual notes |
| F7 | Pause / resume |
| F8 | Stop |

## Note mapping

| Semitone | Note | Key | Modifier |
|---|---|---|---|
| 0 | C (Do) | A / S / Q | none |
| 2 | D (Re) | S / W | none |
| 3 | Eb (Mib) | D / E | Ctrl |
| 4 | E (Mi) | D / E | none |
| 5 | F (Fa) | F / R | none |
| 6 | F# (Fa#) | F / R | Shift |
| 7 | G (Sol) | G / T | none |
| 8 | G# (Sol#) | G / T | Shift |
| 9 | A (La) | H / Y | none |
| 10 | Bb (Sib) | J / U | Ctrl |
| 11 | B (Si) | J / U | none |

## How it works

1. The MIDI file is read with [mido](https://mido.readthedocs.io/) and its notes are collected across all tracks.
2. The key is estimated and the song is transposed and shifted to the playable octaves.
3. Notes that start together are grouped into chords, split by the modifier they need.
4. Key presses are sent with [pydirectinput](https://github.com/learncodebygaming/pydirectinput), which the game registers reliably, while [pynput](https://pynput.readthedocs.io/) listens for the control keys.

## Troubleshooting

**No `.mid` files found.** Put the MIDI files in the same folder as the script.

**Keys do nothing in the game.** Make sure the game window is focused. If it still fails, run the terminal as administrator.

**The song sounds wrong.** Check the transposition printed in the console. Very dense or unusual MIDI files may need to be simplified first.

## Disclaimer

This is a fan-made tool and is not affiliated with the game or its developers. It sends automated keyboard input, which a game's terms of service may not allow. Use it at your own risk.

## License

MIT. See [LICENSE](LICENSE).
