"""Tests for holonomy_harmony.topology — TopologyAnalyzer and invariants."""

from __future__ import annotations

import pytest

from holonomy_harmony.tonal_graph import TonalGraph
from holonomy_harmony.topology import (
    BettiNumbers,
    FundamentalGroupPresentation,
    HomologyGroup,
    SimplicialComplex,
    TopologicalInvariants,
    TopologyAnalyzer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _graph_from_roots(roots: list[int]) -> TonalGraph:
    g = TonalGraph()
    g.build_from_progression(roots)
    return g


# ---------------------------------------------------------------------------
# SimplicialComplex
# ---------------------------------------------------------------------------

class TestSimplicialComplex:

    def test_empty_complex(self):
        g = TonalGraph()
        ta = TopologyAnalyzer(g)
        sc = ta.build_complex()
        assert len(sc.vertices) == 0
        assert len(sc.edges) == 0
        assert len(sc.triangles) == 0

    def test_single_edge(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        ta = TopologyAnalyzer(g)
        sc = ta.build_complex()
        assert sc.vertices == frozenset({0, 7})
        assert (0, 7) in sc.edges
        assert len(sc.edges) == 1

    def test_euler_single_edge(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        ta = TopologyAnalyzer(g)
        sc = ta.build_complex()
        # V=2, E=1, T=0 => χ=1
        assert sc.euler_characteristic() == 1

    def test_triangle_detected(self):
        # C(0) -> G(7) -> D(2) -> C(0) should form a triangle
        g = TonalGraph()
        g.add_transition(0, 7)
        g.add_transition(7, 2)
        g.add_transition(2, 0)
        ta = TopologyAnalyzer(g)
        sc = ta.build_complex()
        assert len(sc.triangles) == 1
        assert (0, 2, 7) in sc.triangles

    def test_no_triangle_without_closure(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        g.add_transition(7, 2)
        # No edge from 2 back to 0
        ta = TopologyAnalyzer(g)
        sc = ta.build_complex()
        assert len(sc.triangles) == 0


# ---------------------------------------------------------------------------
# BettiNumbers
# ---------------------------------------------------------------------------

class TestBettiNumbers:

    def test_euler_from_betti(self):
        b = BettiNumbers(beta_0=1, beta_1=2, beta_2=0)
        assert b.euler_from_betti() == -1

    def test_euler_contractible(self):
        b = BettiNumbers(beta_0=1, beta_1=0, beta_2=0)
        assert b.euler_from_betti() == 1

    def test_single_edge_betti(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        ta = TopologyAnalyzer(g)
        betti = ta.compute_betti()
        assert betti.beta_0 == 1  # connected
        assert betti.beta_1 == 0  # single edge, no cycle

    def test_cycle_creates_betti1(self):
        # Unfilled cycle: square without diagonal (4 vertices, 4 edges, 0 triangles)
        g = TonalGraph()
        g.add_transition(0, 7)
        g.add_transition(7, 2)
        g.add_transition(2, 9)
        g.add_transition(9, 0)
        ta = TopologyAnalyzer(g)
        betti = ta.compute_betti()
        assert betti.beta_0 == 1
        assert betti.beta_1 >= 1  # unfilled cycle = 1-cycle

    def test_disconnected_graph(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        g.add_transition(2, 9)  # disconnected component
        ta = TopologyAnalyzer(g)
        betti = ta.compute_betti()
        assert betti.beta_0 == 2  # two components


# ---------------------------------------------------------------------------
# Connected components
# ---------------------------------------------------------------------------

class TestConnectedComponents:

    def test_fully_connected(self):
        roots = [0, 7, 2, 9, 4, 0]
        g = _graph_from_roots(roots)
        ta = TopologyAnalyzer(g)
        comps = ta.compute_connected_components()
        assert len(comps) == 1

    def test_two_components(self):
        g = TonalGraph()
        g.add_transition(0, 2)
        g.add_transition(5, 7)
        ta = TopologyAnalyzer(g)
        comps = ta.compute_connected_components()
        assert len(comps) == 2

    def test_isolated_vertices_not_in_graph(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        ta = TopologyAnalyzer(g)
        sc = ta.build_complex()
        assert 11 not in sc.vertices  # B is isolated, not in graph


# ---------------------------------------------------------------------------
# Fundamental group
# ---------------------------------------------------------------------------

class TestFundamentalGroup:

    def test_trivial_no_edges(self):
        g = TonalGraph()
        ta = TopologyAnalyzer(g)
        pi1 = ta.compute_fundamental_group()
        assert pi1.is_trivial

    def test_single_edge_trivial(self):
        g = TonalGraph()
        g.add_transition(0, 7)
        ta = TopologyAnalyzer(g)
        pi1 = ta.compute_fundamental_group()
        assert pi1.is_trivial  # no cycle => trivial π₁

    def test_cycle_gives_generators(self):
        # Unfilled cycle (no triangle)
        g = TonalGraph()
        g.add_transition(0, 7)
        g.add_transition(7, 2)
        g.add_transition(2, 9)
        g.add_transition(9, 0)
        ta = TopologyAnalyzer(g)
        pi1 = ta.compute_fundamental_group()
        assert pi1.rank() >= 1

    def test_rank_method(self):
        pi1 = FundamentalGroupPresentation(
            generators=("a", "b"),
            relations=(),
            is_trivial=False,
        )
        assert pi1.rank() == 2


# ---------------------------------------------------------------------------
# HomologyGroup
# ---------------------------------------------------------------------------

class TestHomologyGroup:

    def test_trivial_group(self):
        h = HomologyGroup(rank=0)
        assert h.is_trivial
        assert h.order == 1

    def test_z_group(self):
        h = HomologyGroup(rank=1)
        assert not h.is_trivial
        assert h.order is None  # infinite

    def test_torsion_group(self):
        h = HomologyGroup(rank=0, torsion={2: 1})
        assert not h.is_trivial
        assert h.order == 2

    def test_repr(self):
        assert repr(HomologyGroup(rank=0)) == "0"
        assert repr(HomologyGroup(rank=2)) == "Z^2"
        assert "Z/2Z" in repr(HomologyGroup(rank=0, torsion={2: 1}))


# ---------------------------------------------------------------------------
# TopologyAnalyzer integration
# ---------------------------------------------------------------------------

class TestTopologyAnalyzer:

    def test_analyze_progression_i_iv_v_i(self):
        roots = [0, 5, 7, 0]  # I IV V I in C
        ta = TopologyAnalyzer()
        result = ta.analyze_progression(roots)
        assert isinstance(result, TopologicalInvariants)
        assert result.euler_characteristic is not None
        assert result.betti.beta_0 == 1  # connected

    def test_analyze_from_graph(self):
        g = TonalGraph()
        for roots in [[0, 7, 2, 9, 4, 11, 0]]:
            g.build_from_progression(roots)
        ta = TopologyAnalyzer(g)
        inv = ta.analyze()
        assert inv.betti.beta_0 >= 1

    def test_summary_not_empty(self):
        roots = [0, 5, 7, 0]
        ta = TopologyAnalyzer()
        inv = ta.analyze_progression(roots)
        summary = inv.summary()
        assert "Euler" in summary
        assert "Betti" in summary

    def test_build_complex_from_roots(self):
        roots = [0, 7, 2, 0]
        ta = TopologyAnalyzer()
        sc = ta.build_complex_from_roots(roots)
        assert len(sc.vertices) >= 3
        assert len(sc.edges) >= 3

    def test_euler_consistent_with_betti(self):
        """χ = β_0 - β_1 + β_2"""
        roots = [0, 7, 2, 0, 5, 0]
        ta = TopologyAnalyzer()
        inv = ta.analyze_progression(roots)
        expected = inv.betti.beta_0 - inv.betti.beta_1 + inv.betti.beta_2
        assert inv.euler_characteristic == expected

    def test_genus_nonnegative(self):
        roots = [0, 7, 2, 9, 4, 0]
        ta = TopologyAnalyzer()
        inv = ta.analyze_progression(roots)
        assert inv.genus >= 0

    def test_homology_groups_match_betti(self):
        roots = [0, 5, 7, 0]
        ta = TopologyAnalyzer()
        inv = ta.analyze_progression(roots)
        assert inv.homology_0.rank == inv.betti.beta_0
        assert inv.homology_1.rank == inv.betti.beta_1
        assert inv.homology_2.rank == inv.betti.beta_2
