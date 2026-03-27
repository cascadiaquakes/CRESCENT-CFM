# CFM 3D Fault Surface Processing Scripts

Scripts for generating optimized versions of the CRESCENT Community Fault Model 3D surfaces for web viewer performance.

## Prerequisites

```bash
pip install open3d numpy
```

## Scripts

### `decimate_cfm.py` — Mesh Decimation

Reduces triangle count in the full-resolution 3D fault surface GeoJSON using [Open3D](https://www.open3d.org/) quadric decimation. The algorithm removes triangles in flat areas while preserving detail around complex edges and curves.

**Offshore faults** automatically receive a higher triangle retention ratio (2x) to preserve boundary visibility.

**Usage**

```bash
python scripts/decimate_cfm.py --input crescent_cfm_files/crescent_cfm_crustal_3d.geojson --output crescent_cfm_files/crescent_cfm_crustal_3d_lowres.geojson --ratio 0.07
```

`--ratio` sets the fraction of triangles kept for onshore faults. Offshore faults automatically keep 2x that amount (capped at 30%). Lower ratio = smaller file but less detail. The current production value `0.07` produces a ~6MB file.

```

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | required | Path to full-resolution GeoJSON |
| `--output` | required | Path for decimated output |
| `--ratio` | `0.1` | Fraction of triangles to keep for onshore faults (offshore gets 2x, capped at 30%) |

**Example ratios:**

| Ratio | Onshore | Offshore | Approx Output |
|-------|---------|----------|---------------|
| 0.10 | 10% | 20% | ~8.6 MB |
| 0.07 | 7% | 14% | ~6.0 MB |
| 0.05 | 5% | 10% | ~4.5 MB |

The script also auto-injects an `id` property mirroring `CFM_ID` for viewer compatibility.

---

### `split_hires_faults.py` — Individual Fault Extraction

Splits the full-resolution 77MB GeoJSON into 329 individual files (one per fault) for on-demand high-resolution loading in the web viewer.

**Usage:**

```bash
cd scripts/
python split_hires_faults.py
```

No arguments needed. Reads from `../crescent_cfm_files/crescent_cfm_crustal_3d.geojson` and writes individual files to `../crescent_cfm_files/hires_faults/`.

Output files are named by CFM_ID: `1_hires.geojson`, `2_hires.geojson`, etc.

---

## Workflow

1. Run `decimate_cfm.py` to generate the low-res overview file
2. Run `split_hires_faults.py` to generate individual high-res files
3. Push both outputs to the `dev` branch
4. The CFM web viewer loads the low-res file by default and fetches individual high-res files on demand
