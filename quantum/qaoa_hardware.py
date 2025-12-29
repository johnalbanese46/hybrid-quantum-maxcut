"""
QAOA (Quantum Approximate Optimization Algorithm) for Max-Cut on Amazon Braket QPU.

Runs the same QAOA p=1 circuit on a real quantum hardware device (not simulator).
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from botocore.exceptions import ClientError

from braket.aws import AwsDevice
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


# Preflight permission check
print("Checking Braket permissions...")
try:
    braket_client = boto3.client("braket", region_name="us-east-1")
    braket_client.search_devices(filters=[{"name": "deviceType", "values": ["QPU"]}], maxResults=1)
except ClientError as e:
    error_code = e.response.get("Error", {}).get("Code", "")
    if error_code in ("AccessDenied", "UnauthorizedOperation"):
        print("\nError: AWS identity is valid but lacks required Braket permissions.")
        print("This script requires IAM permissions such as:")
        print("  - braket:SearchDevices")
        print("  - braket:GetDevice")
        print("  - braket:CreateQuantumTask")
        print("  - braket:GetQuantumTask")
        print("  - S3 write permissions for results")
        print("\nPlease ensure your AWS credentials have the necessary Braket permissions.")
        sys.exit(1)
    else:
        # Re-raise if it's a different error
        raise
except Exception as e:
    # Re-raise other exceptions (e.g., network issues)
    raise

print("Permissions check passed.\n")

# Fixed QAOA parameters
gamma = 1.0
beta = 0.5
p = 1
shots = 500

# Device selection: check environment variable first, otherwise use default
device_arn = os.environ.get("BRAKET_DEVICE_ARN")
if not device_arn:
    # Default to IonQ Harmony (commonly available gate-model QPU)
    device_arn = "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"

# Get the device
device = AwsDevice(device_arn)

print(f"Using device: {device_arn}")

# Build the QAOA circuit
circuit = build_qaoa_circuit(gamma, beta, p)

# Execute on hardware
task = device.run(circuit, shots=shots)
task_arn = task.id

print(f"Task ARN: {task_arn}")
print("Waiting for task to complete...")

# Wait for result
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
print("\nTop 8 bitstrings (sorted by count):")
for bitstring, count, cut_val, prob in top_8:
    print(f"  {bitstring}: count={count}, cut={cut_val}, prob={prob:.4f}")

# Print total probability on optimal cut=4 states
print(f"\nTotal probability mass on optimal cut=4 states: {optimal_probability:.4f}")


# Note on hardware variability:
# Hardware results will vary due to:
# 1. Noise: Gate errors, decoherence, and readout errors affect measurement outcomes
# 2. Queueing: Tasks may wait in queue before execution, affecting timing
# 3. Transpilation: Circuit may be transpiled differently based on device connectivity
# 4. Calibration drift: Device parameters change over time and between calibrations
# These factors mean results will differ from ideal simulation and may vary between runs.

