/**
 * Per-frame 3D joint positions after source-dataset forward kinematics.
 * This is deliberately not an SMPL-X parser and not the recognition (30,68) tensor.
 */
export const POSITIONS_SCHEMA = 'svb.avatar.positions.v1';
export const BODY_KEYS = Object.freeze(['left_shoulder', 'left_elbow', 'left_wrist', 'right_shoulder', 'right_elbow', 'right_wrist']);
export const HAND_EDGES = Object.freeze([
  [0,1],[1,2],[2,3],[3,4], [0,5],[5,6],[6,7],[7,8],
  [0,9],[9,10],[10,11],[11,12], [0,13],[13,14],[14,15],[15,16],
  [0,17],[17,18],[18,19],[19,20], [5,9],[9,13],[13,17],
]);
const clone = (v) => JSON.parse(JSON.stringify(v));
const err = (msg) => {throw new Error(msg)};
const vec3 = (v, path) => {
  if (!Array.isArray(v) || v.length!==3 || !v.every(n=>typeof n==='number' && Number.isFinite(n) && Math.abs(n)<100)) err(`${path} must be [x,y,z] finite coordinates`);
};
export function validatePositionFrame(frame) {
  if (!frame || typeof frame!=='object' || Array.isArray(frame)) err('frame must be an object');
  for (const key of BODY_KEYS) vec3(frame[key], `frame.${key}`);
  for (const side of ['left','right']) {
    const hand=frame[`${side}_hand`];
    if (!Array.isArray(hand) || hand.length!==21) err(`${side}_hand must contain 21 points in MediaPipe hand landmark order`);
    hand.forEach((p,i)=>vec3(p,`${side}_hand[${i}]`));
    // wrist anchor continuity is required so the hand is attached to the arm.
    const wrist=frame[`${side}_wrist`];
    if (Math.hypot(...hand[0].map((v,i)=>v-wrist[i]))>0.10) err(`${side} hand[0] must match wrist within 0.10 m`);
  }
  return frame;
}
export function validatePositionClip(clip) {
  if (!clip || typeof clip!=='object') err('Clip must be an object');
  if (clip.schema!==POSITIONS_SCHEMA) err(`Expected ${POSITIONS_SCHEMA}`);
  if (typeof clip.label!=='string' || !/^[A-Za-z0-9_\-]{1,100}$/.test(clip.label)) err('label must be 1-100 letters, digits, hyphens or underscores');
  if (clip.coordinate_system!=='threejs_world_m') err('Expected coordinate_system threejs_world_m');
  if (clip.units!=='meters') err('Expected units meters');
  if (!Array.isArray(clip.frames)||clip.frames.length<1||clip.frames.length>10000)err('Expected 1-10000 frames');
  let prev=-1;
  for (const [i,kf] of clip.frames.entries()) {
    if (!kf || typeof kf!=='object'||!Number.isInteger(kf.time_ms)||kf.time_ms<=prev||kf.time_ms>600000)err(`Invalid or unordered frames[${i}].time_ms`);
    if (i===0 && kf.time_ms!==0)err('First frame must begin at 0 ms');
    validatePositionFrame(kf.joints);
    prev=kf.time_ms;
  }
  return clip;
}
export function positionDurationMs(clip){return clip.frames.at(-1).time_ms;}
export function lerpPositionFrame(a,b,t){
  const mix=(u,v)=>u+(v-u)*t;
  const result={};
  for (const key of BODY_KEYS) result[key]=a[key].map((v,i)=>mix(v,b[key][i]));
  for (const side of ['left','right'])result[`${side}_hand`]=a[`${side}_hand`].map((point,i)=>point.map((v,j)=>mix(v,b[`${side}_hand`][i][j])));
  return result;
}
export function samplePositionClip(clip,ms){
  const fs=clip.frames;
  if(fs.length===1 || ms<=0)return clone(fs[0].joints);
  if(ms>=positionDurationMs(clip))return clone(fs.at(-1).joints);
  let lo=0,hi=fs.length-1;
  while(hi-lo>1){const m=(hi+lo)>>1;if(fs[m].time_ms<=ms)lo=m;else hi=m;}
  const a=fs[lo],b=fs[hi],t=(ms-a.time_ms)/(b.time_ms-a.time_ms);
  // Linear, not smoothstep, to avoid artificial stops at every recorded video frame.
  return lerpPositionFrame(a.joints,b.joints,t);
}
export class PositionPlayer {
  constructor(clip){this.load(clip);this.loop=true;this.speed=1;}
  load(clip){this.clip=validatePositionClip(clip);this.playheadMs=0;this.playing=false;}
  seek(ms){if(!Number.isFinite(ms))err('Non-finite seek');this.playheadMs=Math.max(0,Math.min(ms,positionDurationMs(this.clip)));return this.current();}
  current(){return samplePositionClip(this.clip,this.playheadMs);}
  tick(dt){
    if(this.playing){let next=this.playheadMs+Math.max(0,dt)*this.speed;const d=positionDurationMs(this.clip);
      if(!d){this.playing=false;}else if(next>=d){if(this.loop)next%=d;else{next=d;this.playing=false;}}
      this.playheadMs=next;
    }
    return this.current();
  }
}
/** A synthetic motion demonstrating import/playback. NOT an ASL word. */
export function demoPositionClip(){
  const wristOffset=(side,factor)=>{
    const s=side==='left'?1:-1;
    return [s*(0.48-0.10*factor),0.88+0.27*factor,0.07+0.10*factor];
  };
  const makeHand=(w,s,bend)=>{
    const hand=Array.from({length:21},()=>[...w]);
    const segments=[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16],[17,18,19,20]];
    const offsets=[-.063,-.035,-.004,.025,.052];
    for(let f=0;f<5;f++){
      const ids=segments[f], x=offsets[f]*s;
      ids.forEach((id,j)=>{
        const t=(j+1)/4, curled=bend*(f===1?0.25:1);
        hand[id]=[w[0]+x*(.5+.5*t)+s*.012*t,w[1]-.09-.23*t+curled*.15*t*t,w[2]+curled*.10*t];
      });
    }
    return hand;
  };
  const make=(t)=>{
    const b=(1-Math.cos(t*Math.PI*2))/2;
    const result={};
    for(const side of ['left','right']){
      const s=side==='left'?1:-1;
      result[`${side}_shoulder`]=[s*.305,1.54,0];
      result[`${side}_elbow`]=[s*(.38-.035*b),1.23+.12*b,.03];
      const w=wristOffset(side,b);
      result[`${side}_wrist`]=w;
      result[`${side}_hand`]=makeHand(w,s,b);
    }
    return result;
  };
  return validatePositionClip({schema:POSITIONS_SCHEMA,label:'SYNTHETIC_POSITION_TEST',coordinate_system:'threejs_world_m',units:'meters',source:'synthetic_test_not_ASL',verified_by_asl_reviewer:false,
    frames:Array.from({length:49},(_,i)=>({time_ms:i*50,joints:make(i/48)}))});
}
