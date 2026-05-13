# Pass8 packaging policy

Pass8 separates project artifacts into five classes:

1. `core` / blueprint-aligned v36.6 objects.
2. `materialized` / full-chain full-data output needed for offline chain runs.
3. `external_modules` / read-only external definition/readout modules.
4. `test_operability` / query scripts, health tables, deploy checks, demos.
5. `advisory` / engineering suggestions such as native-write contracts and directness-debt indexes.

The goal of this phase is full-chain full-data operation, not online life runtime and not validation-only packaging.

Pass7 writer-upgrade tables are retained as advisory only. They are not v36.6 blueprint core.
