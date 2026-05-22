# User Guide — holonomy-harmony

## Table of Contents

1. [Overview](#overview)
2. [Core concepts](#core-concepts)
3. [Analyzing a progression](#analyzing-a-progression)
4. [Roman numeral syntax](#roman-numeral-syntax)
5. [Holonomy computation](#holonomy-computation)
6. [Modulation detection](#modulation-detection)
7. [Stability scoring](#stability-scoring)
8. [Tonal graph](#tonal-graph)
9. [Built-in progressions](#built-in-progressions)
10. [Input/output formats](#inputoutput-formats)
11. [Configuration](#configuration)
12. [Use cases](#use-cases)
13. [Troubleshooting](#troubleshooting)

## Overview

holonomy-harmony treats chord progressions as paths through a topological space (the circle of fifths). The key invariant is **holonomy**: whether the path returns to its starting orientation. This library computes that invariant and uses it to classify progressions, detect modulations, and score harmonic stability.

## Core concepts

### Pitch classes

All computation uses pitch classes 0–11 (C through B). The mapping:

| PC | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|----|---|---|---|---|---|---|---|---|---|---|----|----|
| Name | C | C# | D | D# | E | F | F# | G | G# | A | A# | B |

### Circle of fifths

Pitch classes ordered by ascending perfect fifths: C, G, D, A, E, B, F#, C#, G#, D#, A#, F. Each step on this circle is +7 semitones (mod 12). The holonomy computation measures displacement on *this* circle, not in chromatic space.

### Holonomy

The net circle-of-fifths displacement after traversing a progression. Zero holonomy = the progression closes in the same key. Non-zero = you've modulated.

### Winding number

How many full rotations around the circle of fifths the progression makes. Divide the total circle-of-fifths displacement by 12.

### Stability score

A 0–1 composite metric: diatonic ratio, holonomy penalty, max deviation penalty, modulation count, and modal interchange count. 1.0 = entirely diatonic. 0.0 = maximally chromatic.

## Analyzing a progression

The main entry point is `analyze_progression`:

```python
from holonomy_harmony import analyze_progression

result = analyze_progression(
    symbols=["I", "IV", "V", "I"],
    key_tonic=0,    # C major
    mode="major",
    wrap=False,
)
```

The returned `ProgressionAnalysis` contains:

| Attribute | Type | Description |
|-----------|------|-------------|
| `chords` | `List[Chord]` | Parsed chord objects |
| `holonomy` | `HolonomyResult` | Holonomy signature |
| `graph` | `TonalGraph` | Directed transition graph |
| `modulations` | `List[Tuple[int, str]]` | (index, description) pairs |
| `modal_interchanges` | `List[Tuple[int, str]]` | Borrowed chords |
| `stability_score` | `float` | 0.0–1.0 stability |

### Chord object

```python
chord = result.chords[0]
chord.root          # int, pitch class 0-11
chord.root_name     # str, e.g. "C"
chord.quality       # str, e.g. "maj", "min", "7"
chord.function      # str, e.g. "I", "V/vi"
chord.key           # (tonic_pc, mode)
chord.key_name      # "C major"
chord.is_diatonic   # bool
chord.is_secondary_dominant  # bool
chord.implied_key   # (tonic_pc, mode)
```

## Roman numeral syntax

The parser accepts standard Roman numerals:

| Symbol | Meaning |
|--------|---------|
| `I`, `II`, `III` ... | Major scale degrees (uppercase = major quality) |
| `i`, `ii`, `iii` ... | Minor scale degrees (lowercase = minor quality) |
| `bIII`, `bVI`, `bVII` | Flatted degrees (borrowed from parallel minor) |
| `#IV` | Sharped degree |
| `V7`, `vi7` | With quality suffix |
| `V/vi`, `V7/IV` | Secondary dominants |

### Quality suffixes

| Suffix | Quality |
|--------|---------|
| (none) | Inferred from scale degree |
| `7` | Dominant 7th |
| `maj7` | Major 7th |
| `m7`, `min7` | Minor 7th |
| `dim` | Diminished |
| `dim7` | Diminished 7th |
| `ø7`, `m7b5` | Half-diminished |
| `+`, `aug` | Augmented |
| `sus4`, `sus2` | Suspended |
| `6`, `m6` | Sixth chords |
| `9`, `maj9`, `m9` | Ninth chords |

## Holonomy computation

### Direct computation on pitch classes

If you already have pitch-class roots (not Roman numerals), use `compute_holonomy` directly:

```python
from holonomy_harmony import compute_holonomy

roots = [0, 5, 7, 0]  # C, F, G, C (I-IV-V-I)
result = compute_holonomy(roots, wrap=False)

result.holonomy         # int: net semitone displacement
result.winding_number   # float: full Co5 rotations
result.max_deviation    # int: furthest from tonic on Co5
result.progression_type # ProgressionType enum
result.is_consistent()  # True if holonomy == 0
result.cumulative       # List[int]: displacement at each step
result.steps            # List[(from, to, direction)]
```

### Wrapping

Set `wrap=True` to treat the progression as a closed cycle (appends the first root to the end):

```python
# Open: I → IV → V → I (already closes)
compute_holonomy([0, 5, 7, 0], wrap=False)

# Closed: I → IV → V (wraps back to I)
compute_holonomy([0, 5, 7], wrap=True)
```

### Winding number shortcut

```python
from holonomy_harmony import winding_number

w = winding_number([0, 7, 2, 9, 4, 11, 6])  # Giant Steps roots
# Non-zero: the progression spirals around the circle of fifths
```

### Classification

```python
from holonomy_harmony import classify_progression

ptype = classify_progression([0, 5, 7, 0])
# ProgressionType.DIATONIC
```

The `ProgressionType` enum:

| Type | Meaning |
|------|---------|
| `DIATONIC` | Zero holonomy, stays in one key |
| `MODAL_INTERCHANGE` | Returned home but wandered (borrowed chords) |
| `MODULATION` | Key change, non-zero holonomy |
| `CHROMATIC_MEDIANT` | Multiple root motions by third |
| `CHROMATIC` | Highly chromatic, large holonomy |
| `UNKNOWN` | Doesn't fit other categories |

## Modulation detection

Modulations are identified by:

1. **Secondary dominants** — chords like `V/vi` that temporarily tonicize a new key
2. **Non-diatonic chords** that aren't borrowings from the parallel mode
3. **Holonomy deviation** — cumulative displacement on the circle of fifths

```python
result = analyze_progression(["I", "V/vi", "vi", "IV", "V", "I"])
for idx, desc in result.modulations:
    print(f"Beat {idx}: {desc}")
# Beat 1: Secondary dominant V/vi implies (9, 'major')
```

### Modal interchange

Borrowed chords from the parallel mode are reported separately:

```python
result = analyze_progression(["I", "bVI", "bVII", "I"], key_tonic=0, mode="major")
for idx, desc in result.modal_interchanges:
    print(f"Beat {idx}: {desc}")
# Beat 1: Borrowed chord bVI from parallel minor
# Beat 2: Borrowed chord bVII from parallel minor
```

## Stability scoring

The stability score combines several factors:

| Factor | Effect |
|--------|--------|
| Diatonic ratio | Base score = proportion of diatonic chords |
| Non-zero holonomy | ×0.5 penalty |
| Max deviation > 3 | ×0.7 penalty |
| Max deviation > 1 | ×0.9 penalty |
| Each modulation | ×(1 − 0.2 × count) penalty |
| Each interchange | ×(1 − 0.05 × count) penalty |
| Zero holonomy bonus | +0.1 |

```python
from holonomy_harmony import score_stability

result = analyze_progression(["I", "IV", "V", "I"])
print(score_stability(result))  # ~1.0

result = analyze_progression(["I", "III", "bV", "I"])
print(score_stability(result))  # much lower
```

## Tonal graph

`TonalGraph` is a directed graph where nodes are pitch classes and edges are transitions observed in a progression, weighted by frequency.

```python
from holonomy_harmony import TonalGraph

g = TonalGraph()
g.build_from_progression([0, 5, 7, 0, 5, 7, 0])

# Edge queries
g.get_edge(0, 5)              # Edge(source=0, target=5, weight=2.0, ...)
g.weight(0, 5)                # 2.0
g.normalized_weight(0, 5)     # ~0.286
g.transition_probability(0, 5) # P(F|C) in this progression

# Degree
g.out_degree(0)               # 1 (only goes to F)
g.in_degree(0)                # 2 (from F and G)

# Full matrix
matrix = g.adjacency_matrix()  # 12×12 List[List[float]]

# Neighbors
g.neighbors(7)                 # [0] (G goes to C)
```

### Manual graph construction

```python
from holonomy_harmony import TonalGraph, TransitionDirection

g = TonalGraph()
g.add_transition(0, 7, weight=3.0)   # C → G, weight 3
g.add_transition(0, 7, weight=1.0)   # increments to 4.0
g.add_transition(7, 0, weight=2.0, direction=TransitionDirection.RESOLUTION)
```

## Built-in progressions

The `PROGRESSIONS` dict maps names to `(symbols, key_tonic, mode)`:

```python
from holonomy_harmony import PROGRESSIONS

# List all names
print(list(PROGRESSIONS.keys()))
# ['pachelbel_canon', 'blues_12_bar', 'giant_steps', 'chopin_em_prelude',
#  'axis_progression', 'andulusian_cadence', 'doo_wop', 'sensitive_female',
#  'rhythm_changes', 'bird_changes', 'montgomery_ward', 'plagal_cadence',
#  'perfect_cadence', 'deceptive_cadence', 'coltrane_changes', 'minor_ii_v_i',
#  'take_five', 'hey_jude', 'creep', 'autumn_leaves']

# Use one
symbols, tonic, mode = PROGRESSIONS["blues_12_bar"]
result = analyze_progression(symbols, key_tonic=tonic, mode=mode)
```

| Name | Key | Chords |
|------|-----|--------|
| `pachelbel_canon` | D major | I V vi iii IV I IV V |
| `blues_12_bar` | C major | I I I I IV IV I I V IV I V |
| `giant_steps` | B major | I V IV V bVII ii V I bV bVII bIII V I |
| `axis_progression` | C major | I V vi IV |
| `autumn_leaves` | C minor | ii V I IV bVII iii vi II bII i V i |
| `coltrane_changes` | C major | I III bV I bIII bV bbVII I |
| `creep` | C major | I III IV iv |
| `hey_jude` | C major | I bVII IV I |

## Input/output formats

### Input

- **Roman numerals**: `List[str]` like `["I", "IV", "V", "I"]`
- **Pitch classes**: `List[int]` 0–11 for `compute_holonomy`
- **Key tonic**: `int` 0–11 (0=C)
- **Mode**: `"major"` or `"minor"`

### Output

- `ProgressionAnalysis` — full analysis object
- `HolonomyResult` — holonomy signature
- `ProgressionType` — enum classification
- `Chord` — individual chord in tonal context
- `TonalGraph` — directed weighted graph

## Configuration

`analyze_progression` accepts:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbols` | `List[str]` | required | Roman numerals |
| `key_tonic` | `int` | `0` | Home key (0=C) |
| `mode` | `str` | `"major"` | Major or minor |
| `wrap` | `bool` | `False` | Close the cycle |

`compute_holonomy` accepts:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `roots` | `List[int]` | required | Pitch-class roots |
| `wrap` | `bool` | `False` | Close the cycle |

## Use cases

### 1. Classify any progression

```python
from holonomy_harmony import classify_progression
print(classify_progression([0, 5, 7, 0]))    # DIATONIC
print(classify_progression([0, 4, 8, 0]))    # CHROMATIC_MEDIANT
```

### 2. Compare harmonic stability across songs

```python
from holonomy_harmony import analyze_progression, PROGRESSIONS

for name, (sym, t, m) in PROGRESSIONS.items():
    result = analyze_progression(sym, t, m)
    print(f"{name:25s} stability={result.stability_score:.2f}")
```

### 3. Detect modulations in a song

```python
result = analyze_progression(
    ["I", "IV", "V", "I", "V/vi", "vi", "ii", "V", "I"],
    key_tonic=0, mode="major"
)
for idx, desc in result.modulations:
    print(f"Chord {idx}: {desc}")
```

### 4. Build a tonal transition matrix

```python
from holonomy_harmony import TonalGraph, PROGRESSIONS
import json

g = TonalGraph()
for name, (sym, t, m) in PROGRESSIONS.items():
    from holonomy_harmony import parse_roman
    roots = [parse_roman(s, t, m).root for s in sym]
    g.build_from_progression(roots)

matrix = g.adjacency_matrix()
print(json.dumps(matrix, indent=2))
```

### 5. Find the "adventurous" progressions

```python
from holonomy_harmony import analyze_progression, PROGRESSIONS

adventurous = []
for name, (sym, t, m) in PROGRESSIONS.items():
    result = analyze_progression(sym, t, m)
    if result.stability_score < 0.5:
        adventurous.append((name, result.stability_score))

adventurous.sort(key=lambda x: x[1])
for name, score in adventurous:
    print(f"{name}: {score:.2f}")
```

### 6. Analyze a custom progression in an arbitrary key

```python
result = analyze_progression(
    symbols=["I", "bVI", "bVII", "I"],
    key_tonic=7,  # G major
    mode="major",
)
print(f"Key: {result.chords[0].key_name}")  # "G major"
```

## Troubleshooting

### "Cannot parse Roman numeral"

Check that your symbols use standard notation: `I` through `VII` (uppercase for major, lowercase for minor), optional `b`/`#` prefix, optional quality suffix. Avoid spaces or special characters.

### "Pitch class must be 0-11"

Pitch classes wrap chromatically. If you're computing intervals manually, use `(value % 12)` to wrap.

### "roots list is empty"

`compute_holonomy` requires at least one root. For meaningful results, provide at least two.

### Stability score seems wrong

The stability score combines several heuristics. It's a composite metric, not a ground truth. Use it for relative comparison (ranking progressions) rather than absolute judgment.

### Secondary dominants not detected

Ensure you're using the `/` syntax: `V/vi`, `V7/IV`. The parser recognizes the target as a Roman numeral in the current key.

### Progression classified as UNKNOWN

This happens when the holonomy signature doesn't match any of the defined patterns. Check the raw `holonomy`, `max_deviation`, and `winding_number` values to understand why.
