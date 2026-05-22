#!/usr/bin/env python3
"""
coltrane_vs_pachelbel.py — Compare Coltrane changes vs Pachelbel canon.

Run:  python3 examples/coltrane_vs_pachelbel.py

Demonstrates:
  - Analyzing two contrasting progressions side by side
  - Comparing holonomy, winding numbers, and stability
  - Understanding why chromatic mediant motion creates tension
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


def print_section(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main():
    print(DIVIDER)
    print("Coltrane Changes vs Pachelbel Canon — A Holonomy Comparison")
    print(DIVIDER)

    # ── Pachelbel Canon ─────────────────────────────────────────────────────
    symbols_p, key_p, mode_p = PROGRESSIONS["pachelbel_canon"]
    pach = analyze_progression(symbols_p, key_tonic=key_p, mode=mode_p)

    print_section("Pachelbel Canon (D major)")
    print(f"  Chords:   {' – '.join(symbols_p)}")
    print(f"  Key:      D major (tonic={key_p})")
    print(f"  Holonomy: {pach.holonomy.holonomy:+d} semitones")
    print(f"  Winding:  {pach.holonomy.winding_number:+.2f} rotations")
    print(f"  Max dev:  {pach.holonomy.max_deviation}")
    print(f"  Type:     {pach.holonomy.progression_type.name}")
    print(f"  Stability: {score_stability(pach):.3f}")

    if pach.modulations:
        print(f"  Modulations:")
        for idx, desc in pach.modulations:
            print(f"    Beat {idx}: {desc}")
    else:
        print(f"  Modulations: none (purely diatonic)")

    # ── Coltrane Changes ────────────────────────────────────────────────────
    symbols_c, key_c, mode_c = PROGRESSIONS["coltrane_changes"]
    coltrane = analyze_progression(symbols_c, key_tonic=key_c, mode=mode_c)

    print_section("Coltrane Changes (Giant Steps harmony)")
    print(f"  Chords:   {' – '.join(symbols_c)}")
    print(f"  Key:      C major (tonic={key_c})")
    print(f"  Holonomy: {coltrane.holonomy.holonomy:+d} semitones")
    print(f"  Winding:  {coltrane.holonomy.winding_number:+.2f} rotations")
    print(f"  Max dev:  {coltrane.holonomy.max_deviation}")
    print(f"  Type:     {coltrane.holonomy.progression_type.name}")
    print(f"  Stability: {score_stability(coltrane):.3f}")

    if coltrane.modulations:
        print(f"  Modulations:")
        for idx, desc in coltrane.modulations:
            print(f"    Beat {idx}: {desc}")

    # ── Head-to-head comparison ─────────────────────────────────────────────
    print_section("Head-to-Head Comparison")

    print(f"\n  {'Metric':<25} {'Pachelbel':>12} {'Coltrane':>12}")
    print(f"  {'─' * 25} {'─' * 12} {'─' * 12}")
    print(f"  {'Holonomy (semitones)':<25} {pach.holonomy.holonomy:>+12} {coltrane.holonomy.holonomy:>+12}")
    print(f"  {'Winding number':<25} {pach.holonomy.winding_number:>+12.2f} {coltrane.holonomy.winding_number:>+12.2f}")
    print(f"  {'Max deviation':<25} {pach.holonomy.max_deviation:>12} {coltrane.holonomy.max_deviation:>12}")
    print(f"  {'Stability score':<25} {score_stability(pach):>12.3f} {score_stability(coltrane):>12.3f}")
    print(f"  {'Progression type':<25} {pach.holonomy.progression_type.name:>12} {coltrane.holonomy.progression_type.name:>12}")
    print(f"  {'# Modulations':<25} {len(detect_modulations(pach)):>12} {len(detect_modulations(coltrane)):>12}")
    print(f"  {'# Chords':<25} {len(symbols_p):>12} {len(symbols_c):>12}")

    # ── Interpretation ──────────────────────────────────────────────────────
    print_section("Interpretation")
    print("""
  Pachelbel's Canon stays close to home — its root motion cycles
  through diatonic scale degrees with minimal holonomy. The progression
  closes exactly where it started. This is why it feels restful and
  endlessly repeatable.

  Coltrane's Changes use chromatic mediant motion (root shifts by
  major thirds), which creates large jumps on the circle of fifths.
  The result: high holonomy, rapid key shifts, and a sense of
  constant harmonic acceleration. It's the opposite of Pachelbel —
  instead of comfort, it creates dazzling tension and release.""")

    print(f"\n✓ Comparison complete.")


if __name__ == "__main__":
    main()
