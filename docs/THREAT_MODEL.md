# Threat model

## Protected assets

- exact active source of each exit-code namespace;
- monotonic namespace head revision;
- immutable candidate evidence identity;
- distinction between compatible, disclosed breaking and undisclosed conflicting semantics;
- counters and terminal release state.

## Adversaries and controls

### Locator or digest substitution

The contract resolves the GitHub commit object and canonical tree, requires one exact path, recomputes Git blob SHA-1 and SHA-256 over fetched bytes, and rejects truncated trees, missing blobs and size mismatches.

### Cross-project evidence

Candidate and changelog owner/repository must equal the namespace authority. Candidate path must equal the active documentation path. Changelog commit must equal the candidate commit.

### Prompt injection

Fetched documents are labeled untrusted evidence. Output IDs, keys, types, enum values and verdict implications are validated deterministically. A document cannot select a different namespace/release or bypass the three-part positive gate.

### False compatibility

Compatibility requires all semantic predicates true. Any false, unknown, malformed, fetch error or consensus disagreement cannot activate the candidate.

### Changelog laundering

An authenticated changelog may support `BREAKING_DISCLOSED`; that state is still blocked from compatible activation. It never converts a breaking change into equivalence.

### Race and replay

Each release binds the current parent commit. Activation compares it again to the live head. Duplicate namespace/parent/candidate proposals are rejected. Terminal evaluation and activation are not repeatable.

### Deployer influence

The deployer address is never stored and has no special method. All business paths are permissionless.

## Explicit non-claims

- no claim that binaries implement the documented behavior;
- no CI, package registry, runtime or deployment attestation;
- no claim that synthetic fixture statements are real-world facts;
- no continuous monitoring or time-window guarantee.

