"""
Silent Voice Bridge v2 - Workstream A: Canonical Palm-Space Feature Normalizer
Conforms to Section 4.1: Feature tensor of shape (30, 68) per sign:
- 30 resampled time steps
- 68 features per step in canonical palm space (invariant to camera distance & tilt)

Features (68 dims):
- Dominant Hand (Right or Primary): 21 landmarks x 2 (normalized relative to palm base and scale) = 42
- Secondary Hand (Left or Offhand): 21 landmarks x 2 (relative to primary palm) = 42 (reduced to 21 key palm/tip points x 2 = 20)
- Relative Hand Distance & Torso anchoring:
  - Inter-wrist dx, dy, dz (3)
  - Dominant wrist relative to nose/shoulder mid (3)
Total vector = 68 dimensions.
"""

import numpy as np

NUM_RESAMPLED_FRAMES = 30
FEATURE_DIM = 68

def normalize_landmarks_frame(hand_results, pose_results):
    """
    Extracts a 68-dimensional normalized canonical feature vector for a single frame.
    Handles 1-hand and 2-hand signs (like HOW-ARE-YOU, HELP, HELLO).
    """
    feat = np.zeros(FEATURE_DIM, dtype=np.float32)

    # 1. Pose anchor (Mid-shoulder or nose)
    pose_anchor = np.array([0.5, 0.5, 0.0], dtype=np.float32)
    shoulder_width = 0.3
    if pose_results and pose_results.pose_landmarks and len(pose_results.pose_landmarks) > 0:
        lm = pose_results.pose_landmarks[0]
        # Shoulders 11 and 12
        if len(lm) > 12:
            left_sh = np.array([lm[11].x, lm[11].y, lm[11].z])
            right_sh = np.array([lm[12].x, lm[12].y, lm[12].z])
            pose_anchor = (left_sh + right_sh) / 2.0
            dist = np.linalg.norm(left_sh[:2] - right_sh[:2])
            if dist > 0.05:
                shoulder_width = float(dist)

    # 2. Hands extraction
    hands_by_side = {"Left": None, "Right": None}
    if hand_results and hand_results.hand_landmarks:
        for idx, lm_set in enumerate(hand_results.hand_landmarks):
            label = "Right"
            if idx < len(hand_results.handedness):
                label = hand_results.handedness[idx][0].category_name
            
            coords = np.array([[lm.x, lm.y, lm.z] for lm in lm_set], dtype=np.float32)
            if hands_by_side[label] is None:
                hands_by_side[label] = coords
            else:
                # If duplicate label, assign by x-coordinate (left of screen vs right)
                other_label = "Left" if label == "Right" else "Right"
                if hands_by_side[other_label] is None:
                    hands_by_side[other_label] = coords

    # Primary hand (Right hand if present, otherwise Left)
    primary = hands_by_side["Right"] if hands_by_side["Right"] is not None else hands_by_side["Left"]
    secondary = hands_by_side["Left"] if hands_by_side["Right"] is not None else None

    # Dominant hand normalization:
    # Origin at wrist (idx 0), scale normalized by palm length (wrist to middle MCP idx 9)
    if primary is not None:
        wrist = primary[0]
        middle_mcp = primary[9]
        palm_scale = np.linalg.norm(middle_mcp[:2] - wrist[:2])
        if palm_scale < 1e-4:
            palm_scale = 0.1

        # 21 landmarks x 2 (x, y) = 42 features
        norm_primary = (primary[:, :2] - wrist[:2]) / palm_scale
        feat[0:42] = norm_primary.flatten()

        # Dominant wrist relative to torso pose anchor (scaled by shoulder width)
        rel_wrist = (wrist - pose_anchor) / shoulder_width
        feat[42:45] = rel_wrist

    # Secondary hand (crucial for 2-handed signs like HOW-ARE-YOU):
    if secondary is not None and primary is not None:
        # Distance from primary wrist
        wrist_dist = (secondary[0] - primary[0]) / shoulder_width
        feat[45:48] = wrist_dist

        # 10 key landmarks of secondary hand (wrist, 5 fingertips, 4 MCPs) x 2 = 20 dims
        key_indices = [0, 4, 8, 12, 16, 20, 5, 9, 13, 17]
        sec_wrist = secondary[0]
        sec_scale = np.linalg.norm(secondary[9][:2] - sec_wrist[:2])
        if sec_scale < 1e-4:
            sec_scale = 0.1
        norm_sec = (secondary[key_indices, :2] - sec_wrist[:2]) / sec_scale
        feat[48:68] = norm_sec.flatten()
    elif secondary is not None:
        # Only secondary hand exists
        sec_wrist = secondary[0]
        sec_scale = np.linalg.norm(secondary[9][:2] - sec_wrist[:2])
        if sec_scale < 1e-4:
            sec_scale = 0.1
        norm_sec = (secondary[:, :2] - sec_wrist[:2]) / sec_scale
        feat[0:42] = norm_sec.flatten()
        feat[42:45] = (sec_wrist - pose_anchor) / shoulder_width

    return feat


# Raw landmark layout for avatar playback (Section 4.2 "avatar_frames_file"):
#   rows 0-32  : pose (33 MediaPipe body points)
#   rows 33-53 : left hand (21 points)
#   rows 54-74 : right hand (21 points)
# Each row is (x, y, z) in normalized image coords. Missing parts are NaN.
RAW_POSE_SLICE = slice(0, 33)
RAW_LEFT_SLICE = slice(33, 54)
RAW_RIGHT_SLICE = slice(54, 75)
RAW_NUM_POINTS = 75


def extract_raw_landmarks(hand_results, pose_results):
    """Returns a (75, 3) array of raw landmarks for avatar replay."""
    raw = np.full((RAW_NUM_POINTS, 3), np.nan, dtype=np.float32)

    if pose_results and pose_results.pose_landmarks and len(pose_results.pose_landmarks) > 0:
        lm = pose_results.pose_landmarks[0]
        raw[RAW_POSE_SLICE] = np.array([[p.x, p.y, p.z] for p in lm[:33]], dtype=np.float32)

    if hand_results and hand_results.hand_landmarks:
        filled = {"Left": False, "Right": False}
        for idx, lm_set in enumerate(hand_results.hand_landmarks):
            label = "Right"
            if idx < len(hand_results.handedness):
                label = hand_results.handedness[idx][0].category_name
            if filled[label]:
                label = "Left" if label == "Right" else "Right"
                if filled[label]:
                    continue
            coords = np.array([[p.x, p.y, p.z] for p in lm_set], dtype=np.float32)
            raw[RAW_LEFT_SLICE if label == "Left" else RAW_RIGHT_SLICE] = coords
            filled[label] = True

    return raw


def resample_sequence(sequence, target_len=NUM_RESAMPLED_FRAMES):
    """
    Interpolates any captured sequence of arbitrary frame count into exactly target_len (30) steps.
    Resulting shape: (30, 68)
    """
    arr = np.array(sequence, dtype=np.float32)
    orig_len = len(arr)
    if orig_len == target_len:
        return arr
    if orig_len == 0:
        return np.zeros((target_len, FEATURE_DIM), dtype=np.float32)
    if orig_len == 1:
        return np.repeat(arr, target_len, axis=0)

    orig_indices = np.linspace(0, orig_len - 1, orig_len)
    new_indices = np.linspace(0, orig_len - 1, target_len)
    resampled = np.zeros((target_len, FEATURE_DIM), dtype=np.float32)
    for dim in range(FEATURE_DIM):
        resampled[:, dim] = np.interp(new_indices, orig_indices, arr[:, dim])
    return resampled
