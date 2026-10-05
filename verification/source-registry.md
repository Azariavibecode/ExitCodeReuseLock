# Registered synthetic test sources

These local fixtures are synthetic and exist only to exercise the proof topology. Before StudioNet testing, publish the same paths in a public evidence repository and replace the placeholder commit/digest records in the live runbook with exact immutable values.

| Logical revision | Registered path | Expected semantic result |
|---|---|---|
| baseline | `fixtures/baseline/exit-codes.md` | active meaning: authentication rejection |
| equivalent | `fixtures/equivalent/exit-codes.md` | `VERIFIED_EQUIVALENT` |
| conflict | `fixtures/conflict/exit-codes.md` | `CONFLICT_UNDISCLOSED` |
| disclosed | `fixtures/disclosed/exit-codes.md` + `CHANGELOG.md` | `BREAKING_DISCLOSED` |
| injection | `fixtures/injection/exit-codes.md` | adversarial conflict; never compatible |

For live evidence record all of:

- public GitHub owner/repository;
- full 40-hex commit;
- canonical path;
- SHA-256 recomputed from the fetched bytes;
- transaction hash, consensus/finality and authoritative readback;
- pre/post namespace and counter state for every rejected path.

