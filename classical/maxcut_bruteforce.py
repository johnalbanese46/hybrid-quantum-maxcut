"""
Brute-force Max-Cut solver for a 4-node graph.
Finds the partition that maximizes the number of edges crossing the cut.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.graph import N_NODES, EDGES

def count_cut_size(partition, edges):
    """
    Count the number of edges that cross the cut.
    An edge crosses the cut if its endpoints are in different partitions.
    """
    cut_size = 0
    for u, v in edges:
        if partition[u] != partition[v]:
            cut_size += 1
    return cut_size

# Brute-force all 2^n possible partitions
max_cut_value = 0
best_partition = None

# Iterate through all possible 0/1 assignments
for i in range(2 ** N_NODES):
    # Convert integer to binary tuple of length n
    partition = tuple((i >> j) & 1 for j in range(N_NODES))
    
    # Calculate cut size for this partition
    cut_size = count_cut_size(partition, EDGES)
    
    # Update best solution if this is better
    if cut_size > max_cut_value:
        max_cut_value = cut_size
        best_partition = partition

# Print results
print(f"Max-Cut value: {max_cut_value}")
print(f"Partition: {best_partition}")

