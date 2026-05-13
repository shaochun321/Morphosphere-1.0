"""Extract cell centroids from PhC-C2DH-U373 tracking masks.

Reads TRA label masks (TIFF) and man_track.txt lineage files,
produces a CSV identical in schema to ctc_centroids_real_v24.csv.
"""
import csv, os, sys
from pathlib import Path
from collections import defaultdict
from PIL import Image
import numpy as np

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data" / "PhC-C2DH-U373" / "PhC-C2DH-U373"
OUT_CSV = BASE / "data" / "phc_u373_centroids.csv"

DATASET = "PhC-C2DH-U373"
LICENSE = "CC-BY-4.0"
DOI = ""  # CTC training data, no specific DOI
CITATION = "ctc_phc_c2dh_u373"

COLUMNS = [
    "source_id", "sample_id", "clock_domain", "time_s",
    "sensor_id", "sensor_kind", "x", "y", "z", "channel",
    "value", "uncertainty", "track_id", "frame",
    "centroid_x", "centroid_y", "centroid_z", "area",
    "sequence_id", "license", "citation_key", "dataset_name", "doi",
    "parent_track_id", "start_frame", "end_frame",
]


def parse_man_track(txt_path):
    """Parse man_track.txt: track_id start_frame end_frame parent_id"""
    tracks = {}
    if not txt_path.exists():
        return tracks
    with open(txt_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                tid, sf, ef, parent = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                tracks[tid] = {"start": sf, "end": ef, "parent": parent}
    return tracks


def extract_centroids_from_mask(mask_path):
    """Extract centroid (cx, cy) and area for each labeled region."""
    img = Image.open(mask_path)
    arr = np.array(img)
    labels = np.unique(arr)
    results = []
    for label in labels:
        if label == 0:
            continue  # background
        ys, xs = np.where(arr == label)
        cx = float(xs.mean())
        cy = float(ys.mean())
        area = len(xs)
        results.append((int(label), cx, cy, area))
    return results


def extract_sequence(seq_id):
    tra_dir = DATA_DIR / f"{seq_id}_GT" / "TRA"
    if not tra_dir.exists():
        print(f"  WARNING: {tra_dir} not found, skipping")
        return []

    tracks = parse_man_track(tra_dir / "man_track.txt")
    print(f"  Seq {seq_id}: {len(tracks)} tracks in lineage file")

    rows = []
    mask_files = sorted(tra_dir.glob("man_track*.tif"))
    print(f"  Seq {seq_id}: {len(mask_files)} mask frames")

    for mf in mask_files:
        # Extract frame number from filename: man_track000.tif -> 0
        fname = mf.stem  # man_track000
        frame = int(fname.replace("man_track", ""))

        centroids = extract_centroids_from_mask(mf)
        for tid, cx, cy, area in centroids:
            t_info = tracks.get(tid, {"start": frame, "end": frame, "parent": 0})
            rows.append({
                "source_id": f"ctc_{DATASET.lower()}_v1",
                "sample_id": f"{DATASET}_{seq_id}_t{frame:03d}_track{tid}",
                "clock_domain": "ctc_frame",
                "time_s": f"{frame:.6f}",
                "sensor_id": f"{DATASET}_{seq_id}",
                "sensor_kind": "ctc_tracking_centroid",
                "x": f"{cx:.6f}",
                "y": f"{cy:.6f}",
                "z": "0.000000",
                "channel": "cell_centroid_motion",
                "value": f"{area:.6f}",
                "uncertainty": "0.000000",
                "track_id": f"{seq_id}_{tid}",
                "frame": str(frame),
                "centroid_x": f"{cx:.6f}",
                "centroid_y": f"{cy:.6f}",
                "centroid_z": "0.000000",
                "area": str(area),
                "sequence_id": seq_id,
                "license": LICENSE,
                "citation_key": CITATION,
                "dataset_name": DATASET,
                "doi": DOI,
                "parent_track_id": str(t_info["parent"]),
                "start_frame": str(t_info["start"]),
                "end_frame": str(t_info["end"]),
            })
    return rows


def main():
    print(f"Extracting centroids from {DATA_DIR}")
    all_rows = []
    for seq in ["01", "02"]:
        rows = extract_sequence(seq)
        all_rows.extend(rows)
        print(f"  Seq {seq}: {len(rows)} centroid observations")

    print(f"\nTotal: {len(all_rows)} rows")
    print(f"Writing to {OUT_CSV}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Done: {OUT_CSV.name} ({os.path.getsize(OUT_CSV) // 1024} KB)")


if __name__ == "__main__":
    main()
