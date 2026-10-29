import { clonePose, clipDurationMs, sampleClip, validateClip } from './pose.js';

/** Frame-rate-independent timeline controller. Never edits source sign motion. */
export class AnimationPlayer {
  constructor(clip) {
    this.clip = validateClip(clip);
    this.playheadMs = 0;
    this.playing = false;
    this.loop = true;
    this.speed = 1;
  }
  load(clip) {
    this.clip = validateClip(clip);
    this.playheadMs = 0;
    this.playing = false;
  }
  seek(timeMs) {
    if (!Number.isFinite(timeMs)) throw new Error('Seek time must be finite');
    this.playheadMs = Math.min(Math.max(timeMs, 0), clipDurationMs(this.clip));
    return this.currentPose();
  }
  currentPose() { return sampleClip(this.clip, this.playheadMs); }
  tick(deltaMs) {
    if (this.playing) {
      const duration = clipDurationMs(this.clip);
      if (duration === 0) { this.playing = false; return clonePose(this.clip.keyframes[0].pose); }
      let future = this.playheadMs + Math.max(0, deltaMs) * this.speed;
      if (future >= duration) {
        if (this.loop) future = future % duration;
        else { future = duration; this.playing = false; }
      }
      this.playheadMs = future;
    }
    return this.currentPose();
  }
}
