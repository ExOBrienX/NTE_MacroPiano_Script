#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NTE Piano Macro - v3c
====================
Convierte un archivo MIDI y simula las pulsaciones de teclado
para el piano del juego "Never to Evernees" (NTE).

Cambios v3c:
- Fix crítico de polifía: notas simultáneas con distintos
  modificadores ya no se pisan entre sí.
- Las notas de un acorde se agrupan por modificador y se tocan
  en secuencia ultra-rápida (10ms entre grupos).
- Orden: sin modificador → shift → ctrl

Controles:
    F5 = Velocidad normal (1x)
    F6 = Velocidad lenta  (0.4x) — debug
    F7 = Pausar / Reanudar
    F8 = Detener

Requisitos:
    python -m pip install mido pynput pydirectinput pyautogui

Uso:
    python nte_piano_v3c.py Orange.mid
    python nte_piano_v3c.py Numb.mid
"""

import sys
import time
import threading
import mido
import pydirectinput
from pynput import keyboard as kb
from pynput.keyboard import Key
from collections import defaultdict

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
# Las notas naturales van primero, luego shift, luego ctrl
MODIFIER_ORDER = [None, 'shift', 'ctrl']

# ─────────────────────────────────────────────
# ESTADO GLOBAL
# ─────────────────────────────────────────────

stop_flag   = threading.Event()
pause_flag  = threading.Event()

# midi_note → (game_key, modifier, octave_name, note_in_oct)
active_keys = {}

# Acorde pendiente: notas que llegaron al mismo tiempo
# key=midi_note, value=(game_key, modifier, octave, note_in_oct)
pending_chord = {}
chord_timer   = None
chord_lock    = threading.Lock()

CHORD_WINDOW_MS = 30  # ms para agrupar notas como acorde

# ─────────────────────────────────────────────
# DETECCIÓN DE TONALIDAD
# ─────────────────────────────────────────────

MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

def detect_key(midi_file):
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

    print(f"  Tonalidad detectada: {NOTE_NAMES[best_key % 12]} {best_mode}")
    semitones = -best_key
    if best_mode == 'minor':
        semitones += 3
    return semitones

# ─────────────────────────────────────────────
# DETECCIÓN DE OCTAVAS
# ─────────────────────────────────────────────

def detect_octave_ranges(midi_file, transpose):
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

    print(f"  Rango MIDI del archivo: {min_note} - {max_note}")
    print(f"  Octava Grave → notas {ranges['grave'][0]}-{ranges['grave'][1]}")
    print(f"  Octava Medio → notas {ranges['medio'][0]}-{ranges['medio'][1]}")
    print(f"  Octava Agudo → notas {ranges['agudo'][0]}-{ranges['agudo'][1]}")
    print(f"  Notas fuera de rango (ajustadas): {best_out}")
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
#
# En lugar de presionar todas las teclas a la vez
# (lo que causa conflictos de Ctrl/Shift),
# agrupamos las notas por modificador y las tocamos
# en secuencia ultra-rápida:
#   1. Notas sin modificador  → todas juntas
#   2. Notas con Shift        → Shift down, todas, Shift up
#   3. Notas con Ctrl         → Ctrl down, todas, Ctrl up
#
# 15ms entre grupos = imperceptible al oído
# ─────────────────────────────────────────────

def play_chord(notes_dict):
    """
    notes_dict: { midi_note: (game_key, modifier, octave_name, note_in_oct) }
    """
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
            print(f"  ▶ [{octave_name.upper():5}] {NOTE_NAMES[note_in_oct]:3} → [{game_key.upper()}] {mod_str}")

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

def release_chord_note(midi_note):
    """Suelta una nota individual del acorde."""
    if midi_note not in active_keys:
        return
    game_key, modifier, _, _ = active_keys.pop(midi_note)
    try:
        pydirectinput.keyUp(game_key)
        # No soltamos el modificador aquí porque ya se soltó
        # al terminar el grupo en play_chord
    except Exception as e:
        print(f"  [ERROR release] {e}")

def release_all():
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
    print("  [OK] Todas las teclas liberadas.")

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

def on_press(key):
    global current_speed

    if key == Key.f8:
        print("\n[F8] Deteniendo...")
        stop_flag.set()
        release_all()
        return False
    elif key == Key.f7:
        if pause_flag.is_set():
            pause_flag.clear()
            print("\n[F7] ▶ Reanudando...")
        else:
            pause_flag.set()
            release_all()
            print("\n[F7] ⏸ Pausado... (F7 reanudar, F8 detener)")
    elif key == Key.f5:
        with speed_lock:
            current_speed = 1.0
        print("\n[F5] Velocidad: NORMAL (1x)")
    elif key == Key.f6:
        with speed_lock:
            current_speed = 0.4
        print("\n[F6] Velocidad: LENTA (0.4x) — modo debug")

def start_stop_listener():
    with kb.Listener(on_press=on_press) as listener:
        listener.join()

# ─────────────────────────────────────────────
# REPRODUCTOR PRINCIPAL
# ─────────────────────────────────────────────

def play_midi(midi_path):
    print(f"\nCargando: {midi_path}")

    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        print(f"Error al cargar el MIDI: {e}")
        return

    print(f"  Duración:  {mid.length:.1f} segundos")
    print(f"  Tracks:    {len(mid.tracks)}")

    print("\nAnalizando tonalidad...")
    transpose = detect_key(mid)
    print(f"  Transposición: {transpose:+d} semitonos")

    print("\nDetectando rangos de octava...")
    octave_ranges = detect_octave_ranges(mid, transpose)

    print(f"\n{'─'*50}")
    print(f"  F5 = Velocidad normal (1x)")
    print(f"  F6 = Velocidad lenta  (0.4x) — debug")
    print(f"  F7 = Pausar / Reanudar")
    print(f"  F8 = Detener")
    print(f"{'─'*50}")
    print(f"\nPonte frente al piano en el juego.")

    for i in range(COUNTDOWN_SECONDS, 0, -1):
        if stop_flag.is_set():
            return
        print(f"  Empezando en {i}...")
        time.sleep(1)

    print("\n▶ Reproduciendo... (F6 para ir lento, F5 para volver a normal)\n")

    note_count  = 0
    # Acorde acumulado: notas que llegaron al mismo tiempo
    chord_batch = {}

    for msg in mid:
        if stop_flag.is_set():
            break

        # Si hay tiempo de espera, primero tocar el acorde acumulado
        if msg.time > 0 and chord_batch:
            play_chord(chord_batch)
            note_count += len(chord_batch)
            chord_batch = {}

        # Esperar el tiempo del mensaje (convertido a segundos)
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
            # Acumular en el acorde actual
            chord_batch[msg.note] = (game_key, modifier, octave_name, note_in_oct)

        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            # Si había acorde pendiente, tocarlo antes de soltar
            if chord_batch:
                play_chord(chord_batch)
                note_count += len(chord_batch)
                chord_batch = {}
            release_chord_note(msg.note)

    # Tocar lo que quede al final
    if chord_batch:
        play_chord(chord_batch)
        note_count += len(chord_batch)

    release_all()
    print(f"\n✓ Canción terminada. Total notas tocadas: {note_count}")

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python nte_piano_v3c.py <archivo.mid>")
        print("Ejemplo: python nte_piano_v3c.py Numb.mid")
        sys.exit(1)

    listener_thread = threading.Thread(target=start_stop_listener, daemon=True)
    listener_thread.start()

    try:
        play_midi(sys.argv[1])
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        stop_flag.set()
        release_all()