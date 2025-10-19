# BioProof

Scientific image integrity verification tool for western blots and gel electrophoresis.

## Overview

BioProof helps identify synthetic or manipulated scientific images by checking for:
- **Synthetic patterns** - Unnatural textures that suggest digital generation
- **Duplicated regions** - Copy-pasted or cloned areas suggesting manipulation
- **Device verification** - Presence of camera/lab equipment data proving authentic origin

Each image receives a decision: **Pass**, **Needs review**, or **Policy issue**, along with a risk score (0-100) and explanation.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If OpenCV installation fails, try:
```bash
pip install opencv-python-headless
```

## Usage

### Web Interface

Launch the Streamlit app:
```bash
streamlit run app.py
```

Upload 1-10 images and download the JSON report.

### Command Line

Scan a folder and generate a JSON report:
```bash
python -m bioproof.cli demo_images --out bioproof_report.json
```

## Demo Images

Three test images are included in `demo_images/`:

1. **gel_sample_01.tif** - Authentic gel with device metadata → **Pass**
2. **gel_sample_02.jpg** - Contains duplicated regions → **Needs review**
3. **gel_sample_03.png** - Synthetic patterns, no device data → **Policy issue**

## JSON Report Schema

```json
{
  "file": "sample.tif",
  "status": "Pass | Needs review | Policy issue",
  "risk": 0,
  "reason": "short plain English explanation",
  "checks": {
    "has_raw": true,
    "exif_ok": true,
    "clone_score": 0.42,
    "periodicity_score": 0.18
  }
}
```

## How It Works

### Synthetic Pattern Detection
- Uses FFT (Fast Fourier Transform) analysis to detect synthetic grid patterns
- Digitally generated images often have periodic textures not found in real lab photos
- Threshold: periodicity_score > 0.25 adds 30 risk points

### Duplication Detection
- Random template matching finds copy-pasted regions
- Detects when the same band appears multiple times (common in fake results)
- Threshold: clone_score > 0.98 adds 40 risk points

### Device Verification
- Checks for camera/lab equipment metadata (EXIF tags)
- Verifies `.tif`/`.tiff` raw format from imaging equipment
- Missing both adds 40 risk points - cannot prove authentic origin

### Risk Scoring
- **0-25**: Pass - Verified authentic
- **26+**: Needs review - Suspicious patterns but has device verification
- **26+**: Policy issue - High digital generation risk, no device verification

## Project Structure

```
bioproof/
  app.py                 # Streamlit web interface
  bioproof/
    __init__.py
    analyzer.py          # Core analysis algorithms
    io_utils.py          # File I/O and EXIF utilities
    cli.py               # Command-line interface
  demo_images/
    gel_sample_01.tif
    gel_sample_02.jpg
    gel_sample_03.png
  tools/
    make_synth_gel.py    # Synthetic gel generator
    create_demo_images.py # Demo image creator
  requirements.txt
  README.md
```

## Development

Generate new demo images:
```bash
python tools/create_demo_images.py
python tools/make_synth_gel.py
```

## License

Demo project for educational purposes.
