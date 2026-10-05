# ExitCodeReuseLock

ExitCodeReuseLock is a contract-only GenLayer registry that prevents a CLI release from being marked compatible when an existing numeric exit code silently changes operational meaning.

It authenticates immutable GitHub commit, tree, blob, raw-byte and SHA-256 evidence, then asks validators to compare the exact exit-code section across an active and candidate release. Only a fully equivalent result can advance the namespace head.

## Why GenLayer

String equality cannot reliably determine whether two differently worded descriptions have the same trigger, retry behavior and required operator action. GenLayer validators independently re-fetch the registered evidence and reach comparative consensus over those bounded semantic findings.

## Proof boundary

The contract proves consistency of publisher-controlled documentation at exact GitHub revisions. It does **not** prove that a CLI binary behaves as documented, that CI passed, or that a release was deployed. The bundled sources are explicitly synthetic test fixtures.

## Architecture

This is a semantic reservation table with compare-and-swap activation:

`namespace active source → candidate evaluation → compatible-only activation`

It is not a challenge docket, voting court, deadline workflow or version-graph clone.

- `VERIFIED_EQUIVALENT` requires all three findings to be true: same triggering condition, same operator action and same retry semantics.
- `BREAKING_DISCLOSED` records an authenticated disclosed break but cannot activate it as compatible.
- `CONFLICT_UNDISCLOSED`, `SOURCE_UNVERIFIED` and `INCONCLUSIVE` are fail-closed.
- Activation rechecks the exact parent commit. A competing candidate becomes `STALE_PARENT` after another candidate advances the head.
- Terminal evaluation and activation cannot be replayed.

There is no owner, administrator, allowlist, deployer privilege or clock dependency.

## Public methods

```text
create_namespace(project, exit_code, section_marker, baseline_source_json)
propose_release(namespace_id, candidate_source_json, changelog_source_json="")
evaluate_release(release_id)
activate_compatible_release(release_id)
get_namespace(namespace_id)
get_release(release_id)
get_counts()
```

Each source is canonical JSON with exactly:

```json
{"owner":"ORG","repo":"REPO","commit":"40_HEX","path":"/docs/exit-codes.md","digest":"64_HEX_SHA256"}
```

## Role separation

- Main wallet: deploy only.
- Auxiliary wallet A: create a namespace and propose the equivalent path.
- Auxiliary wallet B: exercise conflict, poisoned-source, stale-parent and replay paths.
- A steward can create an independent namespace with their own public GitHub evidence; no permission is required.

## Local verification

```bash
python -m pytest -q
```

Target runtime: GenLayer `0.2.16`. No frontend is included.

Live StudioNet contract: [`0xe4A2325AFBb21C7159eB63421640D07Cec71AF10`](https://explorer-studio.genlayer.com/address/0xe4A2325AFBb21C7159eB63421640D07Cec71AF10). The two-auxiliary-wallet happy, conflict, disclosed-break, poisoned-source, stale-parent and replay run is recorded in [StudioNet verification](verification/studionet-verification.md).

See [architecture](docs/ARCHITECTURE.md), [threat model](docs/THREAT_MODEL.md), [registered test sources](verification/source-registry.md) and [local verification](verification/local-verification.md).

