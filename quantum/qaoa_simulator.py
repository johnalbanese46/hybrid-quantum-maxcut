"""
QAOA (Quantum Approximate Optimization Algorithm) simulator for Max-Cut.

Uses Amazon Braket's local simulator to run QAOA with fixed parameters.
This is a minimal implementation with p=1 (single layer) for demonstration.
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from braket.devices import LocalSimulator
from braket.circuits import Circuit

from common.graph import N_NODES, EDGES


def cut_size(assignment):
    """Compute cut size for a bitstring assignment (0/1 tuple)."""
    size = 0
    for u, v in EDGES:
        if assignment[u] != assignment[v]:
            size += 1
    return size


def build_qaoa_circuit(gamma, beta, p=1):
    """
    Build a QAOA circuit for Max-Cut using the cost operator C directly.
    
    Args:
        gamma: cost parameter (rotation angle for cost operator)
        beta: mixer parameter (rotation angle for mixer Hamiltonian)
        p: number of QAOA layers (default 1)
    
    Returns:
        Circuit object
    """
    circuit = Circuit()
    
    # Initialize all qubits in |+⟩ state (superposition)
    for i in range(N_NODES):
        circuit.h(i)
    
    # Apply p layers of cost and mixer Hamiltonians
    for layer in range(p):
        # Cost operator: C = Σ_(i,j ∈ edges) (1 - Z_i Z_j) / 2
        # Cost unitary: exp(-i*gamma*C) = exp(-i*gamma*Σ(1-Z_i*Z_j)/2)
        # This expands to: exp(-i*gamma*|E|/2) * exp(i*gamma*Σ Z_i*Z_j/2)
        # The constant phase doesn't matter, so we implement exp(i*gamma*Σ Z_i*Z_j/2)
        # 
        # For each edge (i,j), exp(i*gamma*Z_i*Z_j/2) is implemented as:
        # CNOT(i,j) Rz(-gamma) on j CNOT(i,j)
        # The negative sign in Rz(-gamma) accounts for the fact that we want
        # exp(i*gamma*Z_i*Z_j/2), and the standard decomposition with CNOT
        # requires Rz(-gamma) to achieve this (the 1/2 factor is handled by the
        # CNOT decomposition, and the sign ensures correct phase accumulation).
        for i, j in EDGES:
            circuit.cnot(i, j)
            circuit.rz(j, -gamma)
            circuit.cnot(i, j)
        
        # Mixer Hamiltonian: exp(-i*beta*H_m) where H_m = Σ_i X_i
        # Implemented as X rotations on all qubits
        for i in range(N_NODES):
            circuit.rx(i, 2 * beta)
    
    # Measurement is automatic in Braket when running with shots
    
    return circuit


def run_sweep_mode():
    """Run parameter sweep mode: test all combinations of gamma and beta values."""
    # Parameter sweep values
    gamma_values = [0.5, 1.0, 1.5]
    beta_values = [0.25, 0.5, 0.75]
    p = 1
    
    # Use local simulator
    device = LocalSimulator()
    
    # Number of measurement shots
    shots = 1000
    
    # Perform parameter sweep
    for gamma in gamma_values:
        for beta in beta_values:
            # Build the QAOA circuit for this parameter pair
            circuit = build_qaoa_circuit(gamma, beta, p)
            
            # Execute the circuit
            task = device.run(circuit, shots=shots)
            result = task.result()
            
            # Get measurement counts
            measurement_counts = result.measurement_counts
            
            # Find most frequent bitstring
            most_frequent = max(measurement_counts.items(), key=lambda x: x[1])
            bitstring = most_frequent[0]
            
            # Convert bitstring to tuple of 0/1 for cut calculation
            # Braket returns bitstrings as strings like "0011" or "0 0 1 1"
            assignment = tuple(int(bit) for bit in bitstring.replace(" ", ""))
            
            # Compute cut value
            cut_val = cut_size(assignment)
            
            # Print summary line
            print(f"gamma={gamma}, beta={beta} -> best bitstring={bitstring}, cut={cut_val}")


def run_single_mode():
    """Run single-run mode: detailed analysis of one parameter pair."""
    gamma = 1.0
    beta = 0.5
    p = 1
    shots = 3000
    
    # Use local simulator
    device = LocalSimulator()
    
    # Build and execute the circuit
    circuit = build_qaoa_circuit(gamma, beta, p)
    task = device.run(circuit, shots=shots)
    result = task.result()
    
    # Get measurement counts
    measurement_counts = result.measurement_counts
    
    # Convert bitstrings to assignments and compute cut values
    bitstring_data = []
    optimal_probability = 0.0
    
    for bitstring, count in measurement_counts.items():
        # Convert bitstring to tuple of 0/1
        assignment = tuple(int(bit) for bit in bitstring.replace(" ", ""))
        cut_val = cut_size(assignment)
        probability = count / shots
        
        bitstring_data.append((bitstring, count, cut_val, probability))
        
        # Accumulate probability for optimal cut=4 states
        if cut_val == 4:
            optimal_probability += probability
    
    # Sort by count (descending) and take top 8
    bitstring_data.sort(key=lambda x: x[1], reverse=True)
    top_8 = bitstring_data[:8]
    
    # Print top 8 bitstrings
    print("Top 8 bitstrings (sorted by count):")
    for bitstring, count, cut_val, prob in top_8:
        print(f"  {bitstring}: count={count}, cut={cut_val}, prob={prob:.4f}")
    
    # Print total probability on optimal cut=4 states
    print(f"\nTotal probability mass on optimal cut=4 states: {optimal_probability:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QAOA simulator for Max-Cut")
    parser.add_argument("--single", action="store_true", 
                       help="Run single-run mode (gamma=1.0, beta=0.5, 3000 shots)")
    
    args = parser.parse_args()
    
    if args.single:
        run_single_mode()
    else:
        run_sweep_mode()


# Note on differences with real hardware:
# When running on real quantum hardware (e.g., via Braket's managed devices),
# the main differences will be:
# 1. Noise: Real devices have gate errors, decoherence, and readout errors
# 2. Connectivity: Hardware may have limited qubit connectivity, requiring SWAP gates
# 3. Calibration: Device parameters may vary and need periodic recalibration
# 4. Queue time: Hardware execution requires queuing and may take longer
# 5. Cost: Hardware runs incur charges per shot, unlike local simulation

