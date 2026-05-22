# Holonomy Harmony — Developer Guide

## Architecture

```
holonomy_harmony/
├── __init__.py         # Public API re-exports
├── tonal_graph.py      # TonalGraph, pitch class utilities, TransitionDirection
├── cycle_checker.py    # Holonomy computation, winding number, classification
├── analyzer.py         # Chord class, analyze_progression, modulations, PROGRESSIONS
tests/
├── __init__.py
```

### Module Diagram

```
┌────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  tonal_graph.py│────▶│cycle_checker.py  │────▶│  analyzer.py │
│ (pitch classes,│     │(holonomy, winding│     │(Chord,       │
│  TonalGraph,   │     │ number, classify)│     │ progression  │
│  directions)   │     └──────────────────┘     │ analysis)    │
└────────────────┘                               └──────────────┘
```

### Design Decisions

- **Circle of fifths as coordinate system:** Chord roots are mapped to positions on the circle of fifths (0=C, 1=G, 2=D, ...). Holonomy is computed as net displacement on this circle.
- **Pure Python:** No external dependencies. All math is integer arithmetic and simple geometry.
- **Pitch classes 0–11:** The chromatic scale is the universal representation. All analysis works on pitch classes regardless of notation.

## Extending

### Adding a New Transition Direction

Add to `TransitionDirection` enum in `tonal_graph.py` and update `classify_direction()`:

```python
class TransitionDirection(Enum):
    ...
    NEAPOLITAN = auto()    # flat-II chord

def classify_direction(from_pc: int, to_pc: int) -> TransitionDirection:
    diff = (to_pc - from_pc) % 12
    ...
    if diff == 1:
        return TransitionDirection.NEAPOLITAN
    ...
```

### Adding a New Progression Type

Add to `ProgressionType` enum in `cycle_checker.py` and update `_classify_from_signature()`:

```python
class ProgressionType(Enum):
    ...
    BLUES = auto()    # 12-bar blues pattern

def _classify_from_signature(holonomy, max_dev, winding, steps):
    ...
    # Detect blues: I→IV→I→V→I pattern
    roots = [a for a, b, d in steps]
    if _is_blues_form(roots):
        return ProgressionType.BLUES
    ...
```

### Adding Analysis Functions

Follow the pattern in `analyzer.py`:

```python
def harmonic_rhythm(roots: List[int], beats_per_chord: float = 1.0) -> Dict[str, float]:
    """Measure how frequently chords change."""
    changes = sum(1 for a, b in zip(roots, roots[1:]) if a != b)
    return {
        "total_changes": changes,
        "rate": changes / (len(roots) * beats_per_chord),
    }
```

### Adding to PROGRESSIONS

```python
PROGRESSIONS["ii-V-I"] = [2, 7, 0]
PROGRESSIONS["12_bar_blues"] = [0, 0, 0, 0, 5, 5, 0, 0, 7, 5, 0, 0]
```

## Testing

```bash
pytest                    # all tests
pytest -v                 # verbose
pytest --cov=holonomy_harmony  # coverage
```

### Test Patterns

```python
def test_i_iv_v_i_diatonic():
    h = compute_holonomy([0, 5, 7, 0], wrap=True)
    assert h.holonomy == 0
    assert h.progression_type == ProgressionType.DIATONIC

def test_circle_of_fifths_winds_once():
    cof = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5, 0]
    h = compute_holonomy(cof, wrap=True)
    assert abs(h.winding_number - 1.0) < 0.01
```

## Contributing

1. Fork, branch, implement, test, PR
2. Pure Python only — no external dependencies
3. All new public functions need docstrings with Parameters/Returns
4. Pitch class operations go in `tonal_graph.py`
5. Holonomy/cycle operations go in `cycle_checker.py`
6. High-level analysis goes in `analyzer.py`

### Code Style

- Python 3.10+ (`from __future__ import annotations`)
- `Enum`/`IntEnum` for categorical types
- `@dataclass(frozen=True, slots=True)` for immutable result types
- `Tuple[int, int]` for graph edges
- Docstrings with Parameters/Returns on all public functions

### Build System

`pyproject.toml` with setuptools. No external dependencies.

```bash
pip install -e .
pip install -e ".[dev]"  # with pytest
```
