"""Unit tests for the individual detection scores."""

import numpy as np
import pytest

from bioproof.analyzer import clone_score, has_metadata_mark, periodicity_score


def test_clone_score_is_higher_for_pasted_patch(gel):
    rng = np.random.default_rng(0)
    noise = rng.integers(0, 255, gel.shape, dtype=np.uint8)
    cloned = noise.copy()
    # Paste the same 64x128 patch into two separate places.
    patch = noise[20:84, 20:148].copy()
    cloned[110:174, 240:368] = patch
    assert clone_score(cloned) > clone_score(noise)


def test_clone_score_is_deterministic(gel):
    assert clone_score(gel, seed=7) == clone_score(gel, seed=7)


def test_clone_score_bounded(gel):
    score = clone_score(gel)
    assert -1.0 <= score <= 1.0


def test_periodicity_separates_flat_spectrum_from_gel(gel):
    # White noise has a flat spectrum, so the score sits near zero.
    # A real-looking gel concentrates energy at low frequencies and scores well below it.
    rng = np.random.default_rng(1)
    noise = rng.integers(0, 255, gel.shape, dtype=np.uint8)
    assert abs(periodicity_score(noise)) < 0.1
    assert periodicity_score(gel) < periodicity_score(noise) - 1.0


@pytest.mark.xfail(reason="Known gap: the score compares global vs center log-magnitude, "
                          "so it does not yet react to periodic texture laid over a gel. "
                          "See docs/ARCHITECTURE.md.", strict=True)
def test_periodicity_rises_with_grid_texture(gel):
    yy, xx = np.mgrid[0:gel.shape[0], 0:gel.shape[1]]
    textured = np.clip(gel.astype(float) + 60 * np.sin(xx / 1.5) * np.sin(yy / 1.5), 0, 255).astype(np.uint8)
    assert periodicity_score(textured) > periodicity_score(gel) + 0.25


def test_metadata_mark_detects_provenance_bytes(tmp_path):
    marked = tmp_path / "marked.bin"
    marked.write_bytes(b"\x89PNG....<x:xmpmeta>...C2PA manifest")
    clean = tmp_path / "clean.bin"
    clean.write_bytes(b"\x89PNG just pixels")
    assert has_metadata_mark(str(marked))
    assert not has_metadata_mark(str(clean))


def test_metadata_mark_missing_file_is_false(tmp_path):
    assert not has_metadata_mark(str(tmp_path / "missing.png"))
