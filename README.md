# hybrid-quantum-maxcut

A minimal, reproducible implementation of Max-Cut solvers using both classical brute-force and quantum QAOA approaches. This project focuses on educational clarity and reproducibility, with no claims about quantum advantage.

## How to run

```bash
python classical/maxcut_bruteforce.py
python analysis/verify_ising_mapping.py
python quantum/qaoa_simulator.py
python quantum/qaoa_simulator.py --single
```

## Expected behavior

The classical optimum for this 4-node graph is cut=4. The single-run QAOA simulator (with gamma=1.0, beta=0.5) concentrates probability on the optimal bitstrings 0110 and 1001, which both achieve the maximum cut value.

## Running on real quantum hardware (AWS Braket)

This repo includes `python quantum/qaoa_hardware.py` for QPU execution on Amazon Braket. The script requires IAM permissions including `braket:SearchDevices`, `braket:GetDevice`, `braket:CreateQuantumTask`, and `braket:GetQuantumTask`, as well as an S3 destination bucket configured for Braket results. Results will vary due to hardware noise, device availability, queue times, and calibration drift.
