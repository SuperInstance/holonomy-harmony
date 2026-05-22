"""Tests for holonomy_harmony.analyzer."""

import pytest

from holonomy_harmony.analyzer import (
    Chord,
    PROGRESSIONS,
    analyze_progression,
    detect_modulations,
    parse_roman,
    score_stability,
)


# ---------------------------------------------------------------------------
# parse_roman — standard numerals
# ---------------------------------------------------------------------------

class TestParseRomanStandard:
    def test_i(self):
        c = parse_roman("I")
        assert c.root == 0
        assert c.quality == "maj"
        assert c.is_diatonic is True

    def test_ii(self):
        c = parse_roman("ii")
        assert c.root == 2
        assert c.quality == "min"

    def test_iii(self):
        c = parse_roman("iii")
        assert c.root == 4

    def test_iv(self):
        c = parse_roman("IV")
        assert c.root == 5

    def test_v(self):
        c = parse_roman("V")
        assert c.root == 7
        assert c.quality == "maj"

    def test_vi(self):
        c = parse_roman("vi")
        assert c.root == 9

    def test_vii(self):
        c = parse_roman("vii")
        assert c.root == 11
        assert c.quality == "dim"

    def test_key_g_major(self):
        """In G major, I should be root G=7."""
        c = parse_roman("I", key_tonic=7)
        assert c.root == 7

    def test_minor_mode(self):
        """In C minor, i should be C=0, quality min."""
        c = parse_roman("i", mode="minor")
        assert c.root == 0
        assert c.quality == "min"


# ---------------------------------------------------------------------------
# parse_roman — accidentals
# ---------------------------------------------------------------------------

class TestParseRomanAccidentals:
    def test_biii(self):
        c = parse_roman("bIII")
        # degree 2 (III), major scale pc for degree 2 is 4, flat → 3
        assert c.root == 3
        assert c.is_diatonic is False

    def test_bvi(self):
        c = parse_roman("bVI")
        # degree 5 (VI), pc 9, flat → 8
        assert c.root == 8

    def test_bvii(self):
        c = parse_roman("bVII")
        # degree 6 (VII), pc 11, flat → 10
        assert c.root == 10


# ---------------------------------------------------------------------------
# parse_roman — qualities
# ---------------------------------------------------------------------------

class TestParseRomanQualities:
    def test_seventh(self):
        c = parse_roman("V7")
        assert c.quality == "7"

    def test_maj7(self):
        c = parse_roman("Imaj7")
        assert c.quality == "maj7"

    def test_m7(self):
        c = parse_roman("viim7")
        assert c.quality == "m7"

    def test_dim(self):
        c = parse_roman("viidim")
        assert c.quality == "dim"

    def test_aug(self):
        c = parse_roman("I+")
        assert c.quality == "aug"

    def test_sus4(self):
        c = parse_roman("Vsus4")
        assert c.quality == "sus4"

    def test_dim7(self):
        c = parse_roman("viidim7")
        assert c.quality == "dim7"


# ---------------------------------------------------------------------------
# parse_roman — secondary dominants
# ---------------------------------------------------------------------------

class TestParseRomanSecondaryDominants:
    def test_v_over_vi(self):
        c = parse_roman("V/vi")
        # vi root in C is 9 (A), V of A-major is E=4
        assert c.root == 4
        assert c.is_secondary_dominant is True
        assert c.is_diatonic is False

    def test_v7_over_iv(self):
        c = parse_roman("V7/IV")
        # IV root in C is 5 (F), V of F is C=0
        assert c.root == 0
        assert c.is_secondary_dominant is True
        assert c.quality == "7"


# ---------------------------------------------------------------------------
# analyze_progression — famous progressions
# ---------------------------------------------------------------------------

class TestAnalyzeProgression:
    def test_axis_progression(self):
        sym = PROGRESSIONS["axis_progression"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        assert len(analysis.chords) == 4
        # I-V-vi-IV in C: roots should be 0, 7, 9, 5
        assert [c.root for c in analysis.chords] == [0, 7, 9, 5]

    def test_blues_12_bar(self):
        sym = PROGRESSIONS["blues_12_bar"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        assert len(analysis.chords) == 12
        # All diatonic
        assert all(c.is_diatonic for c in analysis.chords)

    def test_pachelbel_canon(self):
        sym = PROGRESSIONS["pachelbel_canon"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        assert len(analysis.chords) == 8

    def test_giant_steps(self):
        sym = PROGRESSIONS["giant_steps"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        # Giant steps should have some non-diatonic chords
        non_diatonic = [c for c in analysis.chords if not c.is_diatonic]
        assert len(non_diatonic) > 0

    def test_plagal_cadence(self):
        sym = PROGRESSIONS["plagal_cadence"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        assert len(analysis.chords) == 2
        assert analysis.chords[0].function == "IV"
        assert analysis.chords[1].function == "I"

    def test_perfect_cadence(self):
        sym = PROGRESSIONS["perfect_cadence"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        assert len(analysis.chords) == 2

    def test_deceptive_cadence(self):
        sym = PROGRESSIONS["deceptive_cadence"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        assert analysis.chords[0].function == "V"
        assert analysis.chords[1].function == "vi"

    def test_wrap_flag(self):
        sym = PROGRESSIONS["axis_progression"]
        a1 = analyze_progression(sym[0], sym[1], sym[2], wrap=False)
        a2 = analyze_progression(sym[0], sym[1], sym[2], wrap=True)
        # Wrapped has one extra step in holonomy
        assert len(a2.holonomy.steps) == len(a1.holonomy.steps) + 1


# ---------------------------------------------------------------------------
# detect_modulations
# ---------------------------------------------------------------------------

class TestDetectModulations:
    def test_secondary_dominant_detected(self):
        """Progression with V/vi should detect a modulation."""
        analysis = analyze_progression(["I", "V/vi", "vi", "IV"])
        mods = detect_modulations(analysis)
        assert len(mods) >= 1
        assert mods[0][0] == 1  # index 1

    def test_diatonic_no_modulations(self):
        """Pure diatonic progression should have no modulations."""
        analysis = analyze_progression(["I", "IV", "V", "I"])
        mods = detect_modulations(analysis)
        assert len(mods) == 0


# ---------------------------------------------------------------------------
# score_stability
# ---------------------------------------------------------------------------

class TestScoreStability:
    def test_diatonic_high_stability(self):
        """Pure diatonic should score > 0.8."""
        analysis = analyze_progression(["I", "IV", "V", "I"])
        s = score_stability(analysis)
        assert s > 0.8

    def test_chromatic_low_stability(self):
        """Highly chromatic progression should score < 0.5."""
        # Giant steps is very chromatic
        sym = PROGRESSIONS["giant_steps"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        s = score_stability(analysis)
        assert s < 0.5

    def test_stability_in_range(self):
        """Stability score should always be 0.0–1.0."""
        for name, (symbols, tonic, mode) in PROGRESSIONS.items():
            analysis = analyze_progression(symbols, tonic, mode)
            s = score_stability(analysis)
            assert 0.0 <= s <= 1.0, f"{name}: stability {s} out of range"

    def test_minor_progression(self):
        """Minor key progression should also produce valid stability."""
        sym = PROGRESSIONS["andulusian_cadence"]
        analysis = analyze_progression(sym[0], sym[1], sym[2])
        s = score_stability(analysis)
        assert 0.0 <= s <= 1.0


# ---------------------------------------------------------------------------
# Chord dataclass
# ---------------------------------------------------------------------------

class TestChordDataclass:
    def test_root_name(self):
        c = parse_roman("V")
        assert c.root_name == "G"

    def test_key_name(self):
        c = parse_roman("V", key_tonic=7)  # G major
        assert c.key_name == "G major"

    def test_repr(self):
        c = parse_roman("V")
        r = repr(c)
        assert "Chord" in r
        assert "G" in r


# ---------------------------------------------------------------------------
# All PROGRESSIONS parse without error
# ---------------------------------------------------------------------------

class TestProgressionsFixture:
    def test_all_progressions_parse(self):
        """Every entry in PROGRESSIONS should parse and analyze without error."""
        for name, (symbols, tonic, mode) in PROGRESSIONS.items():
            analysis = analyze_progression(symbols, tonic, mode)
            assert len(analysis.chords) == len(symbols), f"{name}: chord count mismatch"

    def test_all_progressions_holonomy_computed(self):
        for name, (symbols, tonic, mode) in PROGRESSIONS.items():
            analysis = analyze_progression(symbols, tonic, mode)
            assert analysis.holonomy is not None
            assert analysis.graph is not None
