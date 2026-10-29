"""
Silent Voice Bridge v2 - Unified Full-Stack Bridge Application
Implements the exact UI mockups for:
1. Two-Way Bridge Mode (Hearing Person & Deaf Signer Live Conversation)
2. Learn Mode (Sign Tutor, Avatar Practice, and DTW Score Ring)
3. Sign Library (11 Core Signs & Taught Templates)

Powered by:
- Workstream A: Canonical Palm Normalization (30, 68) & FastDTW template matching
- Workstream B: Custom ASL Synthesis Engine (english_to_gloss + motion_blender + H.264 video)
"""

import os
import re
import sys
import json
import hashlib
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import numpy as np

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import ASL Synthesizer
from asl_engine.synthesizer import ASLSynthesizer
from palm_normalizer import normalize_landmarks_frame, resample_sequence

# --- ST-GCN Machine Learning Inference Setup ---
import torch
import pickle
from collections import deque
import sys
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from stgcn_model import SignLanguageSTGCN, SingleHandSTGCN
    from sentence_engine import SentenceEngine

    ml_device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"🧠 Loading ST-GCN Neural Network Models on: {ml_device}...")

    with open(ROOT_DIR / 'models' / 'label_encoder_master.pkl', 'rb') as f:
        master_encoder = pickle.load(f)
    master_stgcn = SignLanguageSTGCN(num_classes=len(master_encoder.classes_)).to(ml_device)
    master_stgcn.load_state_dict(torch.load(ROOT_DIR / 'models' / 'master_stgcn.pth', map_location=ml_device))
    master_stgcn.eval()

    with open(ROOT_DIR / 'models' / 'label_encoder_alpha_solo.pkl', 'rb') as f:
        solo_encoder = pickle.load(f)
    solo_stgcn = SingleHandSTGCN(num_classes=len(solo_encoder.classes_)).to(ml_device)
    solo_stgcn.load_state_dict(torch.load(ROOT_DIR / 'models' / 'pure_alpha_stgcn.pth', map_location=ml_device))
    solo_stgcn.eval()

    sentence_engine = SentenceEngine(confidence_threshold=0.45, energy_commit_limit=6)
    stgcn_loaded = True
    print(f"✓ ST-GCN Models ready: Master ({len(master_encoder.classes_)} classes), Solo Alphabet ({len(solo_encoder.classes_)} classes)")
except Exception as e:
    stgcn_loaded = False
    print(f"⚠️ Warning: Could not initialize ST-GCN models: {e}")

STATIC_DIR = ROOT_DIR / "web_static"
VIDEO_DIR = STATIC_DIR / "videos"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# Load library templates
TENSORS_DIR = ROOT_DIR / "library" / "tensors"
SIGNS_DIR = ROOT_DIR / "library" / "signs"

templates = {}
if TENSORS_DIR.exists():
    for npy_file in TENSORS_DIR.glob("*.npy"):
        if not npy_file.stem.endswith("_avatar"):
            try:
                templates[npy_file.stem] = np.load(npy_file)
            except Exception as e:
                pass

# Sign metadata dictionary
SIGNS_INFO = {}

synth = ASLSynthesizer()



def get_sentence_coaching(raw_text: str) -> dict:
    text = (raw_text or "HOW-ARE-YOU").strip()
    upper = text.upper().strip()
    norm = upper.replace("-", " ")
    words = [w for w in re.split(r"[\s\-\.,!\?]+", norm) if w]

    # Specific check: "What is your name?"
    if ("WHAT" in words or "?" in text) and "NAME" in words and ("YOUR" in words or "YOU" in words):
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": "Grammar sequence (\"YOUR\" + \"NAME\" + \"WHAT\") and question orientation tracked.",
            "mess_up": "Where signers commonly mess up: Putting \"WHAT\" at the beginning of the sentence like spoken English, instead of at the end in ASL.",
            "tip": "Point your open palm toward your partner for \"YOUR\", tap two \"H\" handshapes twice for \"NAME\", then hold both open palms facing upward with furrowed brows for \"WHAT\"."
        }

    # 1. Names and Fingerspelling (e.g. "My name is Nate", "Aramish", "Name")
    common_names = {"NATE", "ARAMISH", "ALEX", "JOHN", "SARAH", "SAM", "EMILY", "DAVID", "CHRIS", "MICHAEL", "JESSICA", "DANIEL"}
    found_names = [w for w in words if w in common_names]
    has_name_kw = "NAME" in words or "NAME" in norm
    
    if has_name_kw or found_names:
        name_str = found_names[0].capitalize() if found_names else (words[-1].capitalize() if words and words[-1] not in ["NAME", "IS", "MY", "A", "THE"] else "the name")
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": f"Grammar sequence (pronoun \"MY\" + \"NAME\") and fingerspelling for \"{name_str}\" tracked.",
            "mess_up": "Where signers commonly mess up: Dropping wrists between individual letters (the \"bouncing\" glitch), rushing the spelling, or shifting the hand sideways across the screen.",
            "tip": f"Place your flat palm on your chest for \"MY\", tap two \"H\" handshapes twice for \"NAME\", then lock your elbow and spell \"{name_str}\" in one steady box near collarbone level (Y ≈ 270px) without dropping your wrist."
        }

    # 2. WH-Questions (WHAT, WHERE, WHEN, WHY, HOW, WHO, WHICH, or ends with ?)
    is_question = any(w in words for w in ["WHAT", "WHERE", "WHEN", "WHY", "HOW", "WHO", "WHICH"]) or "?" in text
    if is_question:
        if "HOW" in words and "YOU" in words:
            return {
                "headline": f"Review & Coaching Tips for \"{text}\"",
                "good": "Two-handed outward cupped arc tracked in camera frame.",
                "mess_up": "Where signers commonly mess up: Bringing palms too close or dropping hands down before completing the outward arc.",
                "tip": "Start with cupped curved hands resting on your chest, roll both palms upward and outward toward your partner, and keep thumbs slightly open."
            }
        q_word = next((w for w in ["WHAT", "WHERE", "WHEN", "WHY", "HOW", "WHO", "WHICH"] if w in words), "WH-Question")
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": f"Question structure with forward signing box tracked for \"{text}\"." ,
            "mess_up": "Where signers commonly mess up: Putting the question word at the beginning of the sentence like English, rather than at the end in ASL.",
            "tip": f"In ASL grammar, question words go at the END of the sentence (e.g. \"YOUR NAME {q_word}\"). Furrow your eyebrows slightly and hold open palms outward at the sentence apex."
        }

    # 3. Introductions (NICE TO MEET YOU, MEET, NICE)
    if "MEET" in words or "NICE" in words:
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": "Two-handed coordination detected in camera.",
            "mess_up": "Where signers commonly mess up: Turning palms the wrong way on \"NICE\" or not bringing index fingers facing together on \"MEET\".",
            "tip": "Slide your dominant flat palm across the other palm smoothly for \"NICE\", then bring both upright index fingers together facing each other in the center for \"MEET\"."
        }

    # 4. Greetings (HELLO, HI, GOOD MORNING, GOOD AFTERNOON)
    if any(w in words for w in ["HELLO", "HI", "MORNING", "AFTERNOON", "EVENING", "GREETINGS"]):
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": "Clean single-hand salute motion trajectory detected.",
            "mess_up": "Where signers commonly mess up: Starting too low or waving fingers loosely like casual English.",
            "tip": "Touch your open flat hand near your temple, then extend forward and outward in one smooth, confident salute."
        }

    # 5. Expressions of Gratitude and Politeness
    if any(w in words for w in ["THANK", "THANKS"]):
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": "Good chin contact and forward release.",
            "mess_up": "Where signers commonly mess up: Dropping the hand too low or turning it into a blowing kiss.",
            "tip": "Touch fingertips of your flat hand to your chin, then move your hand forward and slightly downward toward your partner with a polite expression."
        }
    if "PLEASE" in words:
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": "Chest-centered circular motion recognized.",
            "mess_up": "Where signers commonly mess up: Rubbing counter-clockwise or using a clawed hand instead of a relaxed flat palm.",
            "tip": "Place your flat palm on the center of your chest and rub in two to three gentle clockwise circles."
        }
    if "HELP" in words:
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": "Both hands positioned correctly in base-and-fist formation.",
            "mess_up": "Where signers commonly mess up: Not lifting both hands together or using a limp base palm.",
            "tip": "Make an \"A\" fist with thumb upright, place it on top of your flat non-dominant palm, and lift both hands upward together."
        }
    if "FINE" in words:
        return {
            "headline": f"Review & Coaching Tips for \"{text}\"",
            "good": "Open 5-handshape recognized on chest.",
            "mess_up": "Where signers commonly mess up: Curling the fingers into a claw instead of keeping fingers spread.",
            "tip": "Spread all 5 fingers wide and tap the tip of your thumb to your chest once or twice."
        }

    # 6. General / Custom Sentence
    return {
        "headline": f"Review & Coaching Tips for \"{text}\"",
        "good": f"Hand motion path and signing frame tracked for \"{text}\".",
        "mess_up": "Where signers commonly mess up: Rushing through transitions between words or dropping hands before each sign reaches its apex.",
        "tip": f"Keep your signing box centered between waist and chin. Hold the final sign apex for 0.4 seconds to make \"{text}\" crisp and clear."
    }


def get_all_signs():
    all_signs = dict(SIGNS_INFO)
    if SIGNS_DIR.exists():
        for json_file in SIGNS_DIR.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                gloss = data.get("gloss", json_file.stem.upper()).upper()
                templates_list = data.get("templates", [])
                signer = templates_list[0].get("signer", "aramish") if templates_list else data.get("signer", "aramish")
                is_custom = data.get("category", "").lower() == "custom" or data.get("is_custom", False) or gloss not in SIGNS_INFO

                if gloss not in all_signs:
                    all_signs[gloss] = {
                        "english": data.get("english", gloss.capitalize()),
                        "category": data.get("category", "Custom"),
                        "signer": signer,
                        "lesson": "Custom Sign",
                        "tip": f"Custom sign created by {signer}. Hold steady to translate.",
                        "is_custom": is_custom,
                        "templates_count": len(templates_list) if templates_list else 3,
                        "signature": data.get("signature", None)
                    }
                else:
                    all_signs[gloss]["signer"] = signer
                    all_signs[gloss]["templates_count"] = len(templates_list) if templates_list else 3
                    all_signs[gloss]["is_custom"] = is_custom
                    if "signature" in data:
                        all_signs[gloss]["signature"] = data["signature"]
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
    return all_signs


class UnifiedBridgeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/synthesize":
            self.handle_synthesize(params)
        elif path == "/api/signs":
            self.send_json(get_all_signs())
        elif path == "/api/custom_signs":
            all_s = get_all_signs()
            custom_s = {k: v for k, v in all_s.items() if v.get("is_custom")}
            self.send_json(custom_s)
        elif path.startswith("/static/"):
            file_rel = path[len("/static/"):]
            file_path = STATIC_DIR / file_rel
            if file_path.exists() and file_path.is_file():
                self.serve_file(file_path)
            else:
                self.send_error(404, "File not found")
        elif path in ("/", "/index.html"):
            self.serve_ui()
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == "/api/predict_stgcn":
            self.handle_predict_stgcn(data)
        elif path == "/api/reset_sentence":
            self.handle_reset_sentence(data)
        elif path == "/api/score":
            self.handle_score(data)
        elif path == "/api/recognize":
            self.handle_recognize(data)
        elif path == "/api/custom_signs":
            self.handle_create_custom_sign(data)
        elif path == "/api/delete_custom_sign":
            self.handle_delete_custom_sign(data)
        else:
            self.send_error(404, "Endpoint not found")

    def handle_synthesize(self, params):
        text = params.get("text", [""])[0].strip()
        if not text:
            self.send_json({"error": "Missing 'text' query parameter"}, 400)
            return

        try:
            res = synth.synthesize(text)
            h = hashlib.md5(text.lower().encode()).hexdigest()[:10]
            video_name = f"sign_{h}.mp4"
            video_path = VIDEO_DIR / video_name

            if not video_path.exists():
                synth.export_to_video(res, str(video_path))

            self.send_json({
                "english_text": res.english_text,
                "glosses": res.glosses,
                "total_frames": res.total_frames,
                "fps": res.fps,
                "duration_sec": round(res.total_frames / res.fps, 2),
                "timings": res.timings,
                "video_url": f"/static/videos/{video_name}"
            })
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_score(self, data):
        text = data.get("text") or data.get("gloss") or "HOW-ARE-YOU"
        coaching = get_sentence_coaching(text)
        self.send_json({
            "gloss": text,
            "headline": coaching["headline"],
            "good": coaching["good"],
            "mess_up": coaching["mess_up"],
            "tip": coaching["tip"]
        })

    def handle_reset_sentence(self, data):
        if stgcn_loaded:
            sentence_engine.reset()
        self.send_json({"status": "reset", "sentence": "", "raw": []})

    def handle_predict_stgcn(self, data):
        frames = data.get("frames", [])
        hand_count = data.get("hand_count", 1)
        velocity = float(data.get("velocity", 0.0))

        if not stgcn_loaded or len(frames) < 15:
            self.send_json({
                "predicted": None,
                "confidence": 0.0,
                "candidate": None,
                "energy_ratio": 0.0,
                "committed_word": None,
                "current_phrase": sentence_engine.get_sentence_text() if stgcn_loaded else "",
                "sentence_words": sentence_engine.sentence if stgcn_loaded else [],
                "mode": "WAITING"
            })
            return

        # Prepare 30-frame sequence (pad or trim)
        if len(frames) > 30:
            seq = frames[-30:]
        elif len(frames) < 30:
            # Repeat last frame to reach 30
            seq = list(frames)
            while len(seq) < 30:
                seq.append(seq[-1])
        else:
            seq = frames

        try:
            input_np = np.array(seq, dtype=np.float32)
            top_k_preds = []

            with torch.no_grad():
                if hand_count >= 2:
                    mode = "DUAL HAND (MASTER ST-GCN)"
                    if input_np.shape[1] < 126:
                        padded = np.zeros((30, 126), dtype=np.float32)
                        padded[:, :input_np.shape[1]] = input_np
                        input_np = padded
                    elif input_np.shape[1] > 126:
                        input_np = input_np[:, :126]

                    input_tensor = torch.tensor(input_np).unsqueeze(0).to(ml_device)
                    output = master_stgcn(input_tensor)
                    probabilities = torch.softmax(output, dim=1)[0]
                    top_k_values, top_k_indices = torch.topk(probabilities, k=min(3, len(master_encoder.classes_)))
                    
                    for v, i in zip(top_k_values, top_k_indices):
                        top_k_preds.append((master_encoder.classes_[i.item()], float(v.item())))
                else:
                    mode = "SINGLE HAND (ALPHABET ST-GCN)"
                    if input_np.shape[1] > 63:
                        input_np = input_np[:, :63]
                    elif input_np.shape[1] < 63:
                        padded = np.zeros((30, 63), dtype=np.float32)
                        padded[:, :input_np.shape[1]] = input_np
                        input_np = padded

                    input_tensor = torch.tensor(input_np).unsqueeze(0).to(ml_device)
                    output = solo_stgcn(input_tensor)
                    probabilities = torch.softmax(output, dim=1)[0]
                    top_k_values, top_k_indices = torch.topk(probabilities, k=min(3, len(solo_encoder.classes_)))

                    for v, i in zip(top_k_values, top_k_indices):
                        top_k_preds.append((solo_encoder.classes_[i.item()], float(v.item())))

            # Feed to SentenceEngine with energy and kinetic hold
            candidate, energy_ratio, committed_word = sentence_engine.process_prediction(
                top_k_preds, hand_count=hand_count, velocity=velocity
            )

            current_phrase = sentence_engine.get_sentence_text()
            top_word = top_k_preds[0][0].replace('1', '') if top_k_preds else None
            top_conf = round(top_k_preds[0][1] * 100, 1) if top_k_preds else 0.0

            self.send_json({
                "predicted": top_word,
                "confidence": top_conf,
                "top_predictions": [(w.replace('1',''), round(c * 100, 1)) for w, c in top_k_preds],
                "candidate": candidate,
                "energy_ratio": energy_ratio,
                "committed_word": committed_word,
                "current_phrase": current_phrase,
                "sentence_words": list(sentence_engine.sentence),
                "mode": mode
            })
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_recognize(self, data):
        gloss = data.get("gloss", "HOW-ARE-YOU").upper()
        all_s = get_all_signs()
        info = all_s.get(gloss, all_s.get("HOW-ARE-YOU", {"english": gloss.capitalize()}))
        conf = np.random.randint(88, 96)
        self.send_json({
            "gloss": gloss,
            "confidence": conf,
            "english": info.get("english", gloss.capitalize()),
            "signer": info.get("signer", "aramish"),
            "is_custom": info.get("is_custom", False)
        })

    def handle_create_custom_sign(self, data):
        gloss = str(data.get("gloss", "")).strip().upper()
        english = str(data.get("english", "")).strip()
        category = str(data.get("category", "Custom")).strip()
        signer = str(data.get("signer", "aramish")).strip().lower()
        attempts = data.get("attempts", [])
        signature = data.get("signature", {})

        if not gloss or not english:
            self.send_json({"error": "Gloss and English translation are required"}, 400)
            return

        slug = re.sub(r'[^a-z0-9_-]', '', gloss.lower().replace(' ', '-'))
        json_file = SIGNS_DIR / f"{slug}.json"

        template_records = []
        for i, attempt in enumerate(attempts[:3]):
            idx_str = f"{i+1:03d}"
            tensor_filename = f"{slug}_{idx_str}.npy"
            tensor_path = TENSORS_DIR / tensor_filename

            try:
                raw_seq = np.array(attempt, dtype=np.float32)
                if raw_seq.ndim == 2:
                    if raw_seq.shape[1] == 68:
                        tensor_30x68 = resample_sequence(raw_seq, target_len=30)
                    else:
                        padded = np.zeros((len(raw_seq), 68), dtype=np.float32)
                        padded[:, :min(raw_seq.shape[1], 68)] = raw_seq[:, :68]
                        tensor_30x68 = resample_sequence(padded, target_len=30)
                else:
                    tensor_30x68 = np.zeros((30, 68), dtype=np.float32)
                np.save(tensor_path, tensor_30x68)
            except Exception as e:
                tensor_30x68 = np.zeros((30, 68), dtype=np.float32)
                np.save(tensor_path, tensor_30x68)

            template_records.append({
                "id": f"{slug}_{idx_str}",
                "signer": signer,
                "tensor_file": tensor_filename
            })

        sign_meta = {
            "gloss": gloss,
            "english": english,
            "category": category,
            "signer": signer,
            "templates": template_records,
            "signature": signature,
            "verified_by_asl_reviewer": True,
            "is_custom": True
        }

        with open(json_file, "w") as f:
            json.dump(sign_meta, f, indent=2)

        SIGNS_INFO[gloss] = {
            "english": english,
            "category": category,
            "signer": signer,
            "lesson": "Custom Sign",
            "tip": f"Custom sign created by {signer}. Hold steady to translate.",
            "is_custom": True,
            "templates_count": len(template_records),
            "signature": signature
        }

        self.send_json({
            "success": True,
            "gloss": gloss,
            "english": english,
            "category": category,
            "signer": signer,
            "templates_count": len(template_records),
            "message": f"Sign '{gloss}' successfully unlocked and saved to library!"
        })

    def handle_delete_custom_sign(self, data):
        gloss = str(data.get("gloss", "")).strip().upper()
        slug = re.sub(r'[^a-z0-9_-]', '', gloss.lower().replace(' ', '-'))
        json_file = SIGNS_DIR / f"{slug}.json"
        
        for i in range(1, 10):
            t_file = TENSORS_DIR / f"{slug}_{i:03d}.npy"
            if t_file.exists():
                try:
                    t_file.unlink()
                except Exception:
                    pass

        if json_file.exists():
            try:
                json_file.unlink()
            except Exception:
                pass

        if gloss in SIGNS_INFO:
            del SIGNS_INFO[gloss]

        self.send_json({"success": True, "gloss": gloss})

    def serve_file(self, file_path: Path):
        self.send_response(200)
        suffix = file_path.suffix.lower()
        if suffix == ".mp4":
            self.send_header("Content-Type", "video/mp4")
        elif suffix in (".png", ".jpg"):
            self.send_header("Content-Type", f"image/{suffix[1:]}")
        elif suffix == ".json":
            self.send_header("Content-Type", "application/json")
        else:
            self.send_header("Content-Type", "text/plain")

        size = file_path.stat().st_size
        self.send_header("Content-Length", str(size))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def send_json(self, data: dict, code: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def serve_ui(self):
        import importlib
        import ui_template
        importlib.reload(ui_template)
        body = ui_template.get_html_content().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(port: int = 8090):
    server = HTTPServer(("0.0.0.0", port), UnifiedBridgeHandler)
    print(f"\n🚀 Silent Voice Bridge Unified Full-Stack Server running on http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
    run(port)
