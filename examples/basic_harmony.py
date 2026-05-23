#!/usr/bin/env python3
"""
basic_harmony.py — Analyze chord progressions using holonomy theory.

Demonstrates:
- Parsing Roman numeral chord symbols
- Analyzing a progression's holonomy (cycle consistency)
- Checking if a progression closes (zero holonomy = diatonic)
- Viewing the tonal graph built from transitions

Run:  python3 examples/basic_harmony.py
"""

from holonomy_harmony import (
    analyze_progression,
    Chord,
    parse_roman,
    compute_holonomy,
    winding_number,
)

# --- Parse individual chords ---
print("PARSING INDIVIDUAL CHORDS")
print("=" * 50)

symbols = ["I", "V", "vi", "IV", "ii", "V7", "bVI", "V/vi"]
for sym in symbols:
    chord = parse_roman(sym, key_tonic=0, mode="major")
    print(f"  {sym:6s} → {chord}")

print()

# --- Analyze I-V-vi-iii-IV-I-IV-V (Pachelbel's Canon) ---
print("PACHELBEL'S CANON (D major)")
print("=" * 50)

analysis = analyze_progression(
    ["I", "V", "vi", "iii", "IV", "I", "IV", "V"],
    key_tonic=2,  # D major
    mode="major",
)

print(f"Chords: {len(analysis.chords)}")
for c in analysis.chords:
    print(f"  {c}")

print()
print(f"Holonomy: {analysis.holonomy.holonomy}")
print(f"Winding number: {analysis.holonomy.winding_number:.2f}")
print(f"Max deviation: {analysis.holonomy.max_deviation}")
print(f"Type: {analysis.holonomy.progression_type.name}")
print(f"Is consistent (closes): {analysis.holonomy.is_consistent()}")
print()
print(f"Stability score: {analysis.stability_score:.3f}")
print(f"Modulations: {analysis.modulations}")
print(f"Modal interchanges: {analysis.modal_interchanges}")

# --- Show cumulative tonal path ---
print()
print("TONAL PATH (cumulative Co5 displacement):")
print("-" * 50)
for i, cum in enumerate(analysis.holonomy.cumulative):
    if i < len(analysis.chords):
        print(f"  After {analysis.chords[i].function:4s}: cumulative displacement = {cum}")
    else:
        print(f"  Final: cumulative displacement = {cum}")

# --- Tonal graph ---
print()
print(f"Tonal graph: {analysis.graph}")
for pc in range(12):
    neighbors = analysis.graph.neighbors(pc)
    if neighbors:
        from holonomy_harmony import TonalGraph
        from holonomy_harmony.tonal_graph import pitch_name
        for n in neighbors:
            w = analysis.graph.weight(pc, n)
            print(f"  {pitch_name(pc)} → {pitch_name(n)} (weight={w:.1f})")
