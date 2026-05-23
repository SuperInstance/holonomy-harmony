# holonomy-harmony

🎼 Chord progression analysis via holonomy — detect modulations, modal interchange, and cycle violations in harmony.

Holonomy-harmony proves that **harmonic movement = cycle consistency**. A chord progression has zero holonomy when it returns to its tonal center. When it doesn't, you've detected a modulation. This is constraint theory applied to music theory: the circle of fifths is a topological space, and chord progressions trace paths through it.

## Why it exists

Music theory has always had an implicit spatial structure — the circle of fifths, the line of fifths, voice-leading spaces. But the connection between harmonic motion and topological holonomy (the "did you end up where you started?" invariant) hasn't been made explicit in a tool. This library makes that connection executable: every chord progression gets a holonomy number, and that number tells you exactly how "far from home" the harmony wandered.

## The math in plain English

**Holonomy** measures whether a closed loop through a space returns you to the same orientation you started with. On the circle of fifths, each chord transition moves you clockwise (dominant direction) or counter-clockwise (subdominant direction). If you sum all those movements and get zero, the progression is tonally consistent — it returned home. If the sum is non-zero, you modulated.

**Winding number** counts how many full rotations around the circle of fifths the progression makes. A I-IV-V-I progression winds zero times. Coltrane's *Giant Steps* winds multiple times due to its major-third cycles.

**Stability score** (0–1) measures how "safe" a progression is: 1.0 = entirely diatonic, zero holonomy. 0.0 = highly chromatic with multiple modulations.

## Quick start

```bash
pip install holonomy-harmony
```

```python
from holonomy_harmony import analyze_progression, PROGRESSIONS

# Analyze the Pachelbel Canon progression in D major
symbols, tonic, mode = PROGRESSIONS["pachelbel_canon"]
result = analyze_progression(symbols, key_tonic=tonic, mode=mode)

print(f"Holonomy: {result.holonomy.holonomy}")        # -5
print(f"Winding:  {result.holonomy.winding_number}")   # 0.0833
print(f"Type:     {result.holonomy.progression_type}") # ProgressionType.MODULATION
print(f"Stability: {result.stability_score}")           # 0.35

# Analyze Giant Steps — much more adventurous
symbols, tonic, mode = PROGRESSIONS["giant_steps"]
result = analyze_progression(symbols, key_tonic=tonic, mode=mode)
print(f"Type:     {result.holonomy.progression_type}")  # ProgressionType.CHROMATIC
print(f"Stability: {result.stability_score}")            # lower
```

Output:
```
Holonomy: -5
Winding:  0.08333333333333333
Type:     ProgressionType.MODULATION
Stability: 0.35

Type:     ProgressionType.CHROMATIC_MEDIANT
Stability: 0.377
```

## API overview

### High-level: `analyze_progression`

```python
from holonomy_harmony import analyze_progression

result = analyze_progression(
    symbols=["I", "vi", "IV", "V"],  # Roman numerals
    key_tonic=0,                      # C
    mode="major",                     # major or minor
    wrap=False,                       # treat as closed cycle?
)
# result.chords            -> List[Chord]
# result.holonomy          -> HolonomyResult
# result.graph             -> TonalGraph
# result.modulations       -> List[(index, description)]
# result.modal_interchanges -> List[(index, description)]
# result.stability_score   -> float (0.0-1.0)
```

### Holonomy computation

```python
from holonomy_harmony import compute_holonomy, winding_number, classify_progression

roots = [0, 7, 9, 5, 0]  # C, G, A, F, C

h = compute_holonomy(roots, wrap=True)
print(h.holonomy)       # net circle-of-fifths displacement
print(h.winding_number) # full rotations
print(h.max_deviation)  # furthest wander from tonic
print(h.is_consistent())# True if holonomy == 0

print(winding_number(roots))    # shortcut
print(classify_progression(roots))  # ProgressionType enum
```

### Roman numeral parsing

```python
from holonomy_harmony import parse_roman

chord = parse_roman("V7/vi", key_tonic=0, mode="major")
# Chord(root=10, quality='7', function='V7/vi',
#        is_secondary_dominant=True, implied_key=(9, 'major'))
```

### Tonal graph

```python
from holonomy_harmony import TonalGraph

g = TonalGraph()
g.build_from_progression([0, 7, 9, 5, 0])
print(g)  # <TonalGraph nodes=12 edges=4 total_weight=4.0>
print(g.adjacency_matrix())  # 12×12 transition matrix
print(g.transition_probability(0, 7))  # P(G|C)
```

### Built-in progressions

20 famous progressions included:

```python
from holonomy_harmony import PROGRESSIONS

for name in PROGRESSIONS:
    symbols, tonic, mode = PROGRESSIONS[name]
    print(f"{name}: {' '.join(symbols)}")
```

Includes: `pachelbel_canon`, `blues_12_bar`, `giant_steps`, `chopin_em_prelude`, `axis_progression`, `autumn_leaves`, `coltrane_changes`, `rhythm_changes`, `hey_jude`, `creep`, `take_five`, and more.

## Architecture

```
┌─────────────┐    ┌───────────────┐    ┌──────────────┐
│  analyzer.py│───>│ cycle_checker │───>│ tonal_graph  │
│             │    │               │    │              │
│ parse_roman │    │ compute_      │    │ TonalGraph   │
│ analyze_    │    │ holonomy      │    │ Transition   │
│ progression │    │ winding_      │    │ Direction    │
│ detect_     │    │ number        │    │ adjacency    │
│ modulations │    │ classify_     │    │ matrix       │
│ score_      │    │ progression   │    │              │
│ stability   │    │ HolonomyResult│    │              │
└─────────────┘    └───────────────┘    └──────────────┘

Input: Roman numerals → Chord objects → pitch-class roots
Process: roots → circle-of-fifths steps → holonomy signature
Output: HolonomyResult + stability score + modulation list
```

## Documentation

- [User Guide](docs/USER-GUIDE.md) — Complete usage documentation
- [Developer Guide](docs/DEVELOPER-GUIDE.md) — Contributing and internals
- [Examples](examples/) — Working code examples

## Related repos

- [spline-midi-smooth](https://github.com/SuperInstance/spline-midi-smooth) — Spline interpolation for MIDI automation
- [plato-room-musician](https://github.com/SuperInstance/plato-room-musician) — PLATO rooms → MIDI music
- [tensor-midi](https://github.com/SuperInstance/tensor-midi) — INT8-saturated MIDI for neural synthesis

## Requirements

- Python 3.10+
- No external dependencies (pure Python)

## Install

```bash
pip install holonomy-harmony
```

Or from source:

```bash
git clone https://github.com/SuperInstance/holonomy-harmony.git
cd holonomy-harmony
pip install -e .
```

## License

Apache License 2.0
