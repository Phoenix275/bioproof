import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))


def make_gel(seed=3, w=400, h=200):
    """Small synthetic gel: dark background, bright bands, light noise."""
    rng = np.random.default_rng(seed)
    img = np.full((h, w), 0.1, np.float32)
    for lane in range(6):
        cx = 30 + lane * 60
        for _ in range(int(rng.integers(2, 5))):
            y = int(rng.integers(30, h - 30))
            t = int(rng.integers(4, 9))
            cv2.rectangle(img, (cx - 15, y - t // 2), (cx + 15, y + t // 2), float(rng.uniform(0.5, 0.9)), -1)
    img = cv2.GaussianBlur(img, (7, 7), 0)
    img = np.clip(img + rng.normal(0, 0.03, img.shape).astype(np.float32), 0, 1)
    return (img * 255).astype(np.uint8)


@pytest.fixture
def gel():
    return make_gel()


@pytest.fixture
def demo_dir():
    return PROJECT / "demo_images"
