"""
Max-Cut to Ising Hamiltonian Mapping

The Max-Cut problem seeks to partition the nodes of a graph into two sets such that
the number of edges crossing between the two sets is maximized.

This problem maps naturally to an Ising Hamiltonian. In the standard mapping:
- Each node i is assigned a spin variable Z_i ∈ {-1, +1} (Pauli Z operator)
- An edge (i,j) contributes to the cut if Z_i ≠ Z_j (different partitions)
- The cut size is: Σ_(i,j ∈ edges) (1 - Z_i Z_j) / 2

The Ising Hamiltonian is:
    H = Σ_(i,j ∈ edges) (1 - Z_i Z_j) / 2

Expanding this gives:
    H = (|E|/2) - (1/2) Σ_(i,j ∈ edges) Z_i Z_j

Since the constant term doesn't affect optimization, minimizing the Ising energy
corresponds to minimizing -Σ Z_i Z_j, which occurs when Z_i and Z_j have opposite
signs (different partitions), thus maximizing the cut.

This file defines the problem Hamiltonian only (no quantum circuits or execution).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.graph import N_NODES, EDGES


def maxcut_ising_terms():
    """
    Compute the Ising Hamiltonian terms for the Max-Cut problem.
    
    Returns:
        h: dict mapping node index → local field coefficient
        J: dict mapping (i, j) edge tuples → coupling coefficient
    
    The Hamiltonian is: H = Σ_i h[i] * Z_i + Σ_(i,j) J[(i,j)] * Z_i * Z_j
    
    For Max-Cut, we use the form: H = Σ_(i,j ∈ edges) (1 - Z_i Z_j) / 2
    which expands to: H = constant - (1/2) Σ_(i,j ∈ edges) Z_i * Z_j
    
    To minimize this (and maximize cut), we set:
    - h[i] = 0 for all nodes (no local fields)
    - J[(i,j)] = -1/2 for each edge (i,j)
    
    The negative sign ensures that when Z_i and Z_j have opposite signs
    (different partitions), the energy contribution is negative (favorable).
    """
    # Local fields: zero for standard Max-Cut (no bias toward any partition)
    h = {i: 0.0 for i in range(N_NODES)}
    
    # Coupling coefficients: -1/2 for each edge
    # The negative sign means opposite spins (different partitions) lower energy
    # The 1/2 factor comes from the standard Max-Cut Ising form
    J = {}
    for edge in EDGES:
        i, j = edge
        # Store in canonical order (i < j) for consistency
        if i < j:
            J[(i, j)] = -0.5
        else:
            J[(j, i)] = -0.5
    
    return h, J


# Example: what h and J look like for this graph
# h = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
# J = {(0, 1): -0.5, (0, 2): -0.5, (1, 3): -0.5, (2, 3): -0.5}
#
# This means the Hamiltonian is:
# H = -0.5 * (Z_0*Z_1 + Z_0*Z_2 + Z_1*Z_3 + Z_2*Z_3) + constant
#
# To minimize H, we want Z_i * Z_j = -1 for as many edges as possible,
# which corresponds to maximizing the number of edges crossing the cut.

