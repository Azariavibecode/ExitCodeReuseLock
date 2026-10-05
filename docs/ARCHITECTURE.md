# Architecture and invariants

## Proof obligation

Claim: one exact candidate documentation revision preserves the operational meaning of one numeric CLI exit code relative to the active documentation revision.

Falsifiers include a different trigger, different retry class, different operator response, wrong repository/revision/path/blob, missing unique marker, or an ambiguous comparison.

Sufficient evidence is the authenticated baseline blob and candidate blob. A candidate changelog at the exact candidate commit is additionally required before `BREAKING_DISCLOSED` can be accepted. A changelog cannot override semantic differences or produce a compatibility authorization.

## State topology

```text
Namespace(head revision 0, baseline source)
  ├─ Release A(PROPOSED) → EVALUATED/VERIFIED_EQUIVALENT → ACTIVATED
  └─ Release B(PROPOSED) → BLOCKED
                           or EVALUATED → STALE_PARENT at activation
```

The namespace stores one active source and monotonically increasing head revision. A release seals the exact baseline source visible when proposed, the candidate source, optional changelog and parent commit. These fields cannot be edited.

## Positive gate

`VERIFIED_EQUIVALENT` is valid only when all are exact booleans and true:

1. `same_condition`
2. `same_operator_action`
3. `same_retry_semantics`

The bounded vocabulary and object IDs are schema-checked after every validator independently authenticates and reads the documents. Malformed or internally inconsistent model output becomes `INCONCLUSIVE`.

## Consequence

Only an `EVALUATED + VERIFIED_EQUIVALENT` release can call the activation path. Activation uses a compare-and-swap check over `parent_commit`, updates the namespace head exactly once, increments `head_revision`, and marks the release terminal. A semantic verdict therefore controls an actual downstream state transition.

## Authority boundary

The GitHub repository is authoritative only for its own committed documentation. The contract does not infer runtime behavior from Markdown. Candidate and changelog sources must stay inside the baseline owner/repository; the candidate documentation path must remain exact; and a changelog must share the candidate commit.

## Liveness

There is no deadline or privileged finalizer. Anyone may evaluate a proposed release or activate a compatible evaluated release. Source outage safely blocks the specific proposal without changing the namespace head. A new candidate can still be proposed at a different commit.

