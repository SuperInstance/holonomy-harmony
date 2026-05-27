"""
CurvatureFlow — Ricci flow on harmonic manifolds.

Implements discrete Ricci flow on the TonalGraph where edge weights
represent curvature. The flow smooths tonal tension by redistributing
weight along edges, converging toward a uniform-curvature (harmonically
stable) state.

This models how harmonic tension resolves over time: high-curvature
regions (dominant chords, tritone transitions) shed weight while
low-curvature regions (tonic resolutions) absorb it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from .tonal_graph import TonalGraph, PITCH_CLASSES, TransitionDirection, classify_direction


# ---------------------------------------------------------------------------
# Curvature measures
# ---------------------------------------------------------------------------

class CurvatureMeasure(Enum):
    """Types of discrete curvature on edges."""
    COMBINATORIAL = auto()   # Based purely on degree
    HARMONIC = auto()        # Weighted by tonal function (dominant = high curvature)
    RICCI = auto()           # Ricci curvature (Ollivier's definition via transport distance)


@dataclass(frozen=True, slots=True)
class CurvatureEdge:
    """Curvature value on a single edge."""
    source: int
    target: int
    direction: TransitionDirection
    curvature: float
    weight: float


@dataclass(frozen=True, slots=True)
class CurvatureSnapshot:
    """A snapshot of curvature state at a flow step."""
    step: int
    total_curvature: float
    max_curvature: float
    min_curvature: float
    curvature_variance: float
    edges: Tuple[CurvatureEdge, ...]

    def is_flat(self, tolerance: float = 0.01) -> bool:
        """True if all curvatures are within tolerance of uniform."""
        return self.curvature_variance < tolerance


# ---------------------------------------------------------------------------
# Flow state
# ---------------------------------------------------------------------------

@dataclass
class FlowState:
    """Mutable state of the Ricci flow."""
    weights: Dict[Tuple[int, int], float]
    step: int = 0
    converged: bool = False
    history: List[CurvatureSnapshot] = field(default_factory=list)


# ---------------------------------------------------------------------------
# CurvatureFlow
# ---------------------------------------------------------------------------

class CurvatureFlow:
    """
    Discrete Ricci flow on a TonalGraph.

    The flow evolves edge weights so that curvature becomes uniform.
    High-curvature edges (dominant, tritone) lose weight; low-curvature
    edges (tonic, resolution) gain weight. This models the natural
    tendency of harmony toward resolution.

    Parameters
    ----------
    graph : TonalGraph
        The tonal graph to flow on.
    dt : float
        Time step for the flow. Smaller = more stable but slower.
    curvature_measure : CurvatureMeasure
        Which curvature definition to use.
    """

    # Tonal curvature bonus: how much each transition type contributes to curvature
    _TONAL_CURVATURE: Dict[TransitionDirection, float] = {
        TransitionDirection.DOMINANT: 2.0,      # V→I creates strong tension
        TransitionDirection.RESOLUTION: -1.5,    # Resolution releases tension
        TransitionDirection.TRITONE: 3.0,        # Maximum tension
        TransitionDirection.MEDIANT: 1.0,        # Moderate color change
        TransitionDirection.SUBDOMINANT: 0.5,    # Mild preparation
        TransitionDirection.STEP: 0.3,           # Smooth
        TransitionDirection.NO_MOTION: 0.0,      # No curvature
        TransitionDirection.UNKNOWN: 0.5,
    }

    def __init__(
        self,
        graph: TonalGraph,
        dt: float = 0.1,
        curvature_measure: CurvatureMeasure = CurvatureMeasure.HARMONIC,
    ) -> None:
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")
        self._graph = graph
        self._dt = dt
        self._measure = curvature_measure
        self._state: Optional[FlowState] = None

    # -- curvature computation ----------------------------------------------

    def _combinatorial_curvature(self, src: int, tgt: int, weight: float) -> float:
        """
        Combinatorial curvature: κ(e) = 1/d_s + 1/d_t - weight.
        Where d_s, d_t are degrees of source and target vertices.
        """
        d_s = max(1, self._graph.out_degree(src) + self._graph.in_degree(src))
        d_t = max(1, self._graph.out_degree(tgt) + self._graph.in_degree(tgt))
        return 1.0 / d_s + 1.0 / d_t - weight

    def _harmonic_curvature(self, src: int, tgt: int, weight: float) -> float:
        """
        Harmonic curvature: combinatorial + tonal bonus.
        Dominant and tritone transitions have positive curvature (tension).
        Resolutions have negative curvature (release).
        """
        base = self._combinatorial_curvature(src, tgt, weight)
        direction = self._graph.get_direction(src, tgt)
        tonal_bonus = self._TONAL_CURVATURE.get(direction, 0.5)
        return base + tonal_bonus * weight

    def _ricci_curvature(self, src: int, tgt: int, weight: float) -> float:
        """
        Simplified Ollivier-Ricci curvature.

        κ(x,y) = 1 - W_1(μ_x, μ_y)
        where μ_x is the neighbor distribution at x and W_1 is the
        Wasserstein-1 distance (approximated here).
        """
        # Build neighbor distributions
        neighbors_src = self._graph.neighbors(src)
        neighbors_tgt = self._graph.neighbors(tgt)

        if not neighbors_src or not neighbors_tgt:
            return 0.0

        # Uniform distributions over neighbors
        total_src = sum(self._graph.weight(src, n) for n in neighbors_src)
        total_tgt = sum(self._graph.weight(tgt, n) for n in neighbors_tgt)

        if total_src == 0 or total_tgt == 0:
            return 0.0

        # W_1 approximation: average shortest-path distance between neighbors
        # For pitch classes, use circle-of-fifths distance
        def _co5_dist(a: int, b: int) -> float:
            diff = abs(a - b) % 12
            return min(diff, 12 - diff) / 6.0  # normalized to [0, 1]

        # Match neighbors greedily
        dist_sum = 0.0
        count = 0
        for ns in neighbors_src:
            best_dist = 1.0
            for nt in neighbors_tgt:
                d = _co5_dist(ns, nt)
                best_dist = min(best_dist, d)
            w_s = self._graph.weight(src, ns) / total_src
            dist_sum += w_s * best_dist
            count += 1

        return 1.0 - dist_sum

    def compute_curvature(self, src: int, tgt: int, weight: float) -> float:
        """Compute curvature on an edge using the selected measure."""
        if self._measure == CurvatureMeasure.COMBINATORIAL:
            return self._combinatorial_curvature(src, tgt, weight)
        elif self._measure == CurvatureMeasure.HARMONIC:
            return self._harmonic_curvature(src, tgt, weight)
        elif self._measure == CurvatureMeasure.RICCI:
            return self._ricci_curvature(src, tgt, weight)
        return self._combinatorial_curvature(src, tgt, weight)

    # -- flow initialization ------------------------------------------------

    def initialize(self) -> FlowState:
        """Initialize flow state from the graph's current weights."""
        weights: Dict[Tuple[int, int], float] = {}
        for src in PITCH_CLASSES:
            for tgt in self._graph.neighbors(src):
                w = self._graph.weight(src, tgt)
                if w > 0:
                    weights[(src, tgt)] = w

        self._state = FlowState(weights=weights, step=0)
        self._record_snapshot()
        return self._state

    # -- flow steps ---------------------------------------------------------

    def step(self) -> CurvatureSnapshot:
        """Perform one step of the Ricci flow."""
        if self._state is None:
            self.initialize()
        assert self._state is not None

        if self._state.converged:
            return self._state.history[-1]

        # Compute curvature on every edge and update weights
        new_weights: Dict[Tuple[int, int], float] = {}
        for (src, tgt), w in self._state.weights.items():
            kappa = self.compute_curvature(src, tgt, w)
            # Ricci flow: dw/dt = -κ * w
            # Clamp kappa to prevent divergence
            kappa_clamped = max(-10.0, min(10.0, kappa))
            new_w = w - self._dt * kappa_clamped * w
            # Clamp to prevent negative or exploding weights
            new_weights[(src, tgt)] = max(1e-10, min(1e6, new_w))

        self._state.weights = new_weights
        self._state.step += 1

        # Check convergence
        self._record_snapshot()
        snapshot = self._state.history[-1]
        if snapshot.is_flat(tolerance=0.001):
            self._state.converged = True

        return snapshot

    def run(self, max_steps: int = 100, convergence_tol: float = 0.001) -> FlowState:
        """
        Run the flow until convergence or max_steps.

        Parameters
        ----------
        max_steps : int
            Maximum number of flow steps.
        convergence_tol : float
            Variance threshold for declaring convergence.

        Returns
        -------
        FlowState
            The final state of the flow.
        """
        if self._state is None:
            self.initialize()

        for _ in range(max_steps):
            if self._state is not None and self._state.converged:
                break
            snapshot = self.step()
            if snapshot.is_flat(tolerance=convergence_tol):
                if self._state is not None:
                    self._state.converged = True
                break

        return self._state  # type: ignore[return-value]

    # -- snapshot -----------------------------------------------------------

    def _record_snapshot(self) -> None:
        """Record a curvature snapshot of the current state."""
        if self._state is None:
            return

        edges: List[CurvatureEdge] = []
        curvatures: List[float] = []

        for (src, tgt), w in self._state.weights.items():
            kappa = self.compute_curvature(src, tgt, w)
            direction = self._graph.get_direction(src, tgt)
            edges.append(CurvatureEdge(
                source=src,
                target=tgt,
                direction=direction,
                curvature=kappa,
                weight=w,
            ))
            curvatures.append(kappa)

        total = sum(curvatures) if curvatures else 0.0
        max_k = max(curvatures) if curvatures else 0.0
        min_k = min(curvatures) if curvatures else 0.0
        mean = total / len(curvatures) if curvatures else 0.0
        variance = sum(min((k - mean) ** 2, 1e10) for k in curvatures) / len(curvatures) if curvatures else 0.0

        snapshot = CurvatureSnapshot(
            step=self._state.step,
            total_curvature=total,
            max_curvature=max_k,
            min_curvature=min_k,
            curvature_variance=variance,
            edges=tuple(edges),
        )
        self._state.history.append(snapshot)

    # -- queries ------------------------------------------------------------

    @property
    def state(self) -> Optional[FlowState]:
        """Current flow state, or None if not initialized."""
        return self._state

    def total_curvature(self) -> float:
        """Sum of all edge curvatures."""
        if self._state is None:
            return 0.0
        return sum(
            self.compute_curvature(src, tgt, w)
            for (src, tgt), w in self._state.weights.items()
        )

    def curvature_at(self, src: int, tgt: int) -> float:
        """Curvature on a specific edge."""
        if self._state is None:
            return 0.0
        if (src, tgt) not in self._state.weights:
            return 0.0
        w = self._state.weights[(src, tgt)]
        return self.compute_curvature(src, tgt, w)

    def most_tense_transitions(self, n: int = 5) -> List[CurvatureEdge]:
        """Return the n edges with highest curvature (most tension)."""
        if self._state is None:
            return []

        edges: List[CurvatureEdge] = []
        for (src, tgt), w in self._state.weights.items():
            kappa = self.compute_curvature(src, tgt, w)
            direction = self._graph.get_direction(src, tgt)
            edges.append(CurvatureEdge(
                source=src, target=tgt,
                direction=direction, curvature=kappa, weight=w,
            ))
        edges.sort(key=lambda e: e.curvature, reverse=True)
        return edges[:n]

    def flow_from_roots(
        self,
        roots: List[int],
        max_steps: int = 100,
        convergence_tol: float = 0.001,
    ) -> FlowState:
        """Convenience: build graph from roots and run the flow."""
        graph = TonalGraph()
        graph.build_from_progression(roots)
        flow = CurvatureFlow(graph, dt=self._dt, curvature_measure=self._measure)
        return flow.run(max_steps=max_steps, convergence_tol=convergence_tol)
