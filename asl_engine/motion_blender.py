"""
Silent Voice Bridge v2 - Motion Blender & S-Curve Spline Interpolator
Part of the Workstream B Engine.

Features:
- Takes any list of ASL sign clips (either `Pose` objects or numpy arrays).
- Blends consecutive signs with C2-continuous Cosine S-curve interpolation.
- Inserts holding frames at sign apex for visual readability.
- Returns a unified, seamless continuous motion clip with frame-accurate timing tracks.
"""

from typing import List, Dict, Tuple
import numpy as np
from pose_format import Pose
from pose_format.numpy.pose_body import NumPyPoseBody


def generate_spline_transition_data(
    frame_a: np.ma.MaskedArray,
    frame_b: np.ma.MaskedArray,
    num_transition_frames: int = 10
) -> np.ma.MaskedArray:
    """
    Interpolates between two landmark frames using Cosine S-curve easing:
    alpha(t) = 0.5 - 0.5 * cos(pi * t)
    Ensures zero acceleration/velocity at the endpoints for smooth co-articulation.
    frame_a, frame_b shape: (1, NumPoints, Dims)
    """
    shape = (num_transition_frames,) + frame_a.shape
    transition_data = np.zeros(shape, dtype=np.float32)

    for i in range(num_transition_frames):
        t = (i + 1) / (num_transition_frames + 1)
        alpha = 0.5 - 0.5 * np.cos(np.pi * t)
        transition_data[i] = (1.0 - alpha) * frame_a + alpha * frame_b

    # Preserve masked properties
    mask = np.logical_or(
        np.repeat(frame_a.mask[np.newaxis, ...], num_transition_frames, axis=0),
        np.repeat(frame_b.mask[np.newaxis, ...], num_transition_frames, axis=0)
    )
    return np.ma.masked_array(transition_data, mask=mask)


def generate_spline_transition_confidence(
    conf_a: np.ndarray,
    conf_b: np.ndarray,
    num_transition_frames: int = 10
) -> np.ndarray:
    """Interpolates confidence values between two frames."""
    shape = (num_transition_frames,) + conf_a.shape
    transition_conf = np.zeros(shape, dtype=np.float32)

    for i in range(num_transition_frames):
        t = (i + 1) / (num_transition_frames + 1)
        alpha = 0.5 - 0.5 * np.cos(np.pi * t)
        transition_conf[i] = (1.0 - alpha) * conf_a + alpha * conf_b

    return transition_conf


def blend_pose_sequence(
    pose_clips: List[Tuple[str, Pose]],
    transition_frames: int = 10,
    hold_frames: int = 4,
    target_fps: float = 25.0
) -> Tuple[Pose, List[Dict]]:
    """
    Blends a sequence of named ASL sign poses into one smooth, continuous Pose animation.
    
    Args:
        pose_clips: List of tuples (gloss_name, Pose)
        transition_frames: Number of S-curve frames between consecutive signs (default: 10 frames = 0.4s)
        hold_frames: Number of frames to hold the final sign apex for legibility (default: 4 frames)
        target_fps: Standard FPS output (default: 25.0)

    Returns:
        (blended_pose, timing_tracks)
        where timing_tracks is a list of dicts:
        [{"gloss": "YOUR", "start_frame": 0, "end_frame": 85}, ...]
    """
    if not pose_clips:
        raise ValueError("Cannot blend empty pose list")

    if len(pose_clips) == 1:
        gloss, pose = pose_clips[0]
        timings = [{
            "gloss": gloss,
            "start_frame": 0,
            "end_frame": len(pose.body.data),
            "is_transition": False
        }]
        return pose, timings

    header = pose_clips[0][1].header
    data_list = []
    conf_list = []
    timing_tracks = []
    current_frame = 0

    for idx, (gloss, pose) in enumerate(pose_clips):
        # 1. Add current sign frames
        clip_data = pose.body.data
        clip_conf = pose.body.confidence
        clip_len = len(clip_data)

        start_f = current_frame
        data_list.append(clip_data)
        conf_list.append(clip_conf)
        current_frame += clip_len

        # 2. Add hold frames at apex (skip extra hold if this is a static fingerspell letter)
        actual_hold = 0 if gloss.startswith("FS_") else hold_frames
        if actual_hold > 0:
            hold_data = np.repeat(clip_data[-1:], actual_hold, axis=0)
            hold_conf = np.repeat(clip_conf[-1:], actual_hold, axis=0)
            data_list.append(hold_data)
            conf_list.append(hold_conf)
            current_frame += actual_hold

        end_f = current_frame
        timing_tracks.append({
            "gloss": gloss,
            "start_frame": start_f,
            "end_frame": end_f,
            "is_transition": False
        })

        # 3. Add spline transition to next sign (if not last)
        if idx < len(pose_clips) - 1:
            next_gloss, next_pose = pose_clips[idx + 1]
            frame_a = clip_data[-1]
            frame_b = next_pose.body.data[0]
            conf_a = clip_conf[-1]
            conf_b = next_pose.body.confidence[0]

            # Fast crisp transition between letters (6 frames), standard for words (10 frames)
            is_letter_to_letter = gloss.startswith("FS_") and next_gloss.startswith("FS_")
            actual_trans = 6 if is_letter_to_letter else transition_frames

            trans_data = generate_spline_transition_data(frame_a, frame_b, num_transition_frames=actual_trans)
            trans_conf = generate_spline_transition_confidence(conf_a, conf_b, num_transition_frames=actual_trans)

            trans_start = current_frame
            data_list.append(trans_data)
            conf_list.append(trans_conf)
            current_frame += actual_trans
            trans_end = current_frame

            timing_tracks.append({
                "gloss": f"TRANSITION ({gloss} -> {pose_clips[idx + 1][0]})",
                "start_frame": trans_start,
                "end_frame": trans_end,
                "is_transition": True
            })

    # Concatenate all frames along time dimension (axis 0)
    final_data = np.ma.concatenate(data_list, axis=0)
    final_conf = np.concatenate(conf_list, axis=0)

    blended_body = NumPyPoseBody(fps=target_fps, data=final_data, confidence=final_conf)
    blended_pose = Pose(header=header, body=blended_body)

    return blended_pose, timing_tracks
