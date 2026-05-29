"""Tests for holonomy_harmony.flow — CurvatureFlow on harmonic manifolds."""

from __future__ import annotations

import pytest

from holonomy_harmony.tonal_graph import TonalGraph
from holonomy_harmony.flow import (
    CurvatureEdge,
    CurvatureFlow,
    CurvatureMeasure,
    CurvatureSnapshot,
    FlowState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _graph_from_roots(roots: list[int]) -> TonalGraph:
    g = TonalGraph()
    g.build_from_progression(roots)
    return g


# ---------------------------------------------------------------------------
# CurvatureFlow initialization
# ---------------------------------------------------------------------------

class TestCurvatureFlowInit:

    def test_invalid_dt_raises(self):
        g = TonalGraph()
        with pytest.raises(ValueError, match="dt must be positive"):
            CurvatureFlow(g, dt=-0.1)

    def test_zero_dt_raises(self):
        g = TonalGraph()
        with pytest.raises(ValueError, match="dt must be positive"):
            CurvatureFlow(g, dt=0)

    def test_initialize_creates_state(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g)
        state = flow.initialize()
        assert isinstance(state, FlowState)
        assert state.step == 0
        assert not state.converged
        assert len(state.weights) > 0

    def test_initialize_records_snapshot(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g)
        flow.initialize()
        assert flow.state is not None
        assert len(flow.state.history) == 1


# ---------------------------------------------------------------------------
# Single step
# ---------------------------------------------------------------------------

class TestCurvatureFlowStep:

    def test_step_advances(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g, dt=0.05)
        flow.initialize()
        snap = flow.step()
        assert isinstance(snap, CurvatureSnapshot)
        assert snap.step == 1

    def test_weights_remain_positive(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g, dt=0.1)
        flow.initialize()
        for _ in range(20):
            flow.step()
        for w in flow.state.weights.values():
            assert w > 0

    def test_step_records_history(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g)
        flow.initialize()
        flow.step()
        flow.step()
        assert len(flow.state.history) == 3  # init + 2 steps


# ---------------------------------------------------------------------------
# Running the flow
# ---------------------------------------------------------------------------

class TestCurvatureFlowRun:

    def test_run_returns_state(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g, dt=0.1)
        state = flow.run(max_steps=10)
        assert isinstance(state, FlowState)
        assert state.step > 0

    def test_run_respects_max_steps(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g, dt=0.1)
        state = flow.run(max_steps=5)
        assert state.step <= 5

    def test_convergence_flag(self):
        """With many steps and high tolerance, flow should converge or hit max."""
        g = _graph_from_roots([0, 7, 0])
        flow = CurvatureFlow(g, dt=0.3)
        state = flow.run(max_steps=200, convergence_tol=0.5)
        # Either converged or hit max steps
        assert state.step <= 200


# ---------------------------------------------------------------------------
# Curvature measures
# ---------------------------------------------------------------------------

class TestCurvatureMeasures:

    def test_combinatorial_measure(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g, curvature_measure=CurvatureMeasure.COMBINATORIAL)
        flow.initialize()
        snap = flow.step()
        assert isinstance(snap, CurvatureSnapshot)

    def test_harmonic_measure(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g, curvature_measure=CurvatureMeasure.HARMONIC)
        flow.initialize()
        snap = flow.step()
        assert isinstance(snap, CurvatureSnapshot)

    def test_ricci_measure(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g, curvature_measure=CurvatureMeasure.RICCI)
        flow.initialize()
        snap = flow.step()
        assert isinstance(snap, CurvatureSnapshot)

    def test_different_measures_different_curvature(self):
        """Different measures should generally produce different curvature values."""
        g = _graph_from_roots([0, 7, 2, 0])

        results = {}
        for measure in CurvatureMeasure:
            flow = CurvatureFlow(g, curvature_measure=measure)
            flow.initialize()
            kappa = flow.curvature_at(0, 7)
            results[measure] = kappa

        # At least two should differ
        values = list(results.values())
        assert len(set(round(v, 6) for v in values)) >= 2


# ---------------------------------------------------------------------------
# CurvatureSnapshot
# ---------------------------------------------------------------------------

class TestCurvatureSnapshot:

    def test_is_flat_high_tolerance(self):
        snap = CurvatureSnapshot(
            step=0,
            total_curvature=1.0,
            max_curvature=0.5,
            min_curvature=0.5,
            curvature_variance=0.001,
            edges=(),
        )
        assert snap.is_flat(tolerance=0.01)

    def test_not_flat_low_tolerance(self):
        snap = CurvatureSnapshot(
            step=0,
            total_curvature=5.0,
            max_curvature=3.0,
            min_curvature=0.0,
            curvature_variance=1.0,
            edges=(),
        )
        assert not snap.is_flat(tolerance=0.01)


# ---------------------------------------------------------------------------
# Query methods
# ---------------------------------------------------------------------------

class TestCurvatureFlowQueries:

    def test_total_curvature(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g)
        flow.initialize()
        tc = flow.total_curvature()
        assert isinstance(tc, float)

    def test_curvature_at_specific_edge(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g)
        flow.initialize()
        k = flow.curvature_at(0, 7)
        assert isinstance(k, float)

    def test_curvature_at_missing_edge(self):
        g = _graph_from_roots([0, 7])
        flow = CurvatureFlow(g)
        flow.initialize()
        k = flow.curvature_at(5, 9)
        assert k == 0.0

    def test_most_tense_transitions(self):
        g = _graph_from_roots([0, 7, 6, 0])  # includes tritone 7->6
        flow = CurvatureFlow(g)
        flow.initialize()
        tense = flow.most_tense_transitions(n=3)
        assert len(tense) <= 3
        assert all(isinstance(e, CurvatureEdge) for e in tense)
        # Should be sorted descending by curvature
        for i in range(len(tense) - 1):
            assert tense[i].curvature >= tense[i + 1].curvature

    def test_most_tense_before_init(self):
        g = TonalGraph()
        flow = CurvatureFlow(g)
        assert flow.most_tense_transitions() == []

    def test_state_before_init(self):
        g = TonalGraph()
        flow = CurvatureFlow(g)
        assert flow.state is None


# ---------------------------------------------------------------------------
# FlowState
# ---------------------------------------------------------------------------

class TestFlowState:

    def test_state_fields(self):
        g = _graph_from_roots([0, 7, 2, 0])
        flow = CurvatureFlow(g)
        state = flow.run(max_steps=3)
        assert state.step > 0
        assert isinstance(state.converged, bool)
        assert isinstance(state.history, list)
        assert len(state.weights) > 0


# ---------------------------------------------------------------------------
# Convenience: flow_from_roots
# ---------------------------------------------------------------------------

class TestFlowFromRoots:

    def test_flow_from_roots(self):
        flow = CurvatureFlow(TonalGraph())
        state = flow.flow_from_roots([0, 5, 7, 0], max_steps=10)
        assert isinstance(state, FlowState)
        assert state.step > 0

    def test_flow_from_roots_long_progression(self):
        roots = [0, 5, 7, 0, 3, 7, 0]  # longer progression
        flow = CurvatureFlow(TonalGraph())
        state = flow.flow_from_roots(roots, max_steps=20)
        assert len(state.weights) >= 4  # at least 4 distinct transitions


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_single_chord_no_transitions(self):
        g = TonalGraph()
        flow = CurvatureFlow(g)
        flow.initialize()
        assert len(flow.state.weights) == 0

    def test_repeated_chord(self):
        g = _graph_from_roots([0, 0, 0])
        flow = CurvatureFlow(g)
        flow.initialize()
        # NO_MOTION edges should have zero curvature bonus
        snap = flow.step()
        assert isinstance(snap, CurvatureSnapshot)

    def test_all_12_pitch_classes(self):
        roots = list(range(12)) + [0]
        g = _graph_from_roots(roots)
        flow = CurvatureFlow(g, dt=0.05)
        state = flow.run(max_steps=5)
        assert len(state.weights) == 12  # 12 transitions
