#!/usr/bin/env python3
"""
modulation_detection.py — Find modulations in Giant Steps and other progressions.

Run:  python3 examples/modulation_detection.py

Demonstrates:
  - Using analyze_progression() to find key changes
  - Reading cumulative holonomy to track tonal drift
  - Comparing modulation patterns across different progressions
  - Understanding how holonomy detects key changes automatically
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from holonomy_harmony import (
    PROGRESSIONS,
    analyze_progression,
    detect_modulations,
    score_stability,
)
from holonomy_harmony.tonal_graph import pitch_name

DIVIDER = "=" * 70


def main():
    print(DIVIDER)
    print("Modulation Detection via Holonomy Analysis")
    print(DIVIDER)

    # ── Giant Steps — the quintessential modulation showcase ────────────────
    print("\n\n" + "─" * 50)
    print("  Giant Steps (John Coltrane)")
    print("─" * 50)

    symbols_gs, key_gs, mode_gs = PROGRESSIONS["giant_steps"]
    gs = analyze_progression(symbols_gs, key_tonic=key_gs, mode=mode_gs)

    print(f"  Key: B major (tonic={key_gs}, root={pitch_name(key_gs)})")
    print(f"  Chords: {' – '.join(symbols_gs)}")
    print(f"\n  Holonomy: {gs.holonomy.holonomy:+d} semitones")
    print(f"  Winding:  {gs.holonomy.winding_number:+.2f} rotations on circle of 5ths")
    print(f"  Type:     {gs.holonomy.progression_type.name}")
    print(f"  Stability: {score_stability(gs):.3f}")

    # ── Cumulative tonal drift ──────────────────────────────────────────────
    print("\n  Cumulative tonal displacement (circle-of-fifths steps):")
    cum = gs.holonomy.cumulative
    for i, c in enumerate(cum):
        bar = "█" * abs(c) if c != 0 else "·"
        sign = "+" if c > 0 else ("−" if c < 0 else " ")
        chord = symbols_gs[i] if i < len(symbols_gs) else "(wrap)"
        print(f"    After beat {i:>2} ({chord:>5}): {sign}{abs(c):>3}  {bar}")

    # ── Detected modulations ────────────────────────────────────────────────
    mods = detect_modulations(gs)
    print(f"\n  Detected modulations ({len(mods)}):")
    for idx, desc in mods:
        print(f"    Beat {idx}: {desc}")

    # ── Compare across several progressions ─────────────────────────────────
    print(f"\n\n{DIVIDER}")
    print("Modulation Patterns Across Progressions")
    print(DIVIDER)

    targets = [
        "giant_steps",
        "coltrane_changes",
        "pachelbel_canon",
        "creep",
        "chopin_em_prelude",
        "autumn_leaves",
        "blues_12_bar",
    ]

    for name in targets:
        if name not in PROGRESSIONS:
            continue
        symbols, key_tonic, mode = PROGRESSIONS[name]
        analysis = analyze_progression(symbols, key_tonic=key_tonic, mode=mode)
        mods = detect_modulations(analysis)
        h = analysis.holonomy

        print(f"\n  {name}:")
        print(f"    Chords: {' – '.join(symbols)}")
        print(f"    Holonomy={h.holonomy:+d}, winding={h.winding_number:+.2f}, "
              f"max_dev={h.max_deviation}, type={h.progression_type.name}")
        print(f"    Modulations: {len(mods)}")
        for idx, desc in mods:
            print(f"      → Beat {idx}: {desc}")

    # ── How holonomy detects modulations ────────────────────────────────────
    print(f"\n\n{DIVIDER}")
    print("How Holonomy Detects Modulations")
    print(DIVIDER)
    print("""
  The holonomy of a chord progression measures how far the tonal center
  drifts from its starting point. The key insight:

  • Zero holonomy → progression returns to the same key (diatonic)
  • Non-zero holonomy → the tonal center has shifted (modulation)

  The cumulative displacement is tracked on the circle of fifths:
  each chord transition adds a signed step. If the sum is zero at the
  end, the key has closed. If not, you've modulated.

  Giant Steps uses major-third root motion (I → III → bV → I...),
  which takes large steps around the circle of fifths, creating
  rapid cumulative drift — the hallmark of constant modulation.

  Pachelbel's Canon uses stepwise diatonic motion (I → V → vi → iii...),
  which stays close to the tonic — zero net drift, no modulation.""")

    print("\n✓ Modulation analysis complete.")


if __name__ == "__main__":
    main()
