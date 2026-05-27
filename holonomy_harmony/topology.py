"""
TopologyAnalyzer — compute topological invariants of harmonic spaces.

Models the space of tonal relations as a topological space and computes
invariants such as Euler characteristic, Betti numbers, fundamental group
presentation, and homology groups from the TonalGraph structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .tonal_graph import TonalGraph, PITCH_CLASSES, Edge


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SimplicialComplex:
    """
    A simplicial complex built from tonal transitions.

    0-simplices: pitch classes (vertices)
    1-simplices: directed edges (ordered pairs)
    2-simplices: triangles — three pitch classes that form a closed
                  cycle of mutual transitions
    """
    vertices: FrozenSet[int]
    edges: FrozenSet[Tuple[int, int]]
    triangles: FrozenSet[Tuple[int, int, int]]

    def euler_characteristic(self) -> int:
        """χ = V - E + F (vertices - edges + faces)."""
        return len(self.vertices) - len(self.edges) + len(self.triangles)


@dataclass(frozen=True, slots=True)
class BettiNumbers:
    """
    Betti numbers β_k of the harmonic space.

    β_0: number of connected components
    β_1: number of independent 1-cycles (holes / loops)
    β_2: number of enclosed 2-dimensional cavities
    """
    beta_0: int
    beta_1: int
    beta_2: int

    def euler_from_betti(self) -> int:
        """Compute Euler characteristic from Betti numbers: χ = β_0 - β_1 + β_2."""
        return self.beta_0 - self.beta_1 + self.beta_2


@dataclass(frozen=True, slots=True)
class FundamentalGroupPresentation:
    """
    A presentation of the fundamental group π_1 of the harmonic space.

    Generators correspond to independent loops; relations encode how
    loops compose or cancel.
    """
    generators: Tuple[str, ...]
    relations: Tuple[str, ...]
    is_trivial: bool

    def rank(self) -> int:
        """Minimum number of generators (free rank)."""
        return len(self.generators)


@dataclass(frozen=True, slots=True)
class HomologyGroup:
    """
    A finitely-generated homology group H_k.

    Represented as Z^rank ⊕ torsion where torsion is a dict of
    {order: count} (e.g. {2: 1} means one copy of Z/2Z).
    """
    rank: int
    torsion: Dict[int, int] = field(default_factory=dict)

    @property
    def is_trivial(self) -> bool:
        return self.rank == 0 and not self.torsion

    @property
    def order(self) -> Optional[int]:
        """Finite order if trivial free part, else None (infinite group)."""
        if self.rank > 0:
            return None
        result = 1
        for p, n in self.torsion.items():
            result *= p ** n
        return result if result > 1 else 1

    def __repr__(self) -> str:
        parts = []
        if self.rank > 0:
            parts.append(f"Z^{self.rank}")
        for p, n in sorted(self.torsion.items()):
            for _ in range(n):
                parts.append(f"Z/{p}Z")
        if not parts:
            return "0"
        return " ⊕ ".join(parts)


@dataclass(frozen=True, slots=True)
class TopologicalInvariants:
    """Complete set of topological invariants for a harmonic space."""
    simplicial_complex: SimplicialComplex
    euler_characteristic: int
    betti: BettiNumbers
    fundamental_group: FundamentalGroupPresentation
    homology_0: HomologyGroup
    homology_1: HomologyGroup
    homology_2: HomologyGroup
    genus: int  # (β_1) / 2 for orientable surfaces; here a generalized notion

    def summary(self) -> str:
        lines = [
            f"Euler characteristic: χ = {self.euler_characteristic}",
            f"Betti numbers: β₀={self.betti.beta_0}  β₁={self.betti.beta_1}  β₂={self.betti.beta_2}",
            f"H₀ = {self.homology_0}",
            f"H₁ = {self.homology_1}",
            f"H₂ = {self.homology_2}",
            f"π₁ rank = {self.fundamental_group.rank()}  trivial={self.fundamental_group.is_trivial}",
            f"Genus: {self.genus}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# TopologyAnalyzer
# ---------------------------------------------------------------------------

class TopologyAnalyzer:
    """
    Compute topological invariants of harmonic spaces defined by a
    TonalGraph or a raw sequence of chord roots.

    The harmonic space is modeled as a simplicial complex:
      - 0-simplices = pitch classes that appear
      - 1-simplices = pairs connected by a transition
      - 2-simplices = triples forming closed 3-cycles

    From this complex we compute the Euler characteristic, Betti numbers,
    fundamental group presentation, and homology groups.
    """

    def __init__(self, graph: Optional[TonalGraph] = None) -> None:
        self._graph = graph or TonalGraph()

    # -- building the complex -----------------------------------------------

    def build_complex(self) -> SimplicialComplex:
        """Build a simplicial complex from the tonal graph."""
        vertices: Set[int] = set()
        edge_set: Set[Tuple[int, int]] = set()

        # Extract edges from graph adjacency
        adj: Dict[int, Set[int]] = {pc: set() for pc in PITCH_CLASSES}
        for i in PITCH_CLASSES:
            for j in self._graph.neighbors(i):
                vertices.add(i)
                vertices.add(j)
                edge_set.add((i, j))
                adj[i].add(j)

        # Find 2-simplices (triangles): three vertices with mutual transitions
        triangle_set: Set[Tuple[int, int, int]] = set()
        vertex_list = sorted(vertices)
        for idx_a in range(len(vertex_list)):
            for idx_b in range(idx_a + 1, len(vertex_list)):
                a, b = vertex_list[idx_a], vertex_list[idx_b]
                if b not in adj[a] and a not in adj[b]:
                    continue
                for idx_c in range(idx_b + 1, len(vertex_list)):
                    c = vertex_list[idx_c]
                    # Check all three edges exist (in either direction)
                    ab = b in adj[a] or a in adj[b]
                    ac = c in adj[a] or a in adj[c]
                    bc = c in adj[b] or b in adj[c]
                    if ab and ac and bc:
                        triangle_set.add((a, b, c))

        return SimplicialComplex(
            vertices=frozenset(vertices),
            edges=frozenset(edge_set),
            triangles=frozenset(triangle_set),
        )

    def build_complex_from_roots(self, roots: List[int]) -> SimplicialComplex:
        """Build a simplicial complex from a chord-root progression."""
        graph = TonalGraph()
        graph.build_from_progression(roots)
        analyzer = TopologyAnalyzer(graph)
        return analyzer.build_complex()

    # -- invariants ---------------------------------------------------------

    def compute_euler(self, complex_: Optional[SimplicialComplex] = None) -> int:
        """Compute the Euler characteristic of the harmonic space."""
        sc = complex_ or self.build_complex()
        return sc.euler_characteristic()

    def compute_connected_components(self, complex_: Optional[SimplicialComplex] = None) -> List[Set[int]]:
        """Find connected components via BFS on the undirected version of the graph."""
        sc = complex_ or self.build_complex()

        # Build undirected adjacency from edges
        adj: Dict[int, Set[int]] = {v: set() for v in sc.vertices}
        for a, b in sc.edges:
            adj[a].add(b)
            adj[b].add(a)
        for v in sc.vertices:
            adj.setdefault(v, set())

        visited: Set[int] = set()
        components: List[Set[int]] = []

        for v in sc.vertices:
            if v in visited:
                continue
            component: Set[int] = set()
            queue = [v]
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbor in adj.get(node, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)

        return components

    def compute_betti(self, complex_: Optional[SimplicialComplex] = None) -> BettiNumbers:
        """
        Compute Betti numbers.

        β_0 = number of connected components
        β_1 = rank of cycle space = E - V + β_0
        β_2 = number of independent 2-cycles = χ_adj = T - (E choose 2 subset count)
              Simplified: β_2 = max(0, T - free_faces) where free_faces = E - V + β_0 bound by triangles
        """
        sc = complex_ or self.build_complex()
        components = self.compute_connected_components(sc)
        beta_0 = len(components)

        V = len(sc.vertices)
        E = len(sc.edges)
        T = len(sc.triangles)

        # Euler characteristic: χ = V - E + T
        # And χ = β_0 - β_1 + β_2
        # So β_1 = β_0 - χ + β_2
        #
        # For a 2-complex, β_2 is the dimension of ker(∂_2) / im(∂_3) ≈ dim(ker(∂_2)).
        # A triangle is a 2-cycle if its three boundary edges all exist.
        # If there are no triangles, β_2 = 0.
        # With triangles: each triangle whose boundary is already in the 1-skeleton
        # may or may not contribute to β_2 depending on whether it's a "bounding cycle".
        # Simplified: treat triangles as 2-simplices; β_2 = max(0, T - rank_of_boundary_map_2)
        # The boundary map ∂_2: C_2 → C_1 has rank ≤ E.
        # For correctness, compute β_1 from Euler directly when β_2 is known.
        if T == 0:
            beta_2 = 0
            # No triangles: β_1 = E - V + β_0 (cycle rank formula)
            beta_1 = max(0, E - V + beta_0)
        else:
            # Assume all triangles are non-degenerate 2-simplices.
            # β_2 = T - (number of linearly dependent triangles in ∂_2)
            # Heuristic: independent triangles = max(0, T - (E - V + β_0)) if T > cycle_rank
            cycle_rank = max(0, E - V + beta_0)
            if T > cycle_rank:
                beta_2 = T - cycle_rank
            else:
                beta_2 = 0
            # Now β_1 from Euler: β_1 = β_0 - (V - E + T) + β_2
            euler = V - E + T
            beta_1 = max(0, beta_0 - euler + beta_2)

        return BettiNumbers(beta_0=beta_0, beta_1=beta_1, beta_2=beta_2)

    def compute_fundamental_group(
        self, complex_: Optional[SimplicialComplex] = None
    ) -> FundamentalGroupPresentation:
        """
        Compute a presentation of π_1.

        Generators = independent loops (one per cycle in the 1-skeleton).
        Relations = triangles (each triangle makes its boundary trivial).
        """
        sc = complex_ or self.build_complex()
        betti = self.compute_betti(sc)

        if betti.beta_0 != 1 or betti.beta_1 == 0:
            return FundamentalGroupPresentation(
                generators=(),
                relations=(),
                is_trivial=(betti.beta_1 == 0),
            )

        # Generators: g_0, g_1, ..., g_{β_1 - 1}
        generators = tuple(f"g_{i}" for i in range(betti.beta_1))

        # Relations from triangles: each triangle gives "product of boundary edges = 1"
        relations: List[str] = []
        for a, b, c in sc.triangles:
            relations.append(f"⟨{a},{b},{c}⟩ = 1")

        # Additional relation from holonomy closure (if applicable)
        is_trivial = betti.beta_1 == 0 or (
            len(generators) <= len(relations) and len(relations) > 0
        )

        return FundamentalGroupPresentation(
            generators=generators,
            relations=tuple(relations),
            is_trivial=is_trivial,
        )

    def compute_homology(
        self, complex_: Optional[SimplicialComplex] = None
    ) -> Tuple[HomologyGroup, HomologyGroup, HomologyGroup]:
        """
        Compute homology groups H_0, H_1, H_2.

        H_0 ≅ Z^{β_0}
        H_1 ≅ Z^{β_1} (no torsion in this 2-dimensional complex)
        H_2 ≅ Z^{β_2}
        """
        sc = complex_ or self.build_complex()
        betti = self.compute_betti(sc)

        h0 = HomologyGroup(rank=betti.beta_0)
        h1 = HomologyGroup(rank=betti.beta_1)
        h2 = HomologyGroup(rank=betti.beta_2)

        return h0, h1, h2

    def analyze(self, complex_: Optional[SimplicialComplex] = None) -> TopologicalInvariants:
        """Compute all topological invariants at once."""
        sc = complex_ or self.build_complex()
        euler = self.compute_euler(sc)
        betti = self.compute_betti(sc)
        pi1 = self.compute_fundamental_group(sc)
        h0, h1, h2 = self.compute_homology(sc)
        genus = betti.beta_1 // 2 if betti.beta_1 % 2 == 0 else (betti.beta_1 - 1) // 2

        return TopologicalInvariants(
            simplicial_complex=sc,
            euler_characteristic=euler,
            betti=betti,
            fundamental_group=pi1,
            homology_0=h0,
            homology_1=h1,
            homology_2=h2,
            genus=genus,
        )

    def analyze_progression(self, roots: List[int]) -> TopologicalInvariants:
        """Convenience: build complex from roots and analyze."""
        sc = self.build_complex_from_roots(roots)
        return self.analyze(sc)
