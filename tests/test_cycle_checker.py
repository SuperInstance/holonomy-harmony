"""Tests for holonomy_harmony.cycle_checker."""

import pytest

from holonomy_harmony.cycle_checker import (
    ProgressionType,
    classify_progression,
    compute_holonomy,
    winding_number,
)


# ---------------------------------------------------------------------------
# compute_holonomy
# ---------------------------------------------------------------------------

class TestComputeHolonomy:
    def test_i_iv_v_i_closed(self):
        """I-IV-V-I should have zero holonomy (closed tonal cycle)."""
        # C=0, F=5, G=7, C=0
        result = compute_holonomy([0, 5, 7, 0])
        assert result.holonomy == 0

    def test_i_iv_v_i_wrapped(self):
        """I-IV-V-I with wrap=True should also be zero (appends first root)."""
        result = compute_holonomy([0, 5, 7], wrap=True)
        assert result.holonomy == 0

    def test_chromatic_walk_nonzero(self):
        """Chromatic walk C→C#→D→D#→E should have non-zero holonomy."""
        result = compute_holonomy([0, 1, 2, 3, 4])
        assert result.holonomy != 0

    def test_single_root(self):
        """Single root should have zero holonomy."""
        result = compute_holonomy([0])
        assert result.holonomy == 0
        assert result.max_deviation == 0
        assert len(result.steps) == 0

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            compute_holonomy([])

    def test_coltrane_changes_nonzero(self):
        """Coltrane-style major-third cycle should have non-zero winding number."""
        # C=0, E=4, Ab=8, C=0
        result = compute_holonomy([0, 4, 8, 0])
        # The cycle returns to C (holonomy=0 in semitones) but spirals on Co5
        assert result.winding_number != 0

    def test_wrap_extends_path(self):
        """wrap=True appends first root, creating one extra step."""
        result_open = compute_holonomy([0, 5, 7])
        result_wrap = compute_holonomy([0, 5, 7], wrap=True)
        assert len(result_wrap.steps) == len(result_open.steps) + 1

    def test_cumulative_starts_at_zero(self):
        result = compute_holonomy([0, 5, 7, 0])
        assert result.cumulative[0] == 0

    def test_max_deviation_non_negative(self):
        result = compute_holonomy([0, 5, 7, 0])
        assert result.max_deviation >= 0

    def test_is_consistent_when_zero(self):
        result = compute_holonomy([0, 5, 7, 0])
        assert result.is_consistent()

    def test_steps_have_directions(self):
        result = compute_holonomy([0, 7])
        assert len(result.steps) == 1
        assert result.steps[0][0] == 0  # from_pc
        assert result.steps[0][1] == 7  # to_pc


# ---------------------------------------------------------------------------
# winding_number
# ---------------------------------------------------------------------------

class TestWindingNumber:
    def test_diatonic_zero(self):
        """I-IV-V-I should have winding number close to 0."""
        w = winding_number([0, 5, 7, 0])
        assert abs(w) < 1.0

    def test_single_root_zero(self):
        assert winding_number([0]) == 0.0

    def test_empty_zero(self):
        assert winding_number([]) == 0.0


# ---------------------------------------------------------------------------
# classify_progression
# ---------------------------------------------------------------------------

class TestClassifyProgression:
    def test_i_iv_v_i_diatonic(self):
        """I-IV-V-I should classify as DIATONIC."""
        ptype = classify_progression([0, 5, 7, 0])
        assert ptype == ProgressionType.DIATONIC

    def test_i_vi_diatonic(self):
        """I-vi is a mediant move; classification depends on Co5 displacement."""
        ptype = classify_progression([0, 9])
        # I-vi moves 3 steps on Co5; may be MODAL_INTERCHANGE or MODULATION
        assert ptype != ProgressionType.CHROMATIC

    def test_chromatic_walk(self):
        """Chromatic walk should not be DIATONIC."""
        ptype = classify_progression([0, 1, 2, 3, 4])
        assert ptype != ProgressionType.DIATONIC

    def test_coltrane_major_thirds(self):
        """Coltrane major-third cycle should classify as chromatic or modulation."""
        ptype = classify_progression([0, 4, 8, 0])
        assert ptype in (ProgressionType.CHROMATIC, ProgressionType.MODULATION,
                         ProgressionType.CHROMATIC_MEDIANT)

    def test_giant_steps(self):
        """Giant steps progression should be complex."""
        # B=11, D=2, F=5, B=11 — major third cycle
        ptype = classify_progression([11, 2, 5, 11, 2, 5, 11])
        assert ptype != ProgressionType.DIATONIC


# ---------------------------------------------------------------------------
# HolonomyResult fields
# ---------------------------------------------------------------------------

class TestHolonomyResult:
    def test_fields_present(self):
        result = compute_holonomy([0, 5, 7, 0])
        assert hasattr(result, "holonomy")
        assert hasattr(result, "winding_number")
        assert hasattr(result, "max_deviation")
        assert hasattr(result, "progression_type")
        assert hasattr(result, "steps")
        assert hasattr(result, "cumulative")

    def test_repr_contains_holonomy(self):
        result = compute_holonomy([0, 5, 7, 0])
        r = repr(result)
        assert "holonomy=" in r
        assert "DIATONIC" in r
