# Photo Map Remix UI evidence

This directory contains reproducible visual evidence for the standalone app in
`photo_map/`.

The capture matrix covers 20 deterministic states at each of two viewports:

- desktop: 1440 × 900
- mobile: 390 × 844
- states: overview, 3 category filters, 2 searches, and all 14 memory details

Run a local server from `photo_map/`, install Playwright and Chromium, then run:

```bash
EVIDENCE_APP_URL=http://127.0.0.1:8000 python evidence/capture_matrix.py
```

The script rejects unexpectedly small files and requires exactly 40 PNGs before
writing `manifest.json`.