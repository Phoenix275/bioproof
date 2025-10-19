"""Create watermark stamp for BioProof."""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Create a 48x48 black square with white "DG" text
img = Image.new('L', (48, 48), color=0)  # Black background
draw = ImageDraw.Draw(img)

# Try to use a default font, fall back to bitmap if needed
try:
    # Use a larger font size for visibility
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
except:
    font = ImageFont.load_default()

# Draw "DG" in white, centered
draw.text((8, 4), "DG", fill=255, font=font)

# Save the stamp
img.save("assets/digital_stamp.png")
print("Created assets/digital_stamp.png")
