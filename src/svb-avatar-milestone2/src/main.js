import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import './styles.css';
import { AvatarRig, MEDIAPIPE_HAND_LABELS } from './rig.js';
import {
  ANIMATION_SCHEMA, POSE_SCHEMA, FINGERS, SIDES, clonePose,
  neutralPose, presetPose, demonstrationWave, singlePoseClip,
  validatePose, validateClip, clipDurationMs,
} from './pose.js';
import { AnimationPlayer } from './player.js';
import { PositionRig } from './positionRig.js';
import { POSITIONS_SCHEMA, PositionPlayer, demoPositionClip, validatePositionClip, positionDurationMs } from './positionClip.js';

const $ = (id) => document.getElementById(id);
const status = (message, isError = false) => { $('status').textContent = message; $('status').classList.toggle('error', isError); };
const host = $('canvas-host');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({antialias:true, alpha:false, powerPreference:'high-performance'});
} catch (error) {
  $('render-error').hidden = false;
  $('render-error').textContent = `WebGL renderer failed: ${error.message}. Try Chrome/Edge with hardware acceleration enabled.`;
  throw error;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(host.clientWidth || 640, host.clientHeight || 450);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.23;
renderer.domElement.setAttribute('aria-label','Interactive 3D articulated skeleton');
host.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0c1426);
scene.fog = new THREE.FogExp2(0x0c1426, .075);
const camera = new THREE.PerspectiveCamera(43, 1, .04, 50);
camera.position.set(0.06, 1.55, 3.20);
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.set(0, 1.34, 0);
orbit.enableDamping = true;
orbit.dampingFactor = .07;
orbit.minDistance = 1.3;
orbit.maxDistance = 7;
orbit.maxPolarAngle = Math.PI * .90;
orbit.update();
scene.add(new THREE.HemisphereLight(0xdbeafe,0x202d49,2.2));
const keyLight = new THREE.DirectionalLight(0xffffff,3.0);
keyLight.position.set(2.8,5,5);
scene.add(keyLight);
const backLight = new THREE.DirectionalLight(0x38bdf8,1.5);
backLight.position.set(-4,2,-3);
scene.add(backLight);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(13,13), new THREE.MeshStandardMaterial({color:0x0e1c2d,roughness:.93}));
floor.rotation.x = -Math.PI / 2;
floor.position.y = .27;
scene.add(floor);
const grid = new THREE.GridHelper(10,32,0x30496b,0x1e324e);
grid.position.y = .278;
grid.material.transparent = true;
grid.material.opacity = .55;
scene.add(grid);
const rig = new AvatarRig(scene);
const positionRig = new PositionRig(scene);
let positionPlayer = null;
let motionMode = 'angle';
function setMotionMode(mode) {
  motionMode=mode; rig.root.visible=(mode==='angle');positionRig.show(mode==='position');
  $('motion-type').textContent = mode==='position'?'3D JOINT POSITIONS':'JOINT ANGLES';
  $('motion-banner').textContent = mode==='position' ? 'DIRECT POSITIONS · ORIGINAL ANGLE CONTROLS DISABLED' : 'ANGLE CONTROLS ENABLED';
}
function loadPositionClip(clip) {
  positionPlayer=new PositionPlayer(validatePositionClip(clip));positionPlayer.loop=$('loop').checked;positionPlayer.speed=Number($('speed').value);
  setMotionMode('position');positionRig.applyFrame(positionPlayer.current());positionPlayer.playing=true;
  $('clip-name').textContent=clip.label;clipUi();
}
function backToAngleControls(){
  if(motionMode!=='angle'){setMotionMode('angle');player.playing=false;renderPose(pose);}
}

const player = new AnimationPlayer(demonstrationWave());
player.playing = true;
let pose = neutralPose();
let selectedSide = 'left';
let editing = false;
const clipUi = () => {
  const position = motionMode==='position';
  const target = position ? positionPlayer : player;
  const clip = target.clip;
  $('clip-name').textContent = clip.label;
  $('keyframe-info').textContent = position ? `3D positional motion · ${clip.frames.length} frames` : `${editing ? 'Custom animation' : 'Loaded animation'} · ${clip.keyframes.length} keyframe${clip.keyframes.length===1?'':'s'}`;
  const duration = position ? positionDurationMs(clip) : clipDurationMs(clip);
  $('timeline').max = Math.max(1,duration);
  $('timeline').value = target.playheadMs;
  $('time-label').textContent = `${(target.playheadMs / 1000).toFixed(2)} / ${(duration / 1000).toFixed(2)}s`;
  $('btn-play').textContent = target.playing ? 'Ⅱ Pause' : '▶ Play';
  $('btn-play').setAttribute('aria-label',target.playing ? 'Pause animation' : 'Play animation');
  $('btn-play').disabled = duration === 0;
};
const renderPose = (p, updateUi = true) => {
  pose = validatePose(p);
  rig.applyPose(pose);
  if (updateUi) syncControls();
};

const CONTROL_DEFS = [
  ['SHOULDER', [['shoulder.x','Forward / back',-150,150,1,'°'],['shoulder.y','Twist',-100,100,1,'°'],['shoulder.z','Raise / lower',-165,165,1,'°']]],
  ['ELBOW', [['elbow.flex','Bend',0,155,1,'°']]],
  ['WRIST', [['wrist.x','Pitch',-90,90,1,'°'],['wrist.y','Yaw',-90,90,1,'°'],['wrist.z','Roll',-90,90,1,'°']]],
  ['FINGERS', FINGERS.flatMap((finger) => [
    [`hand.${finger}.curl`,`${finger[0].toUpperCase()+finger.slice(1)} curl`,0,100,1,'%'],
    [`hand.${finger}.spread`,`${finger[0].toUpperCase()+finger.slice(1)} spread`,-100,100,1,'%'],
  ])],
];
const inputs = new Map();
for (const [heading, defs] of CONTROL_DEFS) {
  const section = document.createElement('div');
  section.className = 'joint-group';
  const title = document.createElement('h4'); title.textContent = heading;section.appendChild(title);
  for (const [path,label,min,max,step,suffix] of defs) {
    const wrapper = document.createElement('div'); wrapper.className = 'slider-group';
    const upper = document.createElement('div'); upper.className = 'slider-label';
    const text = document.createElement('label'); text.textContent = label;
    const value = document.createElement('output'); value.textContent = '0'+suffix;
    const input = document.createElement('input'); input.type = 'range';
    input.min = min; input.max = max; input.step = step; input.setAttribute('aria-label',label);
    input.id = 'control-'+path.replaceAll('.','-'); text.htmlFor = input.id;
    upper.append(text,value);wrapper.append(upper,input);section.appendChild(wrapper);
    inputs.set(path,{input,value,suffix});
    input.addEventListener('input', () => {
      backToAngleControls();
      player.playing = false;
      const keys = path.split('.');
      const target = pose.arms[selectedSide];
      let node = target;
      for (let i=0;i<keys.length-1;i++) node = node[keys[i]];
      const actual = (suffix === '%') ? Number(input.value) / 100 : Number(input.value);
      node[keys[keys.length-1]] = actual;
      value.textContent = `${input.value}${suffix}`;
      rig.applyPose(pose);
      clipUi();
      status('Manual joint pose active. Save pose or create a new animation to keep it.');
    });
  }
  $('joint-controls').appendChild(section);
}
function syncControls(){
  for(const [path,{input,value,suffix}] of inputs){
    let v=pose.arms[selectedSide];
    for(const key of path.split('.'))v=v[key];
    if(suffix === '%')v*=100;
    input.value = String(Math.round(v));
    value.textContent = `${Math.round(v)}${suffix}`;
  }
}
function setSide(side){
  if(!SIDES.includes(side))throw new Error('Invalid side');
  selectedSide=side;
  for(const s of SIDES){
    $('side-'+s).classList.toggle('active',s===side);
    $('side-'+s).setAttribute('aria-pressed',String(s===side));
  }
  syncControls();
}
for(const side of SIDES)$('side-'+side).addEventListener('click',()=>setSide(side));
for(const button of document.querySelectorAll('[data-preset]')){
  button.addEventListener('click',()=>{
    backToAngleControls();player.playing=false;
    renderPose(presetPose(button.dataset.preset));
    status(`${button.textContent.trim()} loaded as a test pose (not an ASL sign).`);
    clipUi();
  });
}
$('btn-demo').addEventListener('click',()=>{
  backToAngleControls();editing=false;
  player.load(demonstrationWave());player.playing=true;
  renderPose(player.currentPose());clipUi();
  status('Playing synthetic wave. This is for testing animation, not an ASL sign.');
});
$('btn-play').addEventListener('click',()=>{
  const target=motionMode==='position'?positionPlayer:player;
  if((motionMode==='position'?positionDurationMs(target.clip):clipDurationMs(target.clip))===0)return;
  target.playing=!target.playing;clipUi();
});
$('btn-restart').addEventListener('click',()=>{
  if(motionMode==='position')positionRig.applyFrame(positionPlayer.seek(0));
  else {player.seek(0);renderPose(player.currentPose());}
  clipUi();
});
$('timeline').addEventListener('input',()=>{
  if(motionMode==='position'){positionPlayer.playing=false;positionRig.applyFrame(positionPlayer.seek(Number($('timeline').value)));}
  else{player.playing=false;renderPose(player.seek(Number($('timeline').value)));}
  clipUi();
});
$('speed').addEventListener('change',()=>{player.speed=Number($('speed').value);if(positionPlayer)positionPlayer.speed=player.speed;});
$('loop').addEventListener('change',()=>{player.loop=$('loop').checked;if(positionPlayer)positionPlayer.loop=player.loop;});
$('markers').addEventListener('change',()=>{rig.setJointMarkersVisible($('markers').checked);positionRig.setJointMarkersVisible($('markers').checked);});
$('grid').addEventListener('change',()=>{grid.visible=$('grid').checked;});
$('btn-new-clip').addEventListener('click',()=>{
  backToAngleControls();player.load(singlePoseClip(pose,'CUSTOM_TEST_ANIMATION'));
  editing=true;
  $('frame-time').value='500';
  status('Custom animation created. Change joint sliders, enter a timestamp, then add a keyframe.');
  clipUi();
});
$('btn-add-frame').addEventListener('click',()=>{
  if(motionMode==='position'){status('Position animation is read-only here. Edit it using the Python converter or your source data.',true);return;}
  const t = Number($('frame-time').value);
  if(!Number.isInteger(t)||t<0||t>600000){status('Keyframe timestamp must be an integer from 0 to 600000 ms.',true);return;}
  try{
    if(!editing){
      player.load(singlePoseClip(pose,'CUSTOM_TEST_ANIMATION'));
      editing=true;
    }
    const kfs = player.clip.keyframes;
    const existing = kfs.findIndex(f=>f.time_ms===t);
    const frame={time_ms:t,pose:clonePose(pose)};
    if(existing>=0)kfs[existing]=frame; else kfs.push(frame);
    kfs.sort((a,b)=>a.time_ms-b.time_ms);
    validateClip(player.clip);
    player.seek(t);
    $('frame-time').value=String(t+500);
    status(`Saved keyframe at ${t} ms (${kfs.length} total).`);
    clipUi();
  }catch(error){status(`Could not save keyframe: ${error.message}`,true);}
});
const downloadJson = (fileName,obj) => {
  const blob = new Blob([JSON.stringify(obj,null,2)],{type:'application/json'});
  const url = URL.createObjectURL(blob);
  const link=document.createElement('a');link.href=url;link.download=fileName;
  document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
};
$('btn-save-pose').addEventListener('click',()=>{
  if(motionMode==='position'){status('Position animation does not have a v1 angle-pose. Use Export animation for the complete positions clip.',true);return;}
  downloadJson('avatar-pose-v1.json',pose);
  status('Exported current pose. Saved files remain on your computer.');
});
$('btn-export-clip').addEventListener('click',()=>{
  if(motionMode==='position')downloadJson('avatar-positions-v1.json',validatePositionClip(positionPlayer.clip));
  else downloadJson('avatar-animation-v1.json',validateClip(player.clip));
  status('Exported loaded animation. Manual slider edits require a saved keyframe to become part of this clip.');
});
$('btn-landmarks').addEventListener('click',()=>{
  if(motionMode==='position'){
    downloadJson('current-position-frame.json',{schema:'svb.avatar.position_snapshot.v1',source:positionPlayer.clip.source||'unspecified',label:positionPlayer.clip.label,time_ms:positionPlayer.playheadMs,joints:positionPlayer.current()});
    status('Exported the current 3D positional frame.');return;
  }
  const data={schema:'svb.avatar.joint_snapshot.v1',coordinate_system:'threejs_world',unit:'meters',
    mediapipe_hand_order:MEDIAPIPE_HAND_LABELS,
    hands:rig.getLandmarkPositions(),body:rig.getJointSummary(),
    note:'SYNTHETIC AVATAR JOINT POSITIONS - not detected MediaPipe measurements'};
  downloadJson('avatar-joints-snapshot.json',data);
  status('Exported 21 world-space joint positions per hand and shoulders/elbows/wrists.');
});
$('btn-import').addEventListener('click',()=>$('file-import').click());
$('file-import').addEventListener('change',async(event)=>{
  const file=event.target.files?.[0];
  if(!file)return;
  try{
    if(file.size>15*1024*1024)throw new Error('File exceeds 15 MB');
    const loaded=JSON.parse(await file.text());
    if(loaded.schema===POSITIONS_SCHEMA){
      loadPositionClip(loaded);status(`Loaded 3D positional animation: ${loaded.label} (${loaded.frames.length} frames).`);
    }else if(loaded.schema===POSE_SCHEMA){
      backToAngleControls();
      validatePose(loaded);player.load(singlePoseClip(loaded,'IMPORTED_POSE'));editing=true;
      renderPose(loaded);status('Imported avatar pose.');
    }else if(loaded.schema===ANIMATION_SCHEMA){
      backToAngleControls();validateClip(loaded);player.load(loaded);editing=false;
      renderPose(player.currentPose());status(`Imported animation: ${loaded.label}`);
    }else throw new Error('Unsupported schema. Expected svb.avatar.positions.v1, svb.avatar.pose.v1 or svb.avatar.animation.v1.');
    clipUi();
  }catch(error){status(`Import failed: ${error.message}`,true);}
  event.target.value='';
});
const resize = () => {
  const w=Math.max(1,host.clientWidth),h=Math.max(1,host.clientHeight);
  camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);
};
new ResizeObserver(resize).observe(host);
window.addEventListener('resize',resize);
renderPose(player.currentPose());clipUi();
let prev=performance.now(),lastUi=0;
function animate(now){
  const elapsed=Math.min(150,Math.max(0,now-prev));prev=now;
  if(motionMode==='position'){if(positionPlayer.playing)positionRig.applyFrame(positionPlayer.tick(elapsed));}
  else if(player.playing){renderPose(player.tick(elapsed),false);}
  orbit.update();renderer.render(scene,camera);
  if(now-lastUi>65){
    if(motionMode==='angle' && player.playing)syncControls();
    clipUi();lastUi=now;
  }
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

$('btn-position-demo').addEventListener('click',()=>{loadPositionClip(demoPositionClip());status('Loaded SYNTHETIC 3D joint-position example. It is NOT an ASL recording.');});
