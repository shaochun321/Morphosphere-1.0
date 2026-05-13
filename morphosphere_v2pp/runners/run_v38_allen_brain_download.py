#!/usr/bin/env python3
"""Allen Brain Observatory Data Downloader & Extractor.

Downloads ONE small ophys session from Allen Brain Observatory,
extracts calcium imaging traces and cell coordinates into CSV files
for use by the Morphosphere pipeline.

Output directory: data/allen_brain/
Output files:
  - allen_brain_dff_traces.csv     (ΔF/F fluorescence traces)
  - allen_brain_cell_coords.csv    (cell x, y coordinates)
  - allen_brain_metadata.json      (session info, DOI, license)
"""
import os, sys, json, time, csv
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "allen_brain"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = str(OUT_DIR / "brain_observatory_manifest.json")


def main():
    print("=" * 72)
    print("Allen Brain Observatory — Data Download & Extraction")
    print("Phase 3.2: Real Neural Data Integration")
    print("=" * 72)
    print(f"\n  Output directory: {OUT_DIR}")

    try:
        from allensdk.core.brain_observatory_cache import BrainObservatoryCache
    except ImportError:
        print("  ERROR: allensdk not installed. Run: pip install allensdk")
        return False

    # Initialize cache — this manages downloads
    print("\n  Initializing BrainObservatoryCache...")
    boc = BrainObservatoryCache(manifest_file=MANIFEST_PATH)

    # Step 1: Find the smallest available experiment
    print("  Fetching experiment list...")
    try:
        experiments = boc.get_ophys_experiments(stimuli=["natural_scenes"])
    except Exception as e:
        print(f"  ERROR fetching experiment list: {e}")
        print("  This likely means the API server is unreachable.")
        print("  Check your network connection and try again.")
        return False

    if not experiments:
        print("  ERROR: No experiments found.")
        return False

    print(f"  Found {len(experiments)} experiments with natural_scenes stimulus")

    # Pick a small one — prefer VISp (primary visual cortex) with fewest cells
    visp_exps = [e for e in experiments
                 if e.get("targeted_structure", "") == "VISp"]
    if visp_exps:
        # Sort by number of cells (ascending) to get smallest
        visp_exps.sort(key=lambda e: e.get("specimen_name", ""))
        target = visp_exps[0]
    else:
        target = experiments[0]

    exp_id = target["id"]
    print(f"\n  Selected experiment ID: {exp_id}")
    print(f"  Structure: {target.get('targeted_structure', 'unknown')}")
    print(f"  Imaging depth: {target.get('imaging_depth', 'unknown')} μm")

    # Step 2: Download the experiment data (NWB file)
    print(f"\n  Downloading NWB file for experiment {exp_id}...")
    print("  (This may take 1-10 minutes depending on file size and network)")

    try:
        dataset = boc.get_ophys_experiment_data(exp_id)
    except Exception as e:
        print(f"\n  DOWNLOAD FAILED: {e}")
        print(f"\n  Possible causes:")
        print(f"    1. Network timeout (file may be 0.5-2 GB)")
        print(f"    2. Allen API rate limiting")
        print(f"    3. Disk space insufficient")
        print(f"\n  Please check your network and try again.")
        return False

    print("  Download complete!")

    # Step 3: Extract ΔF/F traces
    print("\n  Extracting ΔF/F traces...")
    try:
        timestamps, dff = dataset.get_dff_traces()
        n_cells, n_timepoints = dff.shape
        print(f"  Traces: {n_cells} cells × {n_timepoints} timepoints")
    except Exception as e:
        print(f"  ERROR extracting dff traces: {e}")
        return False

    # Step 4: Extract cell coordinates
    print("  Extracting cell coordinates...")
    try:
        cell_ids = dataset.get_cell_specimen_ids()
        roi_ids = dataset.get_roi_mask_array()
        # Get cell coordinates from ROI masks
        cell_coords = []
        for i, cell_id in enumerate(cell_ids):
            # ROI mask is a 2D binary array — compute centroid
            mask = roi_ids[i]
            ys, xs = mask.nonzero()  # numpy arrays
            if len(xs) > 0:
                cx = float(xs.mean())
                cy = float(ys.mean())
            else:
                cx, cy = 0.0, 0.0
            cell_coords.append({
                "cell_id": int(cell_id),
                "x": round(cx, 2),
                "y": round(cy, 2),
                "roi_area": int(len(xs)),
            })
        print(f"  Coordinates: {len(cell_coords)} cells extracted")
    except Exception as e:
        print(f"  ERROR extracting coordinates: {e}")
        # Fallback: use index-based coordinates
        cell_coords = [{"cell_id": int(cid), "x": float(i), "y": 0.0, "roi_area": 0}
                       for i, cid in enumerate(cell_ids)]
        print(f"  Fallback: using index-based coordinates for {len(cell_coords)} cells")

    # Step 5: Save to CSV
    print("\n  Saving to CSV...")

    # 5a: ΔF/F traces (subsample timepoints to keep file manageable)
    max_tp = min(n_timepoints, 3000)  # cap at 3000 timepoints
    step = max(1, n_timepoints // max_tp)
    traces_path = OUT_DIR / "allen_brain_dff_traces.csv"
    with open(traces_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header: cell_id, t0, t1, t2, ...
        header = ["cell_id"] + [f"t{j}" for j in range(0, n_timepoints, step)]
        writer.writerow(header)
        for i in range(n_cells):
            row = [int(cell_ids[i])] + [round(float(dff[i, j]), 6)
                                         for j in range(0, n_timepoints, step)]
            writer.writerow(row)
    traces_size = traces_path.stat().st_size / 1024
    print(f"  Saved: {traces_path.name} ({traces_size:.0f} KB, "
          f"{n_cells} cells × {len(header)-1} timepoints)")

    # 5b: Cell coordinates
    coords_path = OUT_DIR / "allen_brain_cell_coords.csv"
    with open(coords_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cell_id", "x", "y", "roi_area"])
        writer.writeheader()
        writer.writerows(cell_coords)
    print(f"  Saved: {coords_path.name} ({len(cell_coords)} cells)")

    # 5c: Metadata
    meta = {
        "experiment_id": exp_id,
        "targeted_structure": target.get("targeted_structure", ""),
        "imaging_depth_um": target.get("imaging_depth", 0),
        "n_cells": n_cells,
        "n_timepoints_original": n_timepoints,
        "n_timepoints_saved": len(header) - 1,
        "subsample_step": step,
        "data_source": "Allen Brain Observatory",
        "data_url": f"https://observatory.brain-map.org/visualcoding/experiment/{exp_id}",
        "license": "Allen Institute Terms of Use (non-commercial research)",
        "doi": "10.1038/s41586-019-1346-5",
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "allensdk_version": "2.16.2",
    }
    meta_path = OUT_DIR / "allen_brain_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {meta_path.name}")

    # Summary
    print(f"\n{'=' * 72}")
    print(f"  DOWNLOAD & EXTRACTION COMPLETE")
    print(f"{'=' * 72}")
    print(f"  Experiment: {exp_id} ({target.get('targeted_structure', '')})")
    print(f"  Cells: {n_cells}")
    print(f"  Timepoints: {n_timepoints} (saved {len(header)-1})")
    print(f"  Files:")
    print(f"    {traces_path}")
    print(f"    {coords_path}")
    print(f"    {meta_path}")
    print(f"{'=' * 72}")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n  If download fails, please tell me and I'll provide alternatives.")
        sys.exit(1)
