#!/usr/bin/env python3
"""
progression.py — Generate and analyze chord progressions by holonomy.

Demonstrates:
- Using the built-in PROGRESSIONS database
- Classifying progressions by holonomy type
- Detecting modulations and modal interchange
- Scoring stability vs adventurousness
- Building and querying the tonal graph

Run:  python3 examples/progression.py
"""

from holonomy_harmony import (
    analyze_progression,
    PROGRESSIONS,
)
from holonomy_harmony.tonal_graph import pitch_name

print("PROGRESSION ANALYSIS: HOLONY-BASED CLASSIFICATION")
print("=" * 60)

# --- Analyze all built-in progressions ---
print(f"\n{'Name':22s} {'Key':>6s} {'Holonomy':>9s} {'Winding':>8s} {'MaxDev':>7s} {'Stability':>10s} {'Type':>20s}")
print("-" * 90)

for name, (symbols, key_tonic, mode) in PROGRESSIONS.items():
    analysis = analyze_progression(symbols, key_tonic=key_tonic, mode=mode)
    h = analysis.holonomy
    key_str = f"{pitch_name(key_tonic)} {mode}"
    print(f"{name:22s} {key_str:>6s} {h.holonomy:9d} {h.winding_number:8.2f} "
          f"{h.max_deviation:7d} {analysis.stability_score:10.3f} {h.progression_type.name:>20s}")

# --- Deep dive into a few progressions ---
deep_dives = ["pachelbel_canon", "giant_steps", "coltrane_changes", "creep", "chopin_em_prelude"]

for name in deep_dives:
    symbols, key_tonic, mode = PROGRESSIONS[name]
    analysis = analyze_progression(symbols, key_tonic=key_tonic, mode=mode)

    print()
    print(f"{'=' * 60}")
    print(f"DEEP DIVE: {name}")
    print(f"{'=' * 60}")
    print(f"  Key: {pitch_name(key_tonic)} {mode}")
    print(f"  Progression: {' → '.join(symbols)}")

    roots = [c.root for c in analysis.chords]
    print(f"  Roots: {' → '.join(pitch_name(r) for r in roots)}")

    print(f"  Holonomy: {analysis.holonomy.holonomy}")
    print(f"  Winding: {analysis.holonomy.winding_number:.2f}")
    print(f"  Max deviation: {analysis.holonomy.max_deviation}")
    print(f"  Type: {analysis.holonomy.progression_type.name}")
    print(f"  Consistent (closes): {analysis.holonomy.is_consistent()}")
    print(f"  Stability: {analysis.stability_score:.3f}")

    if analysis.modulations:
        print("  Modulations:")
        for idx, desc in analysis.modulations:
            print(f"    Beat {idx}: {desc}")

    if analysis.modal_interchanges:
        print("  Modal interchanges:")
        for idx, desc in analysis.modal_interchanges:
            print(f"    Beat {idx}: {desc}")

    # Show cumulative path
    print(f"  Cumulative Co5 path: {analysis.holonomy.cumulative}")

# --- Tonal graph for rhythm changes ---
print()
print(f"{'=' * 60}")
print("TONAL GRAPH: Rhythm Changes")
print(f"{'=' * 60}")

symbols, key_tonic, mode = PROGRESSIONS["rhythm_changes"]
analysis = analyze_progression(symbols, key_tonic=key_tonic, mode=mode)

for pc in range(12):
    neighbors = analysis.graph.neighbors(pc)
    if neighbors:
        for n in neighbors:
            w = analysis.graph.weight(pc, n)
            prob = analysis.graph.transition_probability(pc, n)
            print(f"  {pitch_name(pc)} → {pitch_name(n)}: weight={w:.1f}, P={prob:.2f}")
