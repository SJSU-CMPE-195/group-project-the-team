"""
Silent Voice Bridge v2 - Interactive ASL Motion Player
Standalone Workstream B Application.

Type any English phrase to see the synthesized ASL skeleton signer:
- Reorders English to ASL grammar
- Blends dictionary signs & fingerspelling seamlessly with Cosine S-curves
- Displays live HUD with current sign highlighting and playback controls
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from asl_engine.synthesizer import ASLSynthesizer


def play_synthesized_sign(synthesizer: ASLSynthesizer, text: str) -> bool:
    """
    Synthesizes and plays an ASL sign animation in an OpenCV window.
    Returns True if user wants to continue with another phrase, False to exit.
    """
    print(f"\n🎬 Synthesizing ASL motion for: \"{text}\"...")
    try:
        result = synthesizer.synthesize(text)
    except Exception as e:
        print(f"❌ Synthesis error: {e}")
        return True

    print(f"✓ ASL Glosses: {' -> '.join(result.glosses)}")
    print(f"✓ Total Frames: {result.total_frames} ({result.total_frames / result.fps:.1f}s)")
    print("🎨 Rendering animation frames...")
    frames = synthesizer.render_to_frames(result)

    window_name = "Silent Voice Bridge - ASL Avatar Engine (Workstream B)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 720)

    fps = result.fps
    delay_ms = max(1, int(1000.0 / fps))

    frame_idx = 0
    total_frames = len(frames)
    paused = False

    print("\n[Controls]: 'SPACE': Pause/Resume | 'R': Replay | 'ENTER': New phrase | 'Q': Quit\n")

    while True:
        frame = frames[frame_idx].copy()
        h, w = frame.shape[:2]

        # Status footer
        status_text = "PAUSED" if paused else "PLAYING"
        cv2.putText(frame, f"[{status_text}] Frame: {frame_idx + 1}/{total_frames} | 'SPACE': Pause | 'R': Replay | 'ENTER': Next",
                    (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(delay_ms if not paused else 50) & 0xFF

        if key == ord('q') or key == 27:
            cv2.destroyAllWindows()
            return False
        elif key == ord(' '):
            paused = not paused
        elif key == ord('r'):
            frame_idx = 0
            paused = False
        elif key == 13:  # Enter key
            cv2.destroyAllWindows()
            return True

        if not paused:
            frame_idx = (frame_idx + 1) % total_frames


def main():
    print("\n" + "=" * 65)
    print("SILENT VOICE BRIDGE v2 - ASL SYNTHESIS & AVATAR ENGINE")
    print("Custom SJSU CMPE 195 Senior Design Workstream B")
    print("=" * 65)

    synth = ASLSynthesizer()

    sample_phrases = [
        "What is your name?",
        "My name is Aramish",
        "Hello, how are you?",
        "Nice to meet you",
        "Thank you so much",
        "Could you please repeat that?",
        "I need help",
        "I like airplanes",
    ]

    if len(sys.argv) > 1:
        phrase = " ".join(sys.argv[1:])
        play_synthesized_sign(synth, phrase)
        return

    while True:
        print("\nPreset Demonstration Phrases:")
        for idx, p in enumerate(sample_phrases, 1):
            print(f"  [{idx}] \"{p}\"")
        print("\nEnter number (1-8), type any English sentence, or 'q' to exit:")

        try:
            choice = input("ASL Synthesize > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not choice or choice.lower() in ("q", "quit", "exit"):
            break

        if choice.isdigit() and 1 <= int(choice) <= len(sample_phrases):
            phrase = sample_phrases[int(choice) - 1]
        else:
            phrase = choice

        keep_going = play_synthesized_sign(synth, phrase)
        if not keep_going:
            break

    print("\n✓ ASL Engine closed.")


if __name__ == "__main__":
    main()
