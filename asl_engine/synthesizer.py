"""
Silent Voice Bridge v2 - ASL Sign Synthesizer
Master Orchestrator of custom Workstream B Engine.

Converts English text into continuous ASL motion:
1. English -> ASL grammatical gloss reordering & filtering (english_to_gloss.py).
2. Lexicon retrieval: Pulls high-definition sign clips & fingerspelling alphabet from local cache.
3. Motion blending: S-curve cosine spline transitions & holds between signs (motion_blender.py).
4. Export: Outputs continuous Pose object, video file, or frame-accurate timing tracks.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
import urllib.parse
import urllib.request
from pose_format import Pose
from pose_format.pose_visualizer import PoseVisualizer
import cv2
import numpy as np

from asl_engine.english_to_gloss import translate_english_to_gloss
from asl_engine.motion_blender import blend_pose_sequence

LEXICON_DIR = Path(__file__).parent / "lexicon"


@dataclass
class SynthesizedSign:
    english_text: str
    glosses: List[str]
    details: List[dict]
    pose: Pose
    timings: List[Dict]
    total_frames: int
    fps: float


class ASLSynthesizer:
    def __init__(self, lexicon_dir: Path = LEXICON_DIR):
        self.lexicon_dir = Path(lexicon_dir)
        self.lexicon_dir.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, Pose] = {}

    def get_pose_for_gloss(self, gloss: str) -> Optional[Pose]:
        """Loads a pose from local cache, disk, or fetches it dynamically if missing."""
        if gloss in self.cache:
            return self.cache[gloss]

        pose_file = self.lexicon_dir / f"{gloss}.pose"
        if pose_file.exists():
            with open(pose_file, "rb") as f:
                pose = Pose.read(f.read())
            self.cache[gloss] = pose
            return pose

        # Dynamic fallback: if not in lexicon, try to fetch single term
        search_term = gloss.lower().replace("-", " ")
        if gloss.startswith("FS_") and len(gloss) == 4:
            search_term = gloss[3].lower()

        print(f"⚠️ Gloss '{gloss}' not in local lexicon. Fetching on demand ('{search_term}')...")
        try:
            encoded = urllib.parse.quote(search_term)
            url = f"https://us-central1-sign-mt.cloudfunctions.net/spoken_text_to_signed_pose?text={encoded}&spoken=en&signed=ase"
            req = urllib.request.Request(url, headers={"User-Agent": "SilentVoiceBridge/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            pose_file.write_bytes(data)
            pose = Pose.read(data)
            self.cache[gloss] = pose
            print(f"✓ Cached new gloss '{gloss}' to local lexicon ({len(pose.body.data)} frames)")
            return pose
        except Exception as e:
            print(f"❌ Failed to fetch fallback pose for '{gloss}': {e}")
            return None

    def synthesize(
        self,
        text: str,
        transition_frames: int = 10,
        hold_frames: int = 4,
        target_fps: float = 25.0
    ) -> SynthesizedSign:
        """
        Translates an English sentence into a continuous, fluid ASL sign animation.
        """
        # 1. English NLP to ASL Gloss
        glosses, details = translate_english_to_gloss(text)
        if not glosses:
            glosses = ["HELLO"]

        # 2. Retrieve pose clips for each gloss
        clips = []
        for g in glosses:
            p = self.get_pose_for_gloss(g)
            if p is not None:
                clips.append((g, p))
            else:
                # If sign completely unavailable, try fingerspelling its letters
                print(f"⚠️ Skipping unavailable gloss: {g}")

        if not clips:
            raise RuntimeError(f"Could not synthesize any sign clips for text: '{text}'")

        # 3. Blend pose sequence with Cosine S-curve Spline
        blended_pose, timings = blend_pose_sequence(
            clips,
            transition_frames=transition_frames,
            hold_frames=hold_frames,
            target_fps=target_fps
        )

        return SynthesizedSign(
            english_text=text,
            glosses=glosses,
            details=details,
            pose=blended_pose,
            timings=timings,
            total_frames=len(blended_pose.body.data),
            fps=target_fps
        )

    def render_to_frames(self, synthesized: SynthesizedSign, bg_color=(15, 15, 15)) -> List[np.ndarray]:
        """Renders the synthesized skeleton with high-definition PoseVisualizer."""
        visualizer = PoseVisualizer(synthesized.pose)
        raw_frames = list(visualizer.draw(background_color=bg_color))

        annotated_frames = []
        total = len(raw_frames)

        for f_idx, raw_f in enumerate(raw_frames):
            frame = raw_f.copy()
            h, w = frame.shape[:2]

            # Find active gloss for this frame
            active_gloss = "TRANSITION"
            for t in synthesized.timings:
                if t["start_frame"] <= f_idx < t["end_frame"]:
                    active_gloss = t["gloss"]
                    break

            # Top overlay banner
            cv2.rectangle(frame, (0, 0), (w, 75), (20, 20, 20), -1)
            cv2.putText(frame, f"ENGLISH: \"{synthesized.english_text}\"", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

            # Highlight gloss
            is_trans = "TRANSITION" in active_gloss
            gloss_color = (180, 180, 180) if is_trans else (50, 230, 50)
            cv2.putText(frame, f"CURRENT SIGN: {active_gloss}", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, gloss_color, 2, cv2.LINE_AA)

            # Bottom info bar
            cv2.rectangle(frame, (0, h - 40), (w, h), (15, 15, 15), -1)
            gloss_chain = "  ->  ".join([f"[{g}]" for g in synthesized.glosses])
            cv2.putText(frame, f"GLOSSES: {gloss_chain}", (20, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 220, 255), 1, cv2.LINE_AA)

            annotated_frames.append(frame)

        return annotated_frames

    def export_to_video(self, synthesized: SynthesizedSign, output_path: str, fps: float = 25.0) -> Path:
        """Renders and saves the synthesized sign animation as an MP4 video."""
        frames = self.render_to_frames(synthesized)
        if not frames:
            raise RuntimeError("No frames rendered")

        h, w = frames[0].shape[:2]
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        # Write raw mp4v first
        temp_file = out_file.with_suffix(".tmp.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(temp_file), fourcc, fps, (w, h))

        for f in frames:
            writer.write(f)
        writer.release()

        # Convert to universal H.264 with yuv420p via ffmpeg if available
        import shutil
        import subprocess

        ffmpeg_bin = shutil.which("ffmpeg")
        if ffmpeg_bin:
            cmd = [
                ffmpeg_bin, "-y",
                "-i", str(temp_file),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(out_file)
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                if temp_file.exists():
                    temp_file.rename(out_file)
        else:
            if temp_file.exists():
                temp_file.rename(out_file)

        print(f"✓ Video saved to: {out_file} ({len(frames)} frames @ {fps} fps)")
        return out_file


if __name__ == "__main__":
    synth = ASLSynthesizer()
    test_phrase = "What is your name?"
    print(f"\nSynthesizing: \"{test_phrase}\"")
    result = synth.synthesize(test_phrase)
    print(f"✓ Glosses: {result.glosses}")
    print(f"✓ Total Frames: {result.total_frames} @ {result.fps} FPS")
    for t in result.timings:
        print(f"   [{t['start_frame']:3d} - {t['end_frame']:3d}] {t['gloss']}")
