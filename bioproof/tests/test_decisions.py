"""End-to-end tests of the Pass / Needs review / Policy issue decision tree."""

import cv2

from bioproof.analyzer import analyze_image, default_stamp_path

REQUIRED_KEYS = {"file", "status", "risk", "reason", "checks"}
CHECK_KEYS = {"has_raw", "exif_ok", "clone_score", "periodicity_score", "ai_declared", "mark_present"}


def _schema_ok(result):
    assert REQUIRED_KEYS <= result.keys()
    assert CHECK_KEYS <= result["checks"].keys()
    assert 0 <= result["risk"] <= 100
    assert result["status"] in {"Pass", "Needs review", "Policy issue"}


def test_demo_images_match_readme(demo_dir):
    expected = {
        "gel_sample_01.tif": "Pass",
        "gel_sample_02.jpg": "Needs review",
        "gel_sample_03.png": "Policy issue",
    }
    for name, status in expected.items():
        result = analyze_image(str(demo_dir / name))
        _schema_ok(result)
        assert result["status"] == status, (name, result["reason"])


def test_declared_and_watermarked_passes(demo_dir):
    result = analyze_image(str(demo_dir / "ai_watermarked.png"), ai_declared=True)
    _schema_ok(result)
    assert result["status"] == "Pass"
    assert result["checks"]["mark_present"]


def test_watermark_without_declaration_is_flagged(demo_dir):
    result = analyze_image(str(demo_dir / "ai_watermarked.png"), ai_declared=False)
    assert result["status"] == "Policy issue"
    assert "not declared" in result["reason"]


def test_declared_without_watermark_is_policy_issue(tmp_path, gel):
    path = tmp_path / "plain.png"
    cv2.imwrite(str(path), gel)
    result = analyze_image(str(path), ai_declared=True)
    _schema_ok(result)
    assert result["status"] == "Policy issue"
    assert result["risk"] == 100


def test_unreadable_file_needs_review(tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"not an image")
    result = analyze_image(str(path))
    _schema_ok(result)
    assert result["status"] == "Needs review"


def test_default_stamp_is_bundled():
    # Regression: the default used to point at a file that did not exist,
    # which silently turned off visible-stamp detection.
    import os

    assert os.path.exists(default_stamp_path())
