"""Workstream A: the (30, 68) feature tensor contract (README Section 4.1)."""
from types import SimpleNamespace

import numpy as np

from palm_normalizer import FEATURE_DIM, NUM_RESAMPLED_FRAMES, normalize_landmarks_frame, resample_sequence


def make_hand(offset_x=0.0, scale=1.0):
    """A fake MediaPipe hand: 21 points fanned out from a wrist."""
    points = []
    for i in range(21):
        points.append(SimpleNamespace(x=0.5 + offset_x + scale * 0.01 * i, y=0.5 - scale * 0.01 * i, z=0.0))
    return points


def make_results(hands, labels):
    handedness = [[SimpleNamespace(category_name=label)] for label in labels]
    return SimpleNamespace(hand_landmarks=hands, handedness=handedness)


def test_contract_constants():
    assert NUM_RESAMPLED_FRAMES == 30
    assert FEATURE_DIM == 68


def test_frame_has_68_features():
    feat = normalize_landmarks_frame(make_results([make_hand()], ["Right"]), None)
    assert feat.shape == (68,)
    assert np.all(np.isfinite(feat))


def test_no_hands_gives_zero_vector():
    feat = normalize_landmarks_frame(make_results([], []), None)
    assert feat.shape == (68,)
    assert not np.any(feat)


def test_two_hands_supported():
    results = make_results([make_hand(), make_hand(offset_x=-0.2)], ["Right", "Left"])
    feat = normalize_landmarks_frame(results, None)
    assert feat.shape == (68,)
    assert np.any(feat)


def test_invariant_to_hand_position():
    """Palm-space features should not change when the whole hand moves across the frame."""
    a = normalize_landmarks_frame(make_results([make_hand()], ["Right"]), None)
    b = normalize_landmarks_frame(make_results([make_hand(offset_x=0.1)], ["Right"]), None)
    np.testing.assert_allclose(a[:42], b[:42], atol=1e-5)


def test_resample_any_length_to_30():
    for length in (1, 7, 30, 95):
        seq = np.random.rand(length, FEATURE_DIM).astype(np.float32)
        out = resample_sequence(seq)
        assert out.shape == (30, 68)


def test_resample_empty_sequence():
    assert resample_sequence([]).shape == (30, 68)
