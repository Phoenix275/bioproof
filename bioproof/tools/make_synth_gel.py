"""Generate synthetic gel images for testing."""

import numpy as np
import cv2
import random


def synth_gel(w=800, h=400, lanes=8, bands_per_lane=(2, 5), seed=3):
    """Generate a synthetic gel electrophoresis image.

    Args:
        w: Width of the image
        h: Height of the image
        lanes: Number of lanes to generate
        bands_per_lane: Tuple of (min, max) number of bands per lane
        seed: Random seed for reproducibility

    Returns:
        Synthetic gel image as uint8 numpy array
    """
    rng = random.Random(seed)
    img = np.zeros((h, w), np.float32) + 0.1
    lane_w = w // (lanes + 2)
    x0 = lane_w // 2
    for i in range(lanes):
        cx = x0 + i * lane_w
        nb = rng.randint(bands_per_lane[0], bands_per_lane[1])
        ys = sorted(rng.randint(40, h - 40) for _ in range(nb))
        for y in ys:
            thickness = rng.randint(4, 10)
            val = rng.uniform(0.5, 0.9)
            cv2.rectangle(
                img,
                (cx - 20, y - thickness // 2),
                (cx + 20, y + thickness // 2),
                val,
                -1,
            )
    # blur and add noise
    img = cv2.GaussianBlur(img, (7, 7), 0)
    noise = np.random.normal(0, 0.03, img.shape).astype(np.float32)
    img = np.clip(img + noise, 0, 1)
    img = (img * 255).astype(np.uint8)
    return img


if __name__ == "__main__":
    g = synth_gel()
    cv2.imwrite("demo_images/gel_sample_03.png", g)
    print("Created demo_images/gel_sample_03.png")
