"""Tests for holonomy_harmony.tonal_graph."""

import pytest

from holonomy_harmony.tonal_graph import (
    PITCH_NAMES,
    TonalGraph,
    TransitionDirection,
    circle_of_fifths_position,
    classify_direction,
    pc_from_name,
    pitch_name,
    semitone_interval,
)


# ---------------------------------------------------------------------------
# pitch_name / pc_from_name
# ---------------------------------------------------------------------------

class TestPitchNameConversions:
    """Round-trip and lookup tests for pitch class ↔ name."""

    def test_pitch_name_all_twelve(self):
        """pitch_name returns correct name for pc 0–11."""
        expected = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        for pc, name in enumerate(expected):
            assert pitch_name(pc) == name

    def test_pitch_name_out_of_range(self):
        with pytest.raises(ValueError):
            pitch_name(12)
        with pytest.raises(ValueError):
            pitch_name(-1)

    def test_pc_from_name_sharps(self):
        """pc_from_name resolves all sharp names."""
        for pc, name in enumerate(PITCH_NAMES):
            assert pc_from_name(name) == pc

    def test_pc_from_name_flats(self):
        """pc_from_name resolves common flat names."""
        flats = {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10, "Cb": 11, "Fb": 4}
        for name, expected_pc in flats.items():
            assert pc_from_name(name) == expected_pc

    def test_roundtrip_name_to_pc_to_name(self):
        """For each sharp name: pc_from_name → pitch_name round-trips."""
        for name in PITCH_NAMES:
            assert pitch_name(pc_from_name(name)) == name

    def test_pc_from_name_unknown_raises(self):
        with pytest.raises(ValueError):
            pc_from_name("X")
        with pytest.raises(ValueError):
            pc_from_name("Z#")


# ---------------------------------------------------------------------------
# semitone_interval
# ---------------------------------------------------------------------------

class TestSemitoneInterval:
    """Tests for the signed shortest-path semitone interval."""

    def test_unison(self):
        assert semitone_interval(0, 0) == 0

    def test_minor_second_up(self):
        assert semitone_interval(0, 1) == 1

    def test_minor_second_down(self):
        assert semitone_interval(1, 0) == -1

    def test_perfect_fifth_up(self):
        # 0→7 is 7 semitones up; shortest path is -5 (7-12)
        assert semitone_interval(0, 7) == -5

    def test_tritone(self):
        assert semitone_interval(0, 6) == 6  # exact half, no wrap

    def test_major_seventh_down(self):
        """C to D: shortest is +2, not -10."""
        assert semitone_interval(0, 2) == 2


# ---------------------------------------------------------------------------
# classify_direction
# ---------------------------------------------------------------------------

class TestClassifyDirection:
    def test_no_motion(self):
        assert classify_direction(0, 0) == TransitionDirection.NO_MOTION

    def test_dominant_up_fifth(self):
        assert classify_direction(0, 7) == TransitionDirection.DOMINANT

    def test_subdominant_up_fourth(self):
        assert classify_direction(0, 5) == TransitionDirection.SUBDOMINANT

    def test_tritone(self):
        assert classify_direction(0, 6) == TransitionDirection.TRITONE

    def test_step(self):
        assert classify_direction(0, 2) == TransitionDirection.STEP

    def test_mediant_third(self):
        assert classify_direction(0, 4) == TransitionDirection.MEDIANT


# ---------------------------------------------------------------------------
# circle_of_fifths_position
# ---------------------------------------------------------------------------

class TestCircleOfFifths:
    def test_c_is_zero(self):
        assert circle_of_fifths_position(0) == 0

    def test_g_is_one(self):
        assert circle_of_fifths_position(7) == 1

    def test_f_is_eleven(self):
        assert circle_of_fifths_position(5) == 11

    def test_all_twelve_unique(self):
        positions = [circle_of_fifths_position(pc) for pc in range(12)]
        assert sorted(positions) == list(range(12))


# ---------------------------------------------------------------------------
# TonalGraph
# ---------------------------------------------------------------------------

class TestTonalGraph:
    def test_construction_empty(self):
        g = TonalGraph()
        assert "edges=0" in repr(g)
        assert g.out_degree(0) == 0

    def test_add_transition(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        assert g.out_degree(0) == 1
        assert g.in_degree(7) == 1
        assert g.weight(0, 7) == 1.0

    def test_add_transition_accumulates_weight(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        g.add_transition(0, 7, weight=2.0)
        assert g.weight(0, 7) == 3.0
        # Should NOT duplicate the edge in adjacency
        assert g.out_degree(0) == 1

    def test_add_transition_invalid_pc(self):
        g = TonalGraph()
        with pytest.raises(ValueError):
            g.add_transition(0, 12)
        with pytest.raises(ValueError):
            g.add_transition(-1, 0)

    def test_build_from_progression(self):
        g = TonalGraph()
        g.build_from_progression([0, 5, 7, 0])  # I-IV-V-I
        assert g.out_degree(0) == 1  # 0→5
        assert g.out_degree(5) == 1  # 5→7
        assert g.out_degree(7) == 1  # 7→0
        assert g.get_edge(0, 5) is not None
        assert g.get_edge(7, 0) is not None

    def test_transition_probability(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        g.add_transition(0, 5)
        assert g.transition_probability(0, 7) == pytest.approx(0.5)
        assert g.transition_probability(0, 5) == pytest.approx(0.5)

    def test_adjacency_matrix_shape(self):
        g = TonalGraph()
        g.build_from_progression([0, 5, 7, 0])
        mat = g.adjacency_matrix()
        assert len(mat) == 12
        assert all(len(row) == 12 for row in mat)

    def test_neighbors(self):
        g = TonalGraph()
        g.build_from_progression([0, 5, 7, 0, 5])
        assert sorted(g.neighbors(0)) == [5]
        assert sorted(g.neighbors(5)) == [7]

    def test_normalized_weight(self):
        g = TonalGraph()
        g.build_from_progression([0, 5, 7, 0])  # 3 transitions
        assert g.normalized_weight(0, 5) == pytest.approx(1.0 / 3.0)
        assert g.normalized_weight(5, 7) == pytest.approx(1.0 / 3.0)

    def test_get_direction_classifies(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        assert g.get_direction(0, 7) == TransitionDirection.DOMINANT

    def test_get_direction_absent_edge_uses_classifier(self):
        g = TonalGraph()
        # No edge added, should still classify
        assert g.get_direction(0, 7) == TransitionDirection.DOMINANT
