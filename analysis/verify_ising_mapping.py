"""
Verify that the Max-Cut to Ising mapping is correct.

This script enumerates all possible assignments and verifies that:
- Maximizing cut size corresponds to minimizing Ising energy
- The optimal assignments match (allowing for global bit-flip symmetry)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.graph import N_NODES, EDGES
from quantum.ising_mapping import maxcut_ising_terms


def cut_size(assignment):
    """
    Compute the cut size for a given assignment.
    
    Args:
        assignment: tuple of 0/1 values, length N_NODES
    
    Returns:
        Number of edges crossing the cut (edges where endpoints differ)
    """
    size = 0
    for u, v in EDGES:
        if assignment[u] != assignment[v]:
            size += 1
    return size


def ising_energy(assignment, h, J):
    """
    Compute the Ising energy for a given assignment.
    
    Args:
        assignment: tuple of 0/1 values, length N_NODES
        h: dict of local field coefficients
        J: dict of coupling coefficients
    
    Returns:
        Ising energy value
    
    Spin mapping: 0 → +1, 1 → -1
    This means nodes with assignment 0 are in partition +1,
    and nodes with assignment 1 are in partition -1.
    """
    # Convert 0/1 to +1/-1 spins
    spins = [1 if bit == 0 else -1 for bit in assignment]
    
    # Local field terms
    energy = sum(h[i] * spins[i] for i in range(N_NODES))
    
    # Coupling terms
    for (i, j), coeff in J.items():
        energy += coeff * spins[i] * spins[j]
    
    return energy


# Get Ising terms
h, J = maxcut_ising_terms()

# Enumerate all assignments and compute metrics
all_cuts = {}
all_energies = {}

for i in range(2 ** N_NODES):
    assignment = tuple((i >> j) & 1 for j in range(N_NODES))
    cut = cut_size(assignment)
    energy = ising_energy(assignment, h, J)
    
    all_cuts[assignment] = cut
    all_energies[assignment] = energy

# Find maximum cut and minimum energy
max_cut = max(all_cuts.values())
min_energy = min(all_energies.values())

# Find assignments achieving these values
max_cut_assignments = [a for a, c in all_cuts.items() if c == max_cut]
min_energy_assignments = [a for a, e in all_energies.items() if e == min_energy]

# Print results
print(f"Maximum cut value: {max_cut}")
print(f"Minimum energy: {min_energy}")
print(f"\nAssignments achieving max cut (showing up to 4):")
for a in max_cut_assignments[:4]:
    print(f"  {a}")
print(f"\nAssignments achieving min energy (showing up to 4):")
for a in min_energy_assignments[:4]:
    print(f"  {a}")

# Check if sets match (allowing for bit-flip symmetry)
# Two assignments are equivalent if one is the bit-flip of the other
def bit_flip(assignment):
    """Flip all bits: 0→1, 1→0"""
    return tuple(1 - bit for bit in assignment)

# Normalize sets by taking the lexicographically smaller of each assignment and its flip
def normalize_set(assignments):
    """Normalize a set of assignments by taking min(assignment, bit_flip(assignment))"""
    normalized = set()
    for a in assignments:
        flipped = bit_flip(a)
        normalized.add(min(a, flipped))
    return normalized

max_cut_normalized = normalize_set(max_cut_assignments)
min_energy_normalized = normalize_set(min_energy_assignments)

match = max_cut_normalized == min_energy_normalized
print(f"\nArgmax-cut set equals argmin-energy set (up to bit-flip symmetry): {match}")

