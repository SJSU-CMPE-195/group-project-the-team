"""Workstream D: sign library format (Section 4.2) and DTW template matching."""
import json
from pathlib import Path

import numpy as np
import pytest
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

ROOT_DIR = Path(__file__).resolve().parent.parent
SIGNS_DIR = ROOT_DIR / "library" / "signs"
TENSORS_DIR = ROOT_DIR / "library" / "tensors"


def load_library():
    library = {}
    for path in sorted(SIGNS_DIR.glob("*.json")):
        entry = json.loads(path.read_text())
        library[entry["gloss"]] = [
            (t["id"], np.load(TENSORS_DIR / t["tensor_file"])) for t in entry["templates"]
        ]
    return library


@pytest.mark.parametrize("path", sorted(SIGNS_DIR.glob("*.json")), ids=lambda p: p.stem)
def test_entry_matches_contract(path):
    entry = json.loads(path.read_text())
    for key in ("gloss", "english", "category", "templates", "verified_by_asl_reviewer"):
        assert key in entry
    assert entry["templates"], "every sign needs at least one template"
    for template in entry["templates"]:
        tensor = np.load(TENSORS_DIR / template["tensor_file"])
        assert tensor.shape == (30, 68)


def test_library_has_demo_vocabulary():
    assert len(list(SIGNS_DIR.glob("*.json"))) >= 10


def test_leave_one_out_dtw_accuracy():
    """Each template, matched against all the others, should find its own sign."""
    library = load_library()
    correct = total = 0
    for gloss, templates in library.items():
        for test_id, test_arr in templates:
            best_gloss, best_d = None, float("inf")
            for ref_gloss, refs in library.items():
                for ref_id, ref_arr in refs:
                    if ref_id == test_id:
                        continue
                    d, _ = fastdtw(test_arr, ref_arr, dist=euclidean)
                    if d < best_d:
                        best_gloss, best_d = ref_gloss, d
            correct += best_gloss == gloss
            total += 1
    accuracy = correct / total
    print(f"Leave-one-out DTW accuracy: {correct}/{total} ({accuracy:.1%})")
    assert accuracy >= 0.85
