"""
Silent Voice Bridge v2 - Adaptive Kinetic Energy Segmenter
Task: Detect sign start, apex, finish from hand and arm velocities.

State Machine:
1. IDLE: Hand velocity is below START_THRESHOLD (waiting for movement).
2. SIGNING: Hand velocity spiked above START_THRESHOLD. Recording landmark trajectory.
3. FINISHED: Velocity drops below STOP_THRESHOLD for consecutive frames (or max duration reached).
   Emits the isolated sign trajectory, cleanly cropped from start to finish!
"""

import numpy as np
import time

class KineticSegmenter:
    def __init__(self, start_vel=0.018, stop_vel=0.009, min_frames=12, max_frames=65, stop_patience=6):
        self.start_vel = start_vel
        self.stop_vel = stop_vel
        self.min_frames = min_frames
        self.max_frames = max_frames
        self.stop_patience = stop_patience

        self.state = "IDLE"  # "IDLE" or "SIGNING"
        self.current_trajectory = []
        self.prev_positions = []
        self.low_vel_counter = 0

    def compute_instantaneous_velocity(self, hand_results):
        """Calculates normalized velocity across all visible hand landmarks."""
        if not hand_results or not hand_results.hand_landmarks:
            return 0.0

        current_pts = []
        for hand in hand_results.hand_landmarks:
            for idx in [0, 4, 8, 12, 16, 20]:  # Wrist + 5 fingertips
                current_pts.append([hand[idx].x, hand[idx].y])

        current_pts = np.array(current_pts, dtype=np.float32)

        if len(self.prev_positions) == 0 or len(self.prev_positions) != len(current_pts):
            self.prev_positions = current_pts
            return 0.0

        # Mean displacement of finger tips & wrist
        disp = np.linalg.norm(current_pts - self.prev_positions, axis=1)
        velocity = float(np.mean(disp))
        self.prev_positions = current_pts
        return velocity

    def update(self, hand_results, feature_vector):
        """
        Updates segmenter with current frame.
        Returns:
            isolated_sign_trajectory (list of features) if a sign just finished, else None.
        """
        vel = self.compute_instantaneous_velocity(hand_results)
        has_hands = hand_results and hand_results.hand_landmarks and len(hand_results.hand_landmarks) > 0

        completed_sign = None

        if self.state == "IDLE":
            if has_hands and vel >= self.start_vel:
                self.state = "SIGNING"
                self.current_trajectory = [feature_vector]
                self.low_vel_counter = 0

        elif self.state == "SIGNING":
            self.current_trajectory.append(feature_vector)

            # Check if motion has slowed down (sign apex passed, hand settling)
            if vel <= self.stop_vel or not has_hands:
                self.low_vel_counter += 1
            else:
                self.low_vel_counter = 0

            # Sign is completed when stopped moving for stop_patience frames, or hit max_frames
            if (self.low_vel_counter >= self.stop_patience and len(self.current_trajectory) >= self.min_frames) \
               or len(self.current_trajectory) >= self.max_frames:
                
                # Emit clean trajectory (pruning trailing resting frames)
                prune_len = max(self.min_frames, len(self.current_trajectory) - self.low_vel_counter)
                completed_sign = self.current_trajectory[:prune_len]
                
                # Reset
                self.state = "IDLE"
                self.current_trajectory = []
                self.low_vel_counter = 0

            elif len(self.current_trajectory) < self.min_frames and self.low_vel_counter >= self.stop_patience:
                # Discard false start (too short / jitter)
                self.state = "IDLE"
                self.current_trajectory = []
                self.low_vel_counter = 0

        return completed_sign, self.state, vel
