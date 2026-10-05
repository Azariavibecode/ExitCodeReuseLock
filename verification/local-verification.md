# Local verification plan

Run `python -m pytest -q` from the repository root.

The direct-mode suite covers:

- equivalent candidate evaluation and exact head activation;
- undisclosed semantic conflict;
- authenticated disclosed breaking change that remains non-activatable;
- bad digest, missing source, truncated tree and incorrect blob identity;
- prompt injection and wrong release identity;
- internally inconsistent positive output;
- stale-parent concurrent proposals with full no-mutation comparison;
- duplicate proposal, terminal evaluation replay and activation replay;
- repository authority, marker and unknown-ID guards;
- deployment by one wallet followed by business actions from another wallet;
- static runtime header, storage, source-authentication and anti-clone checks.

Direct mocks prove deterministic transition logic and validator-output validation. They do not prove live GitHub availability, StudioNet consensus, finality or deployed-source parity. Those require a later, separately recorded StudioNet run.

