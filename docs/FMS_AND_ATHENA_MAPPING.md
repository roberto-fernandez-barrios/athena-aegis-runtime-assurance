# ATHENA/HSaaS/FMS mapping

## Implemented service path

The local `HSaaSOrchestrator` models:

client request -> HSaaS orchestration -> classical preparation -> quantum
request -> execution-context capture -> QPU/result -> assurance decision ->
enforcement/recovery -> returned or withheld service result.

This maps to ATHENA WP3's AEGIS responsibilities for secure/reliable hybrid
design, the transpilation/scheduling/post-processing boundary, QPU execution
evidence, integrity controls, end-to-end V&V, metrics, threat assessment, and
enforcement. It also provides an integration seam for WP5.

## AEGIS slice of the FMS demonstrator

The routing skeleton is a small, deterministic, single-vehicle closed-route
problem. Its exact brute-force oracle establishes route validity, optimal cost,
service correctness, quality degradation, and classical fallback correctness.
The quantum handoff declares a one-hot-position QUBO identity, variable count,
and objective digest. A physical QAOA circuit is intentionally not frozen until
the pilot establishes backend width, depth, shot cost, and runtime feasibility.

It represents the AEGIS decision/evidence/recovery slice around a routing
request. It does not represent multi-vehicle constraints, production data,
FMS nodes S1/S2/E2 in deployment, consortium orchestration, commercial
provider selection, or the globally integrated WP5 demonstrator. Those require
consortium coordination; no paper claim will silently substitute this proxy.

The kernel workload remains first priority because it connects directly to
Paper 1.5. If QPU quota is scarce, the campaign closes one causal chain on that
workload before a full QAOA arm is authorized.
