#!/usr/bin/env python3
"""
voice_leading.py — Analyze smooth voice leading through holonomy.

Demonstrates:
- Comparing progressions with different voice-leading smoothness
- How semitone intervals between roots relate to holonomy
- Common-tone preservation and minimal root movement
- The relationship between voice leading and cycle consistency

Run:  python3 examples/voice_leading.py
"""

from holonomy_harmony import (
    analyze_progression,
    compute_holonomy,
    TonalGraph,
    Chord,
    parse_roman,
)
from holonomy_harmony.tonal_graph import semitone_interval, pitch_name

# --- Compare smooth vs jumpy progressions ---
print("VOICE LEADING: SMOOTH vs JUMPY PROGRESSIONS")
print("=" * 60)

# Smooth: I-vi-IV-V (axis progression — lots of common tones)
smooth = ["I", "vi", "IV", "V"]
# Jumpy: I-bVI-bIII-bVII (chromatic mediant — large leaps)
jumpy = ["I", "bVI", "bIII", "bVII"]
# Very smooth: I-iii-vi-IV (descending thirds)
thirds_chain = ["I", "iii", "vi", "IV"]

for label, symbols in [("Smooth (I-vi-IV-V)", smooth), ("Jumpy (I-bVI-bIII-bVII)", jumpy), ("Thirds (I-iii-vi-IV)", thirds_chain)]:
    analysis = analyze_progression(symbols, key_tonic=0, mode="major")
    roots = [c.root for c in analysis.chords]

    print(f"\n  {label}")
    print(f"  Roots: {[pitch_name(r) for r in roots]}")

    # Show intervals between consecutive roots
    intervals = []
    for i in range(len(roots) - 1):
        iv = semitone_interval(roots[i], roots[i + 1])
        intervals.append(iv)
    print(f"  Semitone intervals: {intervals}")
    print(f"  Total semitone motion: {sum(abs(iv) for iv in intervals)}")

    print(f"  Holonomy: {analysis.holonomy.holonomy} | Type: {analysis.holonomy.progression_type.name}")
    print(f"  Stability: {analysis.stability_score:.3f}")
    print(f"  Max deviation: {analysis.holonomy.max_deviation}")

# --- Show voice-leading distance for famous progressions ---
print()
print("VOICE-LEADING DISTANCE COMPARISON")
print("=" * 60)

famous = {
    "Pachelbel Canon": ["I", "V", "vi", "iii", "IV", "I", "IV", "V"],
    "Blues 12-bar":    ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"],
    "Axis (I-V-vi-IV)": ["I", "V", "vi", "IV"],
    "Doo-wop":         ["I", "vi", "IV", "V"],
    "Rhythm changes":  ["I", "vi", "ii", "V"],
    "Giant Steps":     ["I", "V", "IV", "V", "bVII", "ii", "V", "I", "bV", "bVII", "bIII", "V", "I"],
}

print(f"\n{'Progression':20s} {'Total Motion':>13s} {'Max Leap':>9s} {'Holonomy':>9s} {'Type':>18s}")
print("-" * 75)

for name, symbols in famous.items():
    analysis = analyze_progression(symbols, key_tonic=0, mode="major")
    roots = [c.root for c in analysis.chords]
    intervals = [abs(semitone_interval(roots[i], roots[i+1])) for i in range(len(roots)-1)]
    total_motion = sum(intervals)
    max_leap = max(intervals) if intervals else 0

    print(f"{name:20s} {total_motion:13d} {max_leap:9d} {analysis.holonomy.holonomy:9d} {analysis.holonomy.progression_type.name:>18s}")

print()
print("KEY INSIGHT: Smooth voice leading = small total semitone motion.")
print("Diatonic progressions have zero holonomy (they close in the same key).")
print("Giant Steps has large motion and non-zero holonomy (rapid modulations).")
