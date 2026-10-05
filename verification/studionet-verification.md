# StudioNet live verification

Run completed on 2026-10-05 against StudioNet chain `61999`.

- Contract: [`0xe4A2325AFBb21C7159eB63421640D07Cec71AF10`](https://explorer-studio.genlayer.com/address/0xe4A2325AFBb21C7159eB63421640D07Cec71AF10)
- Auxiliary wallet A: `0x67A1A08Fc4cf7D05c859d0d3D8398a3A30B1677e`
- Auxiliary wallet B: `0x7C87B10a3d43F3b3551414401F8b26B9F662bAB5`
- The deployment wallet performed no business action in this run.
- Full machine-readable inputs, readbacks and links: [`studionet-e2e.json`](studionet-e2e.json)

Every transaction below reached `FINALIZED` with `MAJORITY_AGREE` before its authoritative contract readback was checked.

## Outcomes

| Scenario | Authoritative outcome |
|---|---|
| Equivalent semantic revision | `VERIFIED_EQUIVALENT`, then `ACTIVATED` |
| Undisclosed exit-code reassignment | `CONFLICT_UNDISCLOSED`, `BLOCKED` |
| Authenticated disclosed break | `BREAKING_DISCLOSED`, `BLOCKED` |
| Wrong SHA-256 commitment | `SOURCE_UNVERIFIED`, `BLOCKED` |
| Competing equivalent release after head advance | `STALE_PARENT`; head and counters unchanged |
| Evaluation and activation replay | rejected; namespace, release and counters unchanged |

Final counters: one namespace, five proposals, one activation and three blocked releases. The authoritative namespace head is the equivalent commit `cdb1280d9b896112d80a5938caf8614412c6d652`, revision `1`.

## Transaction evidence

| Step | Transaction |
|---|---|
| Create namespace | [`0x3890…455e`](https://explorer-studio.genlayer.com/transactions/0x3890cefe773532b8086dc1c042dcc71c36af9d2973bdc1864e83b524ceed455e) |
| Propose equivalent | [`0x7e83…917b`](https://explorer-studio.genlayer.com/transactions/0x7e83df6f2ed6ef78fa7018f875415aac35b620250d43502101c1ae3d72c8917b) |
| Propose competing equivalent | [`0x1e65…ec72`](https://explorer-studio.genlayer.com/transactions/0x1e6548d8dc372d7492e01c23aab469a3a8d56b5889c6467dc5bcfde5cee1ec72) |
| Propose conflict | [`0x2a0b…3626`](https://explorer-studio.genlayer.com/transactions/0x2a0b6c67b9bfb5a5000e4040a767f2b4e0d03eea43c4cf822f8ed515bd2b3626) |
| Evaluate conflict | [`0xf836…4874`](https://explorer-studio.genlayer.com/transactions/0xf83602c010ead8c08c79345f2eb68c0acfaf5c8ccb63e7d8aff94c2482f64874) |
| Reject conflict activation | [`0x91c1…a225`](https://explorer-studio.genlayer.com/transactions/0x91c1faf65414c6071ce30a686721b00930365f2177cc9b1e7439d657c40fa225) |
| Evaluate equivalent | [`0xf6e6…f2a6`](https://explorer-studio.genlayer.com/transactions/0xf6e6f544e678f445437f569638a16e8259a106dbab0d090402f9dbd8527ff2a6) |
| Evaluate competing equivalent | [`0xed06…64d0`](https://explorer-studio.genlayer.com/transactions/0xed06bf62ef2d3a1e6dfe0b1aa2458a79ad93e0db20cc0f487ed530c0fab864d0) |
| Activate equivalent | [`0xb60b…cec8`](https://explorer-studio.genlayer.com/transactions/0xb60bd1efebb4e75a6f36e6c2551090bc97df4d53bdcccc46730f4959ee13cec8) |
| Reject stale parent | [`0x1f2f…07ce`](https://explorer-studio.genlayer.com/transactions/0x1f2f498f3c3b3a9dfcbdb1c8cfa743663be26916075661796ee21c06a8d207ce) |
| Propose disclosed break | [`0x3c82…6204`](https://explorer-studio.genlayer.com/transactions/0x3c821f9d9a79b9833e5986d74c804022f7f3dba592af5dfd9c92c7caf4676204) |
| Evaluate disclosed break | [`0xb8a6…a120`](https://explorer-studio.genlayer.com/transactions/0xb8a657dd4045f5f1137d86c038db3bc4887604131d02922965bbee4b36b1a120) |
| Reject breaking activation | [`0x131b…7105`](https://explorer-studio.genlayer.com/transactions/0x131be1a0f485159cf30391363abca3beec0c2eef0ac3ae7f53d10c2ccf627105) |
| Propose poisoned digest | [`0x46d0…7d54`](https://explorer-studio.genlayer.com/transactions/0x46d031e2bfa001e22e915353be9722ba6e9643a530f9a4739fecff7ab97d7d54) |
| Evaluate poisoned digest | [`0xd008…d5d4`](https://explorer-studio.genlayer.com/transactions/0xd0085edb97fe2fe84d3eaa88fe41640d9c543ac1fa8e05dde94888128fe4d5d4) |
| Reject evaluation replay | [`0x46f2…3068`](https://explorer-studio.genlayer.com/transactions/0x46f2fac7b8c6356ef3dfd7644a0068acc7b09593e0911095ab1456c17c593068) |
| Reject activation replay | [`0x78a8…5dba`](https://explorer-studio.genlayer.com/transactions/0x78a8f0096be611fd431f3bbd86f7e0642bbcf95d53ad150f86c116134cd25dba) |

## Evidence boundary

The GitHub fixtures are explicitly synthetic. This run demonstrates source authentication, bounded semantic consensus, fail-closed transitions, compare-and-swap activation and replay resistance. It does not claim that a real CLI binary implements the documented behavior.
