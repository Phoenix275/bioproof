"""Command-line interface for BioProof folder scanning."""

import argparse
import json
import os
import glob
from .analyzer import analyze_image


def main():
    """Scan a folder of images and generate a JSON report."""
    p = argparse.ArgumentParser(description="BioProof folder scan")
    p.add_argument("folder", help="folder of images")
    p.add_argument("--out", default="bioproof_report.json", help="output JSON file")
    args = p.parse_args()

    exts = ("*.tif", "*.tiff", "*.png", "*.jpg", "*.jpeg")
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(args.folder, e)))

    results = [analyze_image(f) for f in files]
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {args.out} with {len(results)} items")


if __name__ == "__main__":
    main()
