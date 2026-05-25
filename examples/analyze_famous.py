#!/usr/bin/env python3
"""
analyze_famous.py — Analyze all 20 progressions from the PROGRESSIONS database.

Run:  python3 examples/analyze_famous.py

Demonstrates:
  - Using the PROGRESSIONS database of famous chord progressions
  - Calling analyze_progression() with Roman-numeral symbols
  - Reading holonomy, stability score, and progression type
  - Detecting modulations and modal interchange
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from holonomy_harmony import (
    PROGRESSIONS,
    analyze_progression,
    score_stability,
    detect_modulations,
)

DIVIDER = "=" * 70


def main():
    print(DIVIDER)
    print("Holonomy Analysis of Famous Chord Progressions")
    print(DIVIDER)
    print(f"\nAnalyzing {len(PROGRESSIONS)} progressions from the built-in database.\n")

    # ── Header ──────────────────────────────────────────────────────────────
    print(f"{'Name':<22} {'Type':<20} {'Holon':>5} {'Wind':>6} {'Stab':>5} {'Mods':>4}")
    print("─" * 70)

    results = []

    for name, (symbols, key_tonic, mode) in PROGRESSIONS.items():
        analysis = analyze_progression(symbols, key_tonic=key_tonic, mode=mode)
        stability = score_stability(analysis)
        mods = detect_modulations(analysis)

        results.append((name, analysis, stability, mods))

        h = analysis.holonomy
        print(
            f"{name:<22} {h.progression_type.name:<20} "
            f"{h.holonomy:>+5} {h.winding_number:>+6.2f} "
            f"{stability:>5.2f} {len(mods):>4}"
        )

    # ── Detailed breakdown of top picks ─────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("Detailed Breakdown — Selected Progressions")
    print(DIVIDER)

    highlights = ["pachelbel_canon", "giant_steps", "coltrane_changes", "creep"]
    for name in highlights:
        if name not in PROGRESSIONS:
            continue
        symbols, key_tonic, mode = PROGRESSIONS[name]
        analysis = analyze_progression(symbols, key_tonic=key_tonic, mode=mode)

        print(f"\n{'─' * 50}")
        print(f"  {name}")
        print(f"  Key: root={key_tonic}, mode={mode}")
        print(f"  Chords: {' – '.join(symbols)}")

        h = analysis.holonomy
        print(f"  Holonomy: {h.holonomy:+d} semitones")
        print(f"  Winding number: {h.winding_number:+.2f} rotations on circle of 5ths")
        print(f"  Max deviation: {h.max_deviation}")
        print(f"  Type: {h.progression_type.name}")
        print(f"  Stability: {score_stability(analysis):.3f}")

        if analysis.modulations:
            print("  Modulations:")
            for idx, desc in analysis.modulations:
                print(f"    Beat {idx}: {desc}")

        if analysis.modal_interchanges:
            print("  Modal interchanges:")
            for idx, desc in analysis.modal_interchanges:
                print(f"    Beat {idx}: {desc}")

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("Summary")
    print(DIVIDER)

    most_stable = max(results, key=lambda r: r[2])
    least_stable = min(results, key=lambda r: r[2])
    zero_holonomy = [r for r in results if r[1].holonomy.holonomy == 0]

    print(f"\n  Most stable:      {most_stable[0]} (stability={most_stable[2]:.3f})")
    print(f"  Least stable:     {least_stable[0]} (stability={least_stable[2]:.3f})")
    print(f"  Zero holonomy:    {len(zero_holonomy)}/{len(results)} progressions close in the same key")

    print(f"\n✓ Analyzed all {len(PROGRESSIONS)} progressions.")


if __name__ == "__main__":
    main()
