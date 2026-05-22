"""
Holonomy-Harmony: A chord progression analyzer based on constraint theory.

Proves that harmonic movement = cycle consistency via holonomy detection.
"""

from .tonal_graph import TonalGraph, TransitionDirection
from .cycle_checker import (
    compute_holonomy,
    winding_number,
    classify_progression,
    HolonomyResult,
)
from .analyzer import (
    Chord,
    parse_roman,
    analyze_progression,
    detect_modulations,
    score_stability,
    PROGRESSIONS,
)

__all__ = [
    "TonalGraph",
    "TransitionDirection",
    "compute_holonomy",
    "winding_number",
    "classify_progression",
    "HolonomyResult",
    "Chord",
    "parse_roman",
    "analyze_progression",
    "detect_modulations",
    "score_stability",
    "PROGRESSIONS",
]
