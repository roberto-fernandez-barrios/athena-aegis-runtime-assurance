# Retrospective specification for the v5 revision

Written on 2026-11-09 before executing the new numerical analyses. This document is a retrospective specification requested by the responsible author; it is not a prospective preregistration. Initial schema inspection established that local count histograms, matrices, scores, references and event timestamps survive. The historical protocols, thresholds, sample and outputs remain immutable.

## Inputs and denominators

Read only the local Campaign B campaign state, fourteen candidate window records, unit records, reference files and policy records, the canonical final analysis and closure supplement, the frozen workload/oracle/endpoint code, and relevant historical environment/protocol records. Export a minimal whitelist of numerical data, local experimental identifiers, context comparison digests and timestamps. Exclude authentication material, provider job/account identifiers and private paths. Preserve source-file hashes and distinguish this filtered export from originals.

The confirmatory set remains the ten historically usable transitions, with six pre-recovery physical probes each (60 probes). Analyze the six held probes in each incomplete C05/C09 transition separately when inputs are present (12 additional probes); never add them to the confirmatory denominator. Bootstrap C01/C02 and all available accepted verification records remain visible. No extra physical observations, threshold choices or inferential subgroups are introduced.

## Numerical reconstruction

Reconstruct each available 3-by-3 physical kernel from six upper-triangle count histograms, using the all-zero count divided by total counts and symmetric placement. Rebuild the exact two-qubit ZZ feature-map reference from the frozen feature vectors and two repetitions, documenting the independent implementation and comparison with the historical reference. Recalculate relative Frobenius error, maximum absolute error, and the frozen conjunction of relative <=0.15 and maximum absolute <=0.20 (historical tolerance 1e-12). Unknown/missing counts, binding fields or oracle results stay explicit and fail closed for eligibility. Do not infer missing measurements from reported decisions.

For every complete reference, join its 39 unit identifiers to reconstructed unit scores. Recompute p=(1+number of calibration scores >= test score)/(39+1), accepting strictly above alpha=0.05. Reconstruct P2 from the selected preceding complete reference and P5 from the new reference, including the recorded fallback admissibility and context evidence. Retain incomplete reference distributions separately; never promote them to complete references. Check each reconstructed result against its original stored counterpart, reporting every discrepancy with tolerances (matrix 1e-12, score 1e-12, clocks 1e-5 seconds). Expected values supplied by the author are comparison controls, not computation inputs.

## Direct comparator and temporal scope

The comparator keeps the same physical probe and requires physical-result evidence, successful available binding checks, consistent recorded context projections, and absolute oracle correctness. It does not require a newly calibrated reference or silently return the classical matrix. Report ACCEPT_PHYSICAL, REJECT or UNKNOWN and reasons. Re-evaluate checkable timestamp ordering and digest equality; distinguish recorded J2/J3/J4 assertions from independently authenticated binding. No private HMAC or provider re-query is performed.

Determine the earliest *recorded upper bound* on availability of counts, oracle and binding from sealed-unit/envelope creation and local HOLD/policy events, checked against the frozen runner's order of operations. Later-obtained information must not be credited to an earlier decision. An offline calculable acceptance is not an observed deployed service, measured latency or valid no-queue counterfactual. Compare properties, not contract-specific definitions: lack of renewal does not itself make the direct comparator inferior. Report structural absence of 39 new calibration jobs per completed transition, without inventing monetary, energy or timing savings.

## Outputs

1. Per-probe reconstruction, comparator decision, P2/P5 rank values, delta defined as p_new minus p_old, and changed decision identities. Joint decision counts for the 60 usable probes; a separate C05/C09 ledger. Describe min, maximum, median, arithmetic mean and population standard deviation of ranks/deltas and errors, without new significance tests or distribution-equivalence claims.
2. Old-reference ages at window opening (the historic selection anchor), first HOLD, and each probe HOLD where known, measured from the old reference ready_at. New-reference elapsed construction times are distinct. Complete 39-score distributions and incomplete distributions are exported.
3. Relative/absolute error margins to the unchanged thresholds; all physically correct results rejected/substituted by a rank policy. Four rejections are not validation of 5% conformal coverage; dependence and exchangeability remain unestablished.
4. Fourteen-candidate operational flow, bootstrap roles, twelve held-result transitions, ten complete usable transitions, primary success count, and retained-only success count. Reconstruct T0--T3 and all endpoint predicates from the exported evidence, preserving the original selection and source rules. Deadline is assessed, not retrospectively enforced as a serving block.
5. Independently calculate the exact binomial upper-tail p-value and Clopper--Pearson intervals from reconstructed successes. Report design power P[Binomial(10, pi)>=9] for pi=0.5,0.6,0.7,0.8,0.9,0.95 under independent homogeneous trials. This is design sensitivity, not a diagnosis of why the observed result occurred. No sample expansion or prospective alternative is performed.
6. A synthetic software case of 39 scores at 0.30 and test score 0.20 demonstrates rank acceptance with failure of the absolute relative-error threshold. It is not a Campaign B observation.
7. Separate minimal KC-B4 correction and regression tests: retain original analyzer bytes; add KC-B4 to fatal declaration blockers in the new version. Compare original/corrected behavior on synthetic passing-primary records plus a verification error, and on an accepted non-usable window error; verify the actual B verdict remains unchanged. The patch was not run during acquisition and does not establish general production correctness.

An offline command will validate manifests, execute these computations and meaningful tests, regenerate tables/figures, compare canonical outputs, and emit machine-readable plus readable reports. Numerical reproduction, hash integrity, HMAC authentication, provider reconciliation and independent temporal anchoring are reported separately.


## Clarification following substantive review, 2026-11-10

The ordering stated above is the local revision record, without independent timestamp attestation. The comparator treats known failed predicates as REJECT even when other fields are absent; otherwise missing required inputs remain UNKNOWN. Tests cover missing timestamps, context and integrity as well as known absent execution. Endpoint reconstruction is conditional on the inherited usable-window set, recorded clocks and held-result/invariant/rerun flags; it does not re-execute the full stratum-support guard or historical acquisition state machine. This clarification does not alter the original denominators, thresholds or physical records.
