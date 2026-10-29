#!/usr/bin/env python3
"""Convert *already reconstructed* world-space skeleton positions to SVB JSON.

This does NOT decode raw ASL3DWord/SMPL-X rotations. First use an authorized
SMPL-X forward-kinematics pipeline to obtain (in meters, with agreed axes):

- body_points: (T,6,3) anatomical left shoulder/elbow/wrist then right equivalent
- hand_points: (T,2,21,3) left and right MediaPipe hand landmark index order
- optional times_ms: (T,) relative timestamps beginning at zero

If absent, timestamps are created from --fps. Requires numpy only.
No resampling, smoothing, filtering, scaling, or left/right swapping is done.

Windows example:
 python tools/positions_npz_to_json.py input.npz output.json --label HELLO --fps 30
"""
import argparse
import json
from pathlib import Path
import numpy as np

BODY=['left_shoulder','left_elbow','left_wrist','right_shoulder','right_elbow','right_wrist']


def convert(src: Path, label: str, fps: float):
    if not (0 < fps <= 240):raise ValueError('fps must be between 0 and 240')
    with np.load(src, allow_pickle=False) as obj:
        if 'body_points' not in obj or 'hand_points' not in obj:raise ValueError('Require body_points and hand_points arrays')
        body=np.asarray(obj['body_points'],dtype=np.float64)
        hands=np.asarray(obj['hand_points'],dtype=np.float64)
        if body.ndim!=3 or body.shape[1:]!=(6,3):raise ValueError(f'body_points shape {body.shape}; expected (T,6,3)')
        if hands.ndim!=4 or hands.shape[1:]!=(2,21,3):raise ValueError(f'hand_points shape {hands.shape}; expected (T,2,21,3)')
        n=len(body)
        if n==0 or n!=len(hands) or n>10000:raise ValueError('Require 1-10000 matching frames')
        if not np.isfinite(body).all() or not np.isfinite(hands).all():raise ValueError('NaN/Infinity in coordinates')
        if np.max(np.abs(body))>100 or np.max(np.abs(hands))>100:raise ValueError('Coordinates are unexpectedly large; expected meters')
        if 'times_ms' in obj:
            times=np.asarray(obj['times_ms'],dtype=np.float64)
            if times.shape!=(n,) or not np.isfinite(times).all():raise ValueError('Invalid times_ms')
            times=times-times[0]
            if not np.all(np.diff(times)>0):raise ValueError('timestamps must be strictly increasing')
            times=np.rint(times).astype(int)
        else:times=np.rint(np.arange(n)/fps*1000).astype(int)
    if len(np.unique(times))!=n:raise ValueError('Timestamps collided after rounding')
    if times[-1]>600000:raise ValueError('Clip duration > 10 minutes')
    if not np.all(np.linalg.norm(hands[:,:,0,:]-body[:,[2,5],:],axis=-1)<=.10):
        raise ValueError('hand landmark 0 must be within 10 cm of body wrist. Verify axes, units and joint mapping.')
    frames=[]
    for t in range(n):
        joints={key: body[t,i].tolist() for i,key in enumerate(BODY)}
        joints['left_hand']=hands[t,0].tolist();joints['right_hand']=hands[t,1].tolist()
        frames.append({'time_ms':int(times[t]),'joints':joints})
    return {'schema':'svb.avatar.positions.v1','label':label,'coordinate_system':'threejs_world_m','units':'meters',
            'source':'external_reconstructed_skeleton','verified_by_asl_reviewer':False,
            'notes':'Unreviewed automatic conversion; source skeleton MUST already have been reconstructed and aligned to Three.js.',
            'frames':frames}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input_npz',type=Path)
    ap.add_argument('output_json',type=Path)
    ap.add_argument('--label',required=True,help='Sign gloss in uppercase, e.g., HELLO')
    ap.add_argument('--fps',type=float,default=30)
    args=ap.parse_args()
    if not args.input_npz.is_file():ap.error(f'File not found: {args.input_npz}')
    if not args.label.replace('_','').replace('-','').isalnum() or len(args.label)>100:ap.error('Invalid label')
    try:clip=convert(args.input_npz,args.label,args.fps)
    except (ValueError,KeyError) as e:ap.error(str(e))
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    args.output_json.write_text(json.dumps(clip,separators=(',',':')),encoding='utf-8')
    print(f'Saved {len(clip["frames"])} frames -> {args.output_json}')
    print('Reminder: geometry and sign correctness have not been validated.')

if __name__=='__main__':main()
