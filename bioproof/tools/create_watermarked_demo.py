"""Create a demo image with visible watermark stamp."""

import numpy as np
import cv2
from PIL import Image

# Create a simple gel-like image
rng = np.random.RandomState(42)
h, w = 400, 600
img = np.zeros((h, w), np.uint8) + 20

# Add some bands
for i in range(6):
    x = 80 + i * 80
    for j in range(3):
        y = 100 + j * 100
        thickness = rng.randint(8, 15)
        cv2.rectangle(img, (x - 30, y - thickness // 2), (x + 30, y + thickness // 2), 200, -1)

# Add blur and noise
img = cv2.GaussianBlur(img, (7, 7), 0)
noise = np.random.normal(0, 10, img.shape).astype(np.int16)
img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

# Load and apply the stamp in top-left corner
stamp = cv2.imread("assets/digital_stamp.png", cv2.IMREAD_GRAYSCALE)
if stamp is not None:
    stamp_resized = cv2.resize(stamp, (48, 48))
    # Paste stamp at top-left (with some margin)
    img[10:58, 10:58] = stamp_resized

# Save
cv2.imwrite("demo_images/digital_watermarked.png", img)
print("Created demo_images/digital_watermarked.png with visible stamp")
