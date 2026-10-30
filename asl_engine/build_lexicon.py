"""
Silent Voice Bridge v2 - ASL Lexicon Builder
Populates the local ASL sign dictionary in asl_engine/lexicon/

Downloads and caches standard ASL motion capture clips (.pose) for:
1. Core conversation signs & phrases
2. ASL fingerspelling alphabet (A-Z)
All data is stored locally so the synthesizer runs completely offline!
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from pose_format import Pose

LEXICON_DIR = Path(__file__).parent / "lexicon"
LEXICON_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = LEXICON_DIR / "index.json"

# Core vocabulary dictionary: Mapping from GLOSS to search phrase
CORE_VOCABULARY = {
    "HELLO": "hello",
    "GOODBYE": "goodbye",
    "HOW-ARE-YOU": "how are you",
    "YOUR": "your",
    "NAME": "name",
    "WHAT": "what",
    "THANK-YOU": "thank you",
    "PLEASE": "please",
    "DEAF": "deaf",
    "FINE": "fine",
    "HELP": "help",
    "YES": "yes",
    "NO": "no",
    "MY-NAME": "my name",
    "ME": "me",
    "YOU": "you",
    "MY": "my",
    "NICE-MEET-YOU": "nice to meet you",
    "PLEASE-REPEAT": "please repeat",
    "WRITE-PLEASE": "write it down",
    "AIRPLANE": "airplane",
    "CAR": "car",
    "WATER": "water",
    "FOOD": "food",
    "LIKE": "like",
    "WHY": "why",
    "WHERE": "where",
    "WHEN": "when",
    "WHO": "who",
    "HOW": "how",
    "I-LOVE-YOU": "i love you",
    "SORRY": "sorry",
}

# Alphabet letters A-Z for fingerspelling
ALPHABET = {f"FS_{chr(c)}": chr(c).lower() for c in range(ord('A'), ord('Z') + 1)}


def fetch_pose_for_term(term: str, retries: int = 2) -> bytes:
    """Queries sign.mt text-to-pose endpoint for an ASL clip."""
    encoded = urllib.parse.quote(term)
    url = f"https://us-central1-sign-mt.cloudfunctions.net/spoken_text_to_signed_pose?text={encoded}&spoken=en&signed=ase"
    req = urllib.request.Request(url, headers={"User-Agent": "SilentVoiceBridge/2.0"})

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as e:
            if attempt < retries:
                time.sleep(1.0)
            else:
                raise RuntimeError(f"Failed to fetch '{term}': {e}")


def build_lexicon():
    print("=" * 65)
    print("SILENT VOICE BRIDGE v2 - ASL LEXICON BUILDER")
    print(f"Target Directory: {LEXICON_DIR}")
    print("=" * 65)

    index_data = {}
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r") as f:
                index_data = json.load(f)
        except Exception:
            index_data = {}

    all_items = {**CORE_VOCABULARY, **ALPHABET}
    total = len(all_items)
    print(f"\nProcessing {total} ASL lexicon entries ({len(CORE_VOCABULARY)} signs + {len(ALPHABET)} letters)...\n")

    success_count = 0
    cached_count = 0

    for idx, (gloss, search_term) in enumerate(all_items.items(), 1):
        target_file = LEXICON_DIR / f"{gloss}.pose"

        if target_file.exists() and gloss in index_data:
            cached_count += 1
            print(f"[{idx:2d}/{total}] ✓ (Cached) {gloss:15} -> {index_data[gloss]['frames']} frames")
            continue

        try:
            print(f"[{idx:2d}/{total}] 🌐 Fetching {gloss:15} ('{search_term}')...", end="", flush=True)
            pose_bytes = fetch_pose_for_term(search_term)
            target_file.write_bytes(pose_bytes)

            pose = Pose.read(pose_bytes)
            num_frames = len(pose.body.data)
            fps = float(pose.body.fps) if pose.body.fps > 0 else 25.0

            index_data[gloss] = {
                "file": f"{gloss}.pose",
                "gloss": gloss,
                "search_term": search_term,
                "frames": num_frames,
                "fps": fps,
                "is_fingerspell": gloss.startswith("FS_"),
            }
            success_count += 1
            print(f" OK ({num_frames} frames @ {fps} fps)")
            time.sleep(0.3)  # Gentle delay between requests
        except Exception as e:
            print(f" FAILED ({e})")

    # Save index
    with open(INDEX_FILE, "w") as f:
        json.dump(index_data, f, indent=2)

    print("\n" + "=" * 65)
    print(f"✓ Lexicon Build Complete! Total Indexed: {len(index_data)} entries")
    print(f"  - Cached: {cached_count}")
    print(f"  - Newly Downloaded: {success_count}")
    print(f"  - Index saved to: {INDEX_FILE}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    build_lexicon()
