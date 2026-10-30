"""
Silent Voice Bridge v2 - Library Cross-Validation & Benchmark
Validates templates against each other to check distinction and recognition accuracy.
"""

import numpy as np
import json
from pathlib import Path
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

BASE_DIR = Path(__file__).resolve().parent
LIBRARY_DIR = BASE_DIR / "library"
SIGNS_DIR = LIBRARY_DIR / "signs"
TENSORS_DIR = LIBRARY_DIR / "tensors"

def benchmark_library():
    print("\n" + "="*65)
    print("📊 SILENT VOICE BRIDGE v2 - TEMPLATE VERIFICATION REPORT")
    print("="*65)

    signs = list(SIGNS_DIR.glob("*.json"))
    if not signs:
        print("❌ No sign definitions found.")
        return

    library_data = {}
    for s_path in sorted(signs):
        with open(s_path, "r") as f:
            data = json.load(f)
        gloss = data["gloss"]
        templates = []
        for t in data.get("templates", []):
            t_file = TENSORS_DIR / t["tensor_file"]
            if t_file.exists():
                arr = np.load(t_file)
                templates.append((t["id"], arr))
        library_data[gloss] = templates

    total_templates = sum(len(t) for t in library_data.values())
    print(f"✓ Loaded {len(library_data)} Glosses with {total_templates} total templates.\n")

    # Leave-one-out validation: Match each template against all OTHER templates
    correct = 0
    total = 0
    confusion = {}

    for test_gloss, test_templates in library_data.items():
        for test_id, test_arr in test_templates:
            best_d = float('inf')
            best_match_gloss = None

            for ref_gloss, ref_templates in library_data.items():
                for ref_id, ref_arr in ref_templates:
                    if ref_id == test_id:
                        continue  # Don't match against self
                    d, _ = fastdtw(test_arr, ref_arr, dist=euclidean)
                    if d < best_d:
                        best_d = d
                        best_match_gloss = ref_gloss

            confidence = np.exp(-best_d / 100.0)
            is_match = (best_match_gloss == test_gloss)
            if is_match:
                correct += 1
            total += 1

            status = "✓ PASS" if is_match else f"❌ MISCLASSIFIED as {best_match_gloss}"
            print(f"• [{test_id}] {test_gloss:15s} -> Best match: {str(best_match_gloss):15s} (Dist: {best_d:5.1f}, Conf: {confidence*100:4.1f}%) | {status}")

    acc = (correct / total) * 100 if total > 0 else 0
    print("\n" + "-"*65)
    print(f"🎯 LEAVE-ONE-OUT ACCURACY: {correct}/{total} ({acc:.1f}%)")
    print("-"*65)

if __name__ == "__main__":
    benchmark_library()
