# Sub-two-minute demo script

Use a fresh terminal at the repository root. Do not display private keys or unreleased user data.

1. Show the three small files in `examples/data/` (15 seconds).
2. Run `PYTHONPATH=src python -m tableproof check --config examples/tableproof.toml` (20 seconds).
3. Point out the observed 1:N relationship, left/right orphan warnings, four predicted sizes, and successful result verification (30 seconds).
4. Change a disposable copy of `merged.tsv` from `S003` to `S999`, rerun against the disposable config, and show that row count remains four while the key multiset fails (35 seconds).
5. Show that examples are hashed and source files were not modified (15 seconds).

Record at readable terminal dimensions, add captions, remove local absolute paths if present, and publish the exact commit hash used. Keep the GIF/video as evidence, not as a claim of independent adoption.
