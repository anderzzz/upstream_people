# Precomputed Data

Generated data files used by the API server. These are gitignored because
they're large and reproducible.

## Files

- `starting_hand_table.json` (~15MB) — equity and classification for all 270,725 PLO starting hands vs 1-5 opponents.

## Regenerating

From the project root:

```bash
PYTHONPATH=. python scripts/precompute_starting_hands.py --samples 50000 --resume
```

Use `--limit 100` for a quick test run. Use `--resume` to continue from a checkpoint if interrupted.
