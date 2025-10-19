"""File I/O utilities for BioProof."""

from PIL import Image
import cv2
import os
import numpy as np

RAW_EXTS = {".tif", ".tiff"}


def load_gray(path: str):
    """Load an image as grayscale using OpenCV.

    Args:
        path: Path to the image file

    Returns:
        Grayscale image as numpy array, or None if loading fails
    """
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return img


def is_raw_ext(path: str) -> bool:
    """Check if the file extension indicates a raw format.

    For demo purposes, .tif and .tiff are treated as raw formats.

    Args:
        path: Path to the image file

    Returns:
        True if extension is .tif or .tiff
    """
    return os.path.splitext(path)[1].lower() in RAW_EXTS


def exif_ok(path: str) -> bool:
    """Check if the image has useful EXIF metadata.

    Looks for common camera metadata tags: Make (271), Model (272), DateTime (306).

    Args:
        path: Path to the image file

    Returns:
        True if any of the expected EXIF tags are present
    """
    try:
        img = Image.open(path)
        exif = img.getexif()
        # 271 Make, 272 Model, 306 DateTime
        return any(tag in exif for tag in [271, 272, 306])
    except Exception:
        return False
