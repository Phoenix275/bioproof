"""Create all three demo images for BioProof testing."""

import numpy as np
import cv2
import random
from PIL import Image
from datetime import datetime


def create_pass_image():
    """Create a clean gel image saved as .tif for 'Pass' demo."""
    rng = random.Random(42)
    h, w = 600, 900
    img = np.zeros((h, w), np.float32) + 0.08

    lane_w = w // 10
    x0 = lane_w

    # Create 8 lanes with highly varied bands to avoid clone detection
    for i in range(8):
        cx = x0 + i * lane_w
        nb = rng.randint(2, 6)
        # More spread out positions
        ys = sorted(rng.randint(80, h - 80) for _ in range(nb))
        for j, y in enumerate(ys):
            # Much more variation in band characteristics
            thickness = rng.randint(6, 20)
            width = rng.randint(18, 40)
            val = rng.uniform(0.4, 0.95)
            # More positional variation
            x_offset = rng.randint(-5, 5)
            y_offset = rng.randint(-4, 4)

            # Draw ellipse instead of rectangle for more variation
            center = (cx + x_offset, y + y_offset)
            axes = (width, thickness // 2)
            angle = rng.uniform(-10, 10)
            cv2.ellipse(img, center, axes, angle, 0, 360, val, -1)

            # Add some random texture to each band
            band_region = img[
                max(0, y + y_offset - thickness):min(h, y + y_offset + thickness),
                max(0, cx + x_offset - width):min(w, cx + x_offset + width)
            ]
            band_noise = np.random.normal(0, 0.05, band_region.shape).astype(np.float32)
            band_region[:] = np.clip(band_region + band_noise, 0, 1)

    # Add realistic blur with variation
    img = cv2.GaussianBlur(img, (9, 9), 0)
    noise = np.random.normal(0, 0.03, img.shape).astype(np.float32)
    img = np.clip(img + noise, 0, 1)
    img = (img * 255).astype(np.uint8)

    # Save as TIFF with basic EXIF
    pil_img = Image.fromarray(img)
    exif = pil_img.getexif()
    exif[271] = "BioImager"  # Make
    exif[272] = "GelDoc 3000"  # Model
    exif[306] = datetime.now().strftime("%Y:%m:%d %H:%M:%S")  # DateTime

    pil_img.save("demo_images/gel_sample_01.tif", exif=exif)
    print("Created demo_images/gel_sample_01.tif")


def create_clone_suspect_image():
    """Create a gel image with cloned bands for 'Needs review' demo."""
    rng = random.Random(99)
    h, w = 400, 800
    img = np.zeros((h, w), np.float32) + 0.1

    lane_w = w // 10
    x0 = lane_w // 2

    # Create lanes with varied bands
    for i in range(8):
        cx = x0 + i * lane_w
        nb = rng.randint(2, 5)
        ys = sorted(rng.randint(60, h - 60) for _ in range(nb))
        for j, y in enumerate(ys):
            thickness = rng.randint(5, 15)
            width = rng.randint(20, 35)
            val = rng.uniform(0.5, 0.95)
            x_offset = rng.randint(-3, 3)
            y_offset = rng.randint(-2, 2)
            cv2.rectangle(
                img,
                (cx + x_offset - width, y + y_offset - thickness // 2),
                (cx + x_offset + width, y + y_offset + thickness // 2),
                val,
                -1,
            )

    img = cv2.GaussianBlur(img, (7, 7), 0)
    noise = np.random.normal(0, 0.025, img.shape).astype(np.float32)
    img = np.clip(img + noise, 0, 1)
    img = (img * 255).astype(np.uint8)

    # Clone a larger band region to ensure detection
    # Copy an 80x50 region from lane 2 to lane 6
    y_src, x_src = 120, 140
    y_dst, x_dst = 120, 460
    patch = img[y_src : y_src + 50, x_src : x_src + 80].copy()
    img[y_dst : y_dst + 50, x_dst : x_dst + 80] = patch

    # Add EXIF to ensure it's not flagged as Policy issue
    pil_img = Image.fromarray(img)
    exif = pil_img.getexif()
    exif[271] = "BioImager"
    exif[272] = "GelDoc 3000"
    exif[306] = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

    # Save as JPG with EXIF
    pil_img.save("demo_images/gel_sample_02.jpg", exif=exif, quality=95)
    print("Created demo_images/gel_sample_02.jpg")


if __name__ == "__main__":
    create_pass_image()
    create_clone_suspect_image()
    print("\nAll demo images created successfully!")
