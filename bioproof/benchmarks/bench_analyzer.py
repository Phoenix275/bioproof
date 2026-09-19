"""Benchmark BioProof on generated gels with known ground truth.

Builds three groups of synthetic gel images:
  clean    : untouched gels
  cloned   : a lane of bands copy-pasted onto another part of the same gel
  stamped  : gels carrying the visible watermark stamp

and reports detection rates plus per-image latency. Run from the project folder:

    python benchmarks/bench_analyzer.py --n 30
"""

import argparse
import os
import sys
import tempfile
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bioproof.analyzer import analyze_image, default_stamp_path


def make_gel(seed, w=800, h=400):
    rng = np.random.default_rng(seed)
    img = np.full((h, w), 0.1, np.float32)
    lane_w = w // 10
    for lane in range(8):
        cx = lane_w // 2 + lane * lane_w
        for _ in range(int(rng.integers(2, 6))):
            y = int(rng.integers(40, h - 40))
            t = int(rng.integers(4, 10))
            cv2.rectangle(img, (cx - 20, y - t // 2), (cx + 20, y + t // 2), float(rng.uniform(0.5, 0.9)), -1)
    img = cv2.GaussianBlur(img, (7, 7), 0)
    img = np.clip(img + rng.normal(0, 0.03, img.shape).astype(np.float32), 0, 1)
    return (img * 255).astype(np.uint8)


def clone_lane(img, seed):
    rng = np.random.default_rng(seed + 10_000)
    out = img.copy()
    _, w = out.shape
    patch = out[40:200, 60:140].copy()
    x = int(rng.integers(300, w - 90))
    out[180:340, x:x + 80] = patch
    return out


def add_stamp(img):
    stamp = cv2.imread(default_stamp_path(), cv2.IMREAD_GRAYSCALE)
    out = img.copy()
    out[10:58, 10:58] = cv2.resize(stamp, (48, 48))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="images per group")
    args = ap.parse_args()

    groups = {"clean": [], "cloned": [], "stamped": []}
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(args.n):
            gel = make_gel(i)
            for name, img in (("clean", gel), ("cloned", clone_lane(gel, i)), ("stamped", add_stamp(gel))):
                path = os.path.join(tmp, f"{name}_{i}.png")
                cv2.imwrite(path, img)
                groups[name].append(path)

        timings = []
        results = {}
        for name, paths in groups.items():
            results[name] = []
            for p in paths:
                t0 = time.perf_counter()
                r = analyze_image(p, ai_declared=False)
                timings.append(time.perf_counter() - t0)
                results[name].append(r)

        clean_scores = [r["checks"]["clone_score"] for r in results["clean"]]
        cloned_scores = [r["checks"]["clone_score"] for r in results["cloned"]]
        stamp_hits = sum(r["checks"]["mark_present"] for r in results["stamped"])
        clean_marks = sum(r["checks"]["mark_present"] for r in results["clean"])

        print(f"images per group         : {args.n}")
        print(f"mean latency per image   : {1000 * np.mean(timings):.1f} ms")
        print(f"p95 latency per image    : {1000 * np.percentile(timings, 95):.1f} ms")
        print(f"clone score, clean gels  : {np.mean(clean_scores):.3f}")
        print(f"clone score, cloned gels : {np.mean(cloned_scores):.3f}")
        print(f"visible stamp recall     : {stamp_hits}/{args.n}")
        print(f"stamp false positives    : {clean_marks}/{args.n}")



if __name__ == "__main__":
    main()
