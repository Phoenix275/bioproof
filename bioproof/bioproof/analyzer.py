"""Core analysis module for BioProof image integrity checks."""

import os
import cv2
import numpy as np
from .io_utils import load_gray, is_raw_ext, exif_ok


def has_metadata_mark(path: str) -> bool:
    """Check if file contains metadata watermark indicators.

    Looks for c2pa, xmpmeta, or other provenance markers in the first 256 KB.

    Args:
        path: Path to the image file

    Returns:
        True if metadata mark found, False otherwise
    """
    try:
        with open(path, 'rb') as f:
            chunk = f.read(256 * 1024)  # Read first 256 KB for better detection
            chunk_lower = chunk.lower()
            # Check for multiple provenance standards
            markers = [b'c2pa', b'xmpmeta', b'contentcredentials', b'aiprovenance']
            return any(marker in chunk_lower for marker in markers)
    except:
        return False


def has_visible_stamp(gray: np.ndarray, stamp_path: str) -> bool:
    """Check if image contains visible watermark stamp.

    Template matches the stamp in top-left and top-right corners.

    Args:
        gray: Grayscale image as numpy array
        stamp_path: Path to the stamp template image

    Returns:
        True if stamp found with correlation > 0.85, False otherwise
    """
    if not os.path.exists(stamp_path):
        return False

    try:
        # Load stamp and resize to 48x48
        stamp = cv2.imread(stamp_path, cv2.IMREAD_GRAYSCALE)
        if stamp is None:
            return False
        stamp = cv2.resize(stamp, (48, 48), interpolation=cv2.INTER_AREA)

        h, w = gray.shape[:2]

        # Check top-left corner (96x96 region)
        if h >= 96 and w >= 96:
            top_left = gray[0:96, 0:96]
            res_tl = cv2.matchTemplate(top_left, stamp, cv2.TM_CCOEFF_NORMED)
            max_tl = float(res_tl.max()) if res_tl.size > 0 else 0.0

            # Check top-right corner (96x96 region)
            top_right = gray[0:96, w-96:w]
            res_tr = cv2.matchTemplate(top_right, stamp, cv2.TM_CCOEFF_NORMED)
            max_tr = float(res_tr.max()) if res_tr.size > 0 else 0.0

            return max(max_tl, max_tr) > 0.85

        return False
    except:
        return False


def clone_score(gray: np.ndarray, seed: int = 7) -> float:
    """Detect likely duplicated band patches within the same image.

    Uses random template matching to find similar regions that may indicate
    cloned or copy-pasted bands.

    Args:
        gray: Grayscale image as numpy array
        seed: Random seed for reproducibility

    Returns:
        Clone score between 0 and 1, where higher values indicate more similarity
    """
    g = gray
    h, w = g.shape[:2]
    scale = 512 / max(h, w)
    if scale < 1.0:
        g = cv2.resize(g, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    g = g.astype(np.float32)
    g = (g - g.mean()) / (g.std() + 1e-6)

    H, W = g.shape
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(12):
        x = int(rng.integers(0, max(1, W - 64)))
        y = int(rng.integers(0, max(1, H - 32)))
        tpl = g[y : y + 32, x : x + 64]
        if tpl.shape != (32, 64):
            continue
        res = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)
        y0, y1 = max(0, y - 8), min(H, y + 40)
        x0, x1 = max(0, x - 8), min(W, x + 72)
        res[y0:y1, x0:x1] = -1.0
        scores.append(float(res.max()))
    return float(np.max(scores)) if scores else 0.0


def periodicity_score(gray: np.ndarray) -> float:
    """Detect excessive periodic structure common in synthetic textures.

    Uses FFT analysis to measure energy concentration that indicates
    grid-like or ring-like patterns.

    Args:
        gray: Grayscale image as numpy array

    Returns:
        Periodicity score, where higher values indicate more synthetic-looking patterns
    """
    g = gray.astype(np.float32)
    f = np.fft.fftshift(np.fft.fft2(g))
    mag = np.log(np.abs(f) + 1e-6)
    H, W = mag.shape
    cy, cx = H // 2, W // 2
    center = float(mag[cy - 20 : cy + 20, cx - 20 : cx + 20].mean())
    global_mean = float(mag.mean())
    return float(global_mean - center)


def analyze_image(path: str, ai_declared: bool = False, stamp_path: str = "assets/digital_stamp.png") -> dict:
    """Analyze a single image for integrity issues.

    Performs multiple checks:
    - Proof of origin (raw file format, EXIF metadata)
    - Clone detection (duplicated bands)
    - Periodicity analysis (synthetic texture detection)
    - Watermark verification (if digital generation declared)

    Args:
        path: Path to the image file
        ai_declared: Whether user declared digital tools were used to generate the image
        stamp_path: Path to the watermark stamp template

    Returns:
        Dictionary with analysis results matching the JSON schema
    """
    gray = load_gray(path)
    if gray is None:
        return {
            "file": os.path.basename(path),
            "status": "Needs review",
            "risk": 70,
            "reason": "cannot read image",
            "checks": {
                "has_raw": False,
                "exif_ok": False,
                "clone_score": 0.0,
                "periodicity_score": 0.0,
                "ai_declared": ai_declared,
                "mark_present": False,
            },
        }

    has_raw = is_raw_ext(path)
    has_exif = exif_ok(path)
    cscore = clone_score(gray)
    pscore = periodicity_score(gray)

    # Check for watermark
    metadata_mark = has_metadata_mark(path)
    visible_mark = has_visible_stamp(gray, stamp_path)
    mark_present = metadata_mark or visible_mark

    # ============================================================================
    # DECISION TREE: Pass / Needs Review / Policy Issue (Fail)
    # ============================================================================

    # Case 1: Digital generation declared with proper watermark → PASS
    if ai_declared and mark_present:
        return {
            "file": os.path.basename(path),
            "status": "Pass",
            "risk": 10,
            "reason": "Digitally generated with proper watermark - compliant with policy.",
            "checks": {
                "has_raw": bool(has_raw),
                "exif_ok": bool(has_exif),
                "clone_score": float(cscore),
                "periodicity_score": float(pscore),
                "ai_declared": bool(ai_declared),
                "mark_present": bool(mark_present),
            },
        }

    # Case 2: Digital generation declared but no watermark → FAIL (policy violation)
    if ai_declared and not mark_present:
        return {
            "file": os.path.basename(path),
            "status": "Policy issue",
            "risk": 100,
            "reason": "Digital generation declared but watermark missing - policy violation.",
            "checks": {
                "has_raw": bool(has_raw),
                "exif_ok": bool(has_exif),
                "clone_score": float(cscore),
                "periodicity_score": float(pscore),
                "ai_declared": bool(ai_declared),
                "mark_present": bool(mark_present),
            },
        }

    # Case 3+: Not digitally generated declared - analyze patterns
    risk = 0
    reasons = []

    # Check for suspicious patterns
    has_duplication = cscore > 0.97  # Slightly more sensitive
    has_synthetic_patterns = pscore > 0.25
    has_device_data = has_raw or has_exif

    # EDGE CASE: Has watermark but user didn't declare digital generation → suspicious
    if mark_present and not ai_declared:
        risk += 50
        reasons.append("Watermark detected but digital generation not declared")

    if has_duplication:
        risk += 40
        reasons.append("Duplicated regions detected")

    if has_synthetic_patterns:
        risk += 35
        reasons.append("Synthetic patterns detected")

    if not has_device_data:
        risk += 40
        reasons.append("No device metadata - cannot confirm image came from real lab equipment")

    # Decision based on combined factors
    if risk <= 25 and has_device_data:
        status = "Pass"
        reasons = ["Verified authentic - has lab equipment metadata and no suspicious patterns"]
    elif (has_synthetic_patterns or has_duplication or mark_present) and not has_device_data:
        # Looks synthetic but not declared → FAIL
        status = "Policy issue"
        risk = min(100, risk)
        reasons.append("Likely digitally generated - must be declared and watermarked if digital tools were used")
    elif not has_device_data:
        # No verification at all → FAIL
        status = "Policy issue"
        reasons.append("Unable to verify authentic lab origin")
    else:
        # Suspicious but has device data → human review needed
        status = "Needs review"
        reasons.append("Has equipment metadata but suspicious patterns detected")

    return {
        "file": os.path.basename(path),
        "status": status,
        "risk": int(min(100, max(0, risk))),
        "reason": "; ".join(reasons),
        "checks": {
            "has_raw": bool(has_raw),
            "exif_ok": bool(has_exif),
            "clone_score": float(cscore),
            "periodicity_score": float(pscore),
            "ai_declared": bool(ai_declared),
            "mark_present": bool(mark_present),
        },
    }
