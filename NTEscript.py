#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NTE Piano Macro - MIDI to Keyboard Converter
===========================================

Converts MIDI files to keyboard macros for the piano in "Neverness to Everness" (NTE).

Features:
- Full polyphony support with chords
- Automatic key and octave detection
- Real-time controls (F5/F6/F7/F8)
- Multi-language interface (Spanish/English)
- File selector interface

Requirements:
    pip install mido pynput pydirectinput

Usage:
    python NTEscript.py
"""

import sys
import time
import threading
import mido
import pydirectinput
import os
from pynput import keyboard as kb
from pynput.keyboard import Key
from collections import defaultdict

# ─────────────────────────────────────────────
# LANGUAGE SYSTEM
# ─────────────────────────────────────────────

LANGUAGES = {
    'es': {
        'title': '🎵 NTE Piano Macro - Conversor MIDI a Teclado',
        'select_lang': 'Selecciona tu idioma / Select your language:',
        'lang_es': '1. Español',
        'lang_en': '2. Inglés',
        'invalid_lang': 'Opción inválida. Intenta de nuevo.',
        'select_file': 'Selecciona un archivo MIDI:',
        'no_files': 'No se encontraron archivos .mid en el directorio actual.',
        'file_option': '{}. {}',
        'enter_number': 'Ingresa el número del archivo (1-{}): ',
        'invalid_file': 'Número inválido. Intenta de nuevo.',
        'loading': 'Cargando: {}',
        'duration': 'Duración: {} segundos',
        'tracks': 'Tracks: {}',
        'analyzing_key': 'Analizando tonalidad...',
        'detected_key': 'Tonalidad detectada: {} {}',
        'transposition': 'Transposición: {} semitonos',
        'detecting_octaves': 'Detectando rangos de octava...',
        'midi_range': 'Rango MIDI del archivo: {}-{}',
        'octave_grave': 'Octava Grave → notas {}-{}',
        'octave_medio': 'Octava Medio → notas {}-{}',
        'octave_agudo': 'Octava Agudo → notas {}-{}',
        'out_of_range': 'Notas fuera de rango (ajustadas): {}',
        'controls_title': '─' * 50,
        'controls_f5': 'F5 = Velocidad normal (1x)',
        'controls_f6': 'F6 = Velocidad lenta (0.4x) — debug',
        'controls_f7': 'F7 = Pausar / Reanudar',
        'controls_f8': 'F8 = Detener',
        'get_ready': 'Ponte frente al piano en el juego.',
        'starting_in': 'Empezando en {}...',
        'playing': '▶ Reproduciendo... (F6 para ir lento, F5 para volver a normal)',
        'stopped': '[F8] Deteniendo...',
        'resumed': '[F7] ▶ Reanudando...',
        'paused': '[F7] ⏸ Pausado... (F7 reanudar, F8 detener)',
        'normal_speed': '[F5] Velocidad: NORMAL (1x)',
        'slow_speed': '[F6] Velocidad: LENTA (0.4x) — modo debug',
        'note_play': '▶ [{:<5}] {:<3} → [{}] {}',
        'finished': '✓ Canción terminada. Total notas tocadas: {}',
        'all_released': '[OK] Todas las teclas liberadas.',
        'error_load': 'Error al cargar el MIDI: {}',
        'error_release': '[ERROR release] {}',
        'interrupted': 'Interrumpido.',
        'usage': 'Uso: python NTEscript.py',
        'example': 'Ejemplo: Ejecuta el script y selecciona un archivo MIDI',
    },
    'en': {
        'title': '🎵 NTE Piano Macro - MIDI to Keyboard Converter',
        'select_lang': 'Select your language / Selecciona tu idioma:',
        'lang_es': '1. Spanish',
        'lang_en': '2. English',
        'invalid_lang': 'Invalid option. Try again.',
        'select_file': 'Select a MIDI file:',
        'no_files': 'No .mid files found in current directory.',
        'file_option': '{}. {}',
        'enter_number': 'Enter file number (1-{}): ',
        'invalid_file': 'Invalid number. Try again.',
        'loading': 'Loading: {}',
        'duration': 'Duration: {} seconds',
        'tracks': 'Tracks: {}',
        'analyzing_key': 'Analyzing key...',
        'detected_key': 'Detected key: {} {}',
        'transposition': 'Transposition: {} semitones',
        'detecting_octaves': 'Detecting octave ranges...',
        'midi_range': 'MIDI file range: {}-{}',
        'octave_grave': 'Grave octave → notes {}-{}',
        'octave_medio': 'Medio octave → notes {}-{}',
        'octave_agudo': 'Agudo octave → notes {}-{}',
        'out_of_range': 'Notes out of range (adjusted): {}',
        'controls_title': '─' * 50,
        'controls_f5': 'F5 = Normal speed (1x)',
        'controls_f6': 'F6 = Slow speed (0.4x) — debug',
        'controls_f7': 'F7 = Pause / Resume',
        'controls_f8': 'F8 = Stop',
        'get_ready': 'Get ready at the piano in the game.',
        'starting_in': 'Starting in {}...',
        'playing': '▶ Playing... (F6 for slow, F5 for normal)',
        'stopped': '[F8] Stopping...',
        'resumed': '[F7] ▶ Resuming...',
        'paused': '[F7] ⏸ Paused... (F7 resume, F8 stop)',
        'normal_speed': '[F5] Speed: NORMAL (1x)',
        'slow_speed': '[F6] Speed: SLOW (0.4x) — debug mode',
        'note_play': '▶ [{:<5}] {:<3} → [{}] {}',
        'finished': '✓ Song finished. Total notes played: {}',
        'all_released': '[OK] All keys released.',
        'error_load': 'Error loading MIDI: {}',
        'error_release': '[ERROR release] {}',
        'interrupted': 'Interrupted.',
        'usage': 'Usage: python NTEscript.py',
        'example': 'Example: Run the script and select a MIDI file',
    }
}

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

COUNTDOWN_SECONDS  = 5
MODIFIER_LEAD_MS   = 8    # Ms antes de presionar la tecla tras el modificador
GROUP_GAP_MS       = 3    # Ms entre grupos de modificador dentro de un acorde

pydirectinput.PAUSE = 0.0

speed_lock    = threading.Lock()
current_speed = 1.1

# ─────────────────────────────────────────────
# LANGUAGE SELECTION AND FILE SELECTOR
# ─────────────────────────────────────────────

def select_language():
    """Select language at startup."""
    print("🎵 NTE Piano Macro")
    print("=" * 40)
    print("Select your language / Selecciona tu idioma:")
    print("1. Spanish")
    print("2. English")

    while True:
        try:
            choice = input("Choose / Elige (1-2): ").strip()
            if choice == '1':
                return 'es'
            elif choice == '2':
                return 'en'
            else:
                print("Invalid option. Try again. / Opción inválida. Intenta de nuevo.")
        except KeyboardInterrupt:
            print("\nExiting... / Saliendo...")
            sys.exit(0)

def select_midi_file(lang):
    """Show a nice file selector for MIDI files."""
    texts = LANGUAGES[lang]

    print(f"\n{texts['title']}")
    print("=" * 60)

    # Find all .mid files in current directory
    midi_files = [f for f in os.listdir('.') if f.lower().endswith('.mid')]

    if not midi_files:
        print(texts['no_files'])
        print("Place some .mid files in the current directory and try again.")
        sys.exit(1)

    print(texts['select_file'])
    print("-" * 40)

    for i, filename in enumerate(midi_files, 1):
        print(texts['file_option'].format(i, filename))

    print("-" * 40)

    while True:
        try:
            choice = input(texts['enter_number'].format(len(midi_files))).strip()
            num = int(choice)
            if 1 <= num <= len(midi_files):
                return midi_files[num - 1]
            else:
                print(texts['invalid_file'])
        except ValueError:
            print(texts['invalid_file'])
        except KeyboardInterrupt:
            print("\nExiting... / Saliendo...")
            sys.exit(0)

# ─────────────────────────────────────────────
# MAPEO DEL JUEGO
# ─────────────────────────────────────────────

NOTE_MAP = {
    0:  ('c', None),
    1:  ('c', 'shift'),
    2:  ('d', None),
    3:  ('e', 'ctrl'),
    4:  ('e', None),
    5:  ('f', None),
    6:  ('f', 'shift'),
    7:  ('g', None),
    8:  ('g', 'shift'),
    9:  ('a', None),
    10: ('b', 'ctrl'),
    11: ('b', None),
}

OCTAVE_KEYS = {
    'grave': {'c': 'z', 'd': 'x', 'e': 'c', 'f': 'v', 'g': 'b', 'a': 'n', 'b': 'm'},
    'medio': {'c': 'a', 'd': 's', 'e': 'd', 'f': 'f', 'g': 'g', 'a': 'h', 'b': 'j'},
    'agudo': {'c': 'q', 'd': 'w', 'e': 'e', 'f': 'r', 'g': 't', 'a': 'y', 'b': 'u'},
}

NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']

# Orden de prioridad de modificadores para acordes
MODIFIER_ORDER = [None, 'shift', 'ctrl']

# ─────────────────────────────────────────────
# ESTADO GLOBAL
# ─────────────────────────────────────────────

stop_flag   = threading.Event()
pause_flag  = threading.Event()

# midi_note → (game_key, modifier, octave_name, note_in_oct)
active_keys = {}

# ─────────────────────────────────────────────
# DETECCIÓN DE TONALIDAD
# ─────────────────────────────────────────────

MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

def detect_key(midi_file, lang):
    texts = LANGUAGES[lang]
    note_counts = [0] * 12
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                note_counts[msg.note % 12] += 1

    best_key, best_score, best_mode = 0, -999, 'major'
    for key in range(12):
        score_major = sum(note_counts[(key + i) % 12] * MAJOR_PROFILE[i] for i in range(12))
        score_minor = sum(note_counts[(key + i) % 12] * MINOR_PROFILE[i] for i in range(12))
        if score_major > best_score:
            best_score, best_key, best_mode = score_major, key, 'major'
        if score_minor > best_score:
            best_score, best_key, best_mode = score_minor, key, 'minor'

    print(f"  {texts['detected_key'].format(NOTE_NAMES[best_key % 12], best_mode)}")
    semitones = -best_key
    if best_mode == 'minor':
        semitones += 3
    return semitones

# ─────────────────────────────────────────────
# DETECCIÓN DE OCTAVAS
# ─────────────────────────────────────────────

def detect_octave_ranges(midi_file, transpose, lang):
    texts = LANGUAGES[lang]
    notes = []
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append(msg.note + transpose)

    if not notes:
        return {'grave': (48, 59), 'medio': (60, 71), 'agudo': (72, 83)}

    min_note, max_note = min(notes), max(notes)
    best_base, best_out = 48, 9999

    for base in range(max(0, min_note - 24), min(116, max_note + 1)):
        out = sum(1 for n in notes if n < base or n > base + 35)
        if out < best_out:
            best_out, best_base = out, base

    ranges = {
        'grave': (best_base,      best_base + 11),
        'medio': (best_base + 12, best_base + 23),
        'agudo': (best_base + 24, best_base + 35),
    }

    print(f"  {texts['midi_range'].format(min_note, max_note)}")
    print(f"  {texts['octave_grave'].format(ranges['grave'][0], ranges['grave'][1])}")
    print(f"  {texts['octave_medio'].format(ranges['medio'][0], ranges['medio'][1])}")
    print(f"  {texts['octave_agudo'].format(ranges['agudo'][0], ranges['agudo'][1])}")
    print(f"  {texts['out_of_range'].format(best_out)}")
    return ranges

# ─────────────────────────────────────────────
# CONVERSIÓN NOTA → TECLA
# ─────────────────────────────────────────────

def midi_note_to_key(midi_note, octave_ranges):
    grave_lo = octave_ranges['grave'][0]
    agudo_hi = octave_ranges['agudo'][1]

    while midi_note < grave_lo:
        midi_note += 12
    while midi_note > agudo_hi:
        midi_note -= 12

    octave_name = 'medio'
    for name, (lo, hi) in octave_ranges.items():
        if lo <= midi_note <= hi:
            octave_name = name
            break

    note_in_oct         = midi_note % 12
    base_note, modifier = NOTE_MAP[note_in_oct]
    game_key            = OCTAVE_KEYS[octave_name][base_note]

    return game_key, modifier, octave_name, note_in_oct

# ─────────────────────────────────────────────
# TOQUE DE ACORDE CON GRUPOS POR MODIFICADOR
# ─────────────────────────────────────────────

def play_chord(notes_dict, lang):
    """
    notes_dict: { midi_note: (game_key, modifier, octave_name, note_in_oct) }
    """
    texts = LANGUAGES[lang]
    if not notes_dict:
        return

    # Agrupar por modificador
    groups = defaultdict(list)
    for midi_note, (game_key, modifier, octave_name, note_in_oct) in notes_dict.items():
        groups[modifier].append((midi_note, game_key, octave_name, note_in_oct))

    # Tocar grupo por grupo en orden: None → shift → ctrl
    for mod in MODIFIER_ORDER:
        if mod not in groups:
            continue

        note_list = groups[mod]

        # Log
        for midi_note, game_key, octave_name, note_in_oct in note_list:
            mod_str = f"+{mod.upper()}" if mod else ""
            print(texts['note_play'].format(octave_name.upper(), NOTE_NAMES[note_in_oct], game_key.upper(), mod_str))

        # Presionar modificador del grupo
        if mod == 'shift':
            pydirectinput.keyDown('shift')
            time.sleep(MODIFIER_LEAD_MS / 1000)
        elif mod == 'ctrl':
            pydirectinput.keyDown('ctrl')
            time.sleep(MODIFIER_LEAD_MS / 1000)

        # Presionar todas las teclas del grupo
        for midi_note, game_key, octave_name, note_in_oct in note_list:
            pydirectinput.keyDown(game_key)
            active_keys[midi_note] = (game_key, mod, octave_name, note_in_oct)

        # Soltar modificador del grupo
        if mod == 'shift':
            pydirectinput.keyUp('shift')
        elif mod == 'ctrl':
            pydirectinput.keyUp('ctrl')

        # Gap entre grupos
        if GROUP_GAP_MS > 0:
            time.sleep(GROUP_GAP_MS / 1000)

def release_chord_note(midi_note, lang):
    """Suelta una nota individual del acorde."""
    texts = LANGUAGES[lang]
    if midi_note not in active_keys:
        return
    game_key, modifier, _, _ = active_keys.pop(midi_note)
    try:
        pydirectinput.keyUp(game_key)
    except Exception as e:
        print(texts['error_release'].format(e))

def release_all(lang):
    texts = LANGUAGES[lang]
    for midi_note, (game_key, modifier, _, _) in list(active_keys.items()):
        try:
            pydirectinput.keyUp(game_key)
        except:
            pass
    active_keys.clear()
    try:
        pydirectinput.keyUp('ctrl')
        pydirectinput.keyUp('shift')
    except:
        pass
    print(f"  {texts['all_released']}")

# ─────────────────────────────────────────────
# SLEEP CON CONTROL DE VELOCIDAD
# ─────────────────────────────────────────────

def smart_sleep(seconds):
    if seconds <= 0:
        return

    chunk   = 0.01
    elapsed = 0.0

    while elapsed < seconds:
        if stop_flag.is_set():
            return
        while pause_flag.is_set():
            if stop_flag.is_set():
                return
            time.sleep(0.05)
        with speed_lock:
            speed = current_speed
        time.sleep(chunk / speed)
        elapsed += chunk

# ─────────────────────────────────────────────
# LISTENER F5/F6/F7/F8
# ─────────────────────────────────────────────

def on_press(key, lang):
    texts = LANGUAGES[lang]
    global current_speed

    if key == Key.f8:
        print(f"\n{texts['stopped']}")
        stop_flag.set()
        release_all(lang)
        return False
    elif key == Key.f7:
        if pause_flag.is_set():
            pause_flag.clear()
            print(f"\n{texts['resumed']}")
        else:
            pause_flag.set()
            release_all(lang)
            print(f"\n{texts['paused']}")
    elif key == Key.f5:
        with speed_lock:
            current_speed = 1.0
        print(f"\n{texts['normal_speed']}")
    elif key == Key.f6:
        with speed_lock:
            current_speed = 0.4
        print(f"\n{texts['slow_speed']}")

def start_stop_listener(lang):
    with kb.Listener(on_press=lambda key: on_press(key, lang)) as listener:
        listener.join()

# ─────────────────────────────────────────────
# REPRODUCTOR PRINCIPAL
# ─────────────────────────────────────────────

def play_midi(midi_path, lang):
    texts = LANGUAGES[lang]
    print(f"\n{texts['loading'].format(midi_path)}")

    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        print(texts['error_load'].format(e))
        return

    duration_formatted = f"{mid.length:.1f}"
    print(f"  {texts['duration'].format(duration_formatted)}")
    print(f"  {texts['tracks'].format(len(mid.tracks))}")

    print(f"\n{texts['analyzing_key']}")
    transpose = detect_key(mid, lang)
    transpose_formatted = f"{transpose:+d}"
    print(f"  {texts['transposition'].format(transpose_formatted)}")

    print(f"\n{texts['detecting_octaves']}")
    octave_ranges = detect_octave_ranges(mid, transpose, lang)

    print(f"\n{texts['controls_title']}")
    print(f"  {texts['controls_f5']}")
    print(f"  {texts['controls_f6']}")
    print(f"  {texts['controls_f7']}")
    print(f"  {texts['controls_f8']}")
    print(f"{texts['controls_title']}")
    print(f"\n{texts['get_ready']}")

    for i in range(COUNTDOWN_SECONDS, 0, -1):
        if stop_flag.is_set():
            return
        print(f"  {texts['starting_in'].format(i)}")
        time.sleep(1)

    print(f"\n{texts['playing']}\n")

    note_count  = 0
    chord_batch = {}

    for msg in mid:
        if stop_flag.is_set():
            break

        # Si hay tiempo de espera, primero tocar el acorde acumulado
        if msg.time > 0 and chord_batch:
            play_chord(chord_batch, lang)
            note_count += len(chord_batch)
            chord_batch = {}

        # Esperar el tiempo del mensaje
        if msg.time > 0:
            smart_sleep(msg.time)

        if stop_flag.is_set():
            break

        while pause_flag.is_set():
            if stop_flag.is_set():
                break
            time.sleep(0.05)

        if msg.type == 'note_on' and msg.velocity > 0:
            raw_note = msg.note + transpose
            game_key, modifier, octave_name, note_in_oct = midi_note_to_key(raw_note, octave_ranges)
            chord_batch[msg.note] = (game_key, modifier, octave_name, note_in_oct)

        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if chord_batch:
                play_chord(chord_batch, lang)
                note_count += len(chord_batch)
                chord_batch = {}
            release_chord_note(msg.note, lang)

    # Tocar lo que quede al final
    if chord_batch:
        play_chord(chord_batch, lang)
        note_count += len(chord_batch)

    release_all(lang)
    print(f"\n{texts['finished'].format(note_count)}")

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    try:
        # Select language
        lang = select_language()

        # Select MIDI file
        midi_file = select_midi_file(lang)

        # Start the listener thread
        listener_thread = threading.Thread(target=start_stop_listener, args=(lang,), daemon=True)
        listener_thread.start()

        # Play the MIDI file
        play_midi(midi_file, lang)

    except KeyboardInterrupt:
        texts = LANGUAGES.get(lang, LANGUAGES['en'])
        print(f"\n{texts['interrupted']}")
        stop_flag.set()
        if 'lang' in locals():
            release_all(lang)