"""
Silent Voice Bridge v2 - ASL Synthesis Web API Server
Serves the custom English-to-ASL Synthesis Engine over HTTP.

Endpoints:
- GET / : Interactive Web UI
- GET /api/synthesize?text=<phrase> : Synthesizes ASL glosses, video, and .pose file
- GET /static/... : Serves generated video and pose files
"""

import hashlib
import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from asl_engine.synthesizer import ASLSynthesizer

STATIC_DIR = ROOT_DIR / "web_static"
VIDEO_DIR = STATIC_DIR / "videos"
POSES_DIR = STATIC_DIR / "poses"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
POSES_DIR.mkdir(parents=True, exist_ok=True)

synth = ASLSynthesizer()


class ASLServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/synthesize":
            self.handle_synthesize(params)
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
            self.send_error(404, "Path not found")

    def handle_synthesize(self, params):
        text = params.get("text", [""])[0].strip()
        if not text:
            self.send_json({"error": "Missing 'text' query parameter"}, 400)
            return

        print(f"\n🌐 Web API Request: \"{text}\"")
        try:
            res = synth.synthesize(text)

            # Generate unique hash for this phrase to cache the generated video
            h = hashlib.md5(text.lower().encode()).hexdigest()[:10]
            video_name = f"sign_{h}.mp4"
            pose_name = f"sign_{h}.pose"

            video_path = VIDEO_DIR / video_name
            pose_path = POSES_DIR / pose_name

            # Save pose file
            if not pose_path.exists():
                with open(pose_path, "wb") as f:
                    res.pose.write(f)

            # Render video if not already cached
            if not video_path.exists():
                synth.export_to_video(res, str(video_path))

            payload = {
                "english_text": res.english_text,
                "glosses": res.glosses,
                "total_frames": res.total_frames,
                "fps": res.fps,
                "duration_sec": round(res.total_frames / res.fps, 2),
                "timings": res.timings,
                "video_url": f"/static/videos/{video_name}",
                "pose_url": f"/static/poses/{pose_name}",
            }
            self.send_json(payload)
        except Exception as e:
            print(f"❌ Error during synthesis: {e}")
            self.send_json({"error": str(e)}, 500)

    def serve_file(self, file_path: Path):
        self.send_response(200)
        suffix = file_path.suffix.lower()
        if suffix == ".mp4":
            self.send_header("Content-Type", "video/mp4")
        elif suffix == ".pose":
            self.send_header("Content-Type", "application/octet-stream")
        elif suffix == ".json":
            self.send_header("Content-Type", "application/json")
        elif suffix in (".png", ".jpg"):
            self.send_header("Content-Type", f"image/{suffix[1:]}")
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
        ui_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Silent Voice Bridge - Custom ASL Synthesis Engine</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card: #151b2b;
      --border: #232d42;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --success: #10b981;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: var(--card);
      border-bottom: 1px solid var(--border);
      padding: 16px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .badge {
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 3px 10px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 24px;
      max-width: 1300px;
      width: 100%;
      margin: 32px auto;
      padding: 0 24px;
      flex: 1;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    h2 {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .chip {
      background: #1e293b;
      border: 1px solid #334155;
      color: var(--text);
      font-size: 0.8rem;
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .chip:hover {
      background: var(--accent);
      color: #0b0f19;
      border-color: var(--accent);
    }
    textarea {
      width: 100%;
      height: 90px;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 12px;
      color: var(--text);
      font-size: 0.95rem;
      resize: none;
      font-family: inherit;
    }
    textarea:focus {
      outline: none;
      border-color: var(--accent);
    }
    button.synthesize-btn {
      background: var(--accent);
      color: #0b0f19;
      border: none;
      border-radius: 10px;
      padding: 12px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    button.synthesize-btn:hover {
      background: var(--accent-hover);
    }
    .viewer-panel {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: #000;
      border-radius: 14px;
      border: 1px solid var(--border);
      min-height: 520px;
      position: relative;
      overflow: hidden;
    }
    video {
      width: 100%;
      max-height: 520px;
      object-fit: contain;
      background: #000;
    }
    .gloss-timeline {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 12px;
      background: #0f172a;
      border-radius: 10px;
      border: 1px solid #1e293b;
    }
    .gloss-tag {
      background: #1e293b;
      color: #38bdf8;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 4px 8px;
      border-radius: 6px;
      border: 1px solid #334155;
    }
    .stats-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .spinner {
      border: 4px solid #1e293b;
      border-top: 4px solid var(--accent);
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      display: none;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🤟 Silent Voice Bridge v2</span>
      <span class="badge">Workstream B Engine</span>
    </div>
    <div style="font-size: 0.85rem; color: var(--text-muted);">
      SJSU CMPE 195 Senior Design Capstone
    </div>
  </header>

  <div class="main-grid">
    <div class="card">
      <h2>💬 English Input</h2>
      <textarea id="englishInput" placeholder="Type an English phrase (e.g. 'What is your name?')...">What is your name?</textarea>
      <button class="synthesize-btn" id="synthesizeBtn" onclick="synthesize()">⚡ Synthesize ASL Motion</button>

      <h2>🎯 Capstone Demo Presets</h2>
      <div class="chips">
        <span class="chip" onclick="setPreset('What is your name?')">What is your name?</span>
        <span class="chip" onclick="setPreset('My name is Aramish')">My name is Aramish</span>
        <span class="chip" onclick="setPreset('Hello, how are you?')">Hello, how are you?</span>
        <span class="chip" onclick="setPreset('Nice to meet you')">Nice to meet you</span>
        <span class="chip" onclick="setPreset('Thank you so much')">Thank you</span>
        <span class="chip" onclick="setPreset('Could you please repeat that?')">Please repeat</span>
        <span class="chip" onclick="setPreset('I am deaf')">I am deaf</span>
        <span class="chip" onclick="setPreset('I like airplanes')">I like airplanes</span>
        <span class="chip" onclick="setPreset('I need help')">I need help</span>
        <span class="chip" onclick="setPreset('Please write it down')">Write it down</span>
      </div>

      <h2>🧬 ASL Grammar & Glosses</h2>
      <div id="glossContainer" class="gloss-timeline">
        <span class="gloss-tag">[YOUR]</span>
        <span style="color: #64748b; font-size: 0.75rem;">→</span>
        <span class="gloss-tag">[NAME]</span>
        <span style="color: #64748b; font-size: 0.75rem;">→</span>
        <span class="gloss-tag">[WHAT]</span>
      </div>

      <div class="stats-row" id="statsRow">
        <span id="statFrames">307 frames @ 25 FPS</span>
        <span id="statDuration">12.3s duration</span>
      </div>
    </div>

    <div class="card">
      <h2>🎭 ASL Skeleton Player (Blended Motion)</h2>
      <div class="viewer-panel" id="viewerPanel">
        <div class="spinner" id="loadingSpinner"></div>
        <video id="aslVideo" controls autoplay loop playsinline>
          <source src="/static/videos/what_is_your_name_demo.mp4" type="video/mp4">
        </video>
      </div>
    </div>
  </div>

  <script>
    function setPreset(text) {
      document.getElementById('englishInput').value = text;
      synthesize();
    }

    async function synthesize() {
      const text = document.getElementById('englishInput').value.trim();
      if (!text) return;

      const spinner = document.getElementById('loadingSpinner');
      const video = document.getElementById('aslVideo');
      const btn = document.getElementById('synthesizeBtn');
      const glossContainer = document.getElementById('glossContainer');

      btn.disabled = true;
      btn.innerText = "⏳ Blending ASL Signs...";
      spinner.style.display = 'block';
      video.style.opacity = '0.3';

      try {
        const resp = await fetch('/api/synthesize?text=' + encodeURIComponent(text));
        const data = await resp.json();
        if (data.error) {
          alert('Synthesis error: ' + data.error);
          return;
        }

        // Render gloss chips
        glossContainer.innerHTML = '';
        data.glosses.forEach((g, idx) => {
          const tag = document.createElement('span');
          tag.className = 'gloss-tag';
          tag.innerText = '[' + g + ']';
          glossContainer.appendChild(tag);
          if (idx < data.glosses.length - 1) {
            const arrow = document.createElement('span');
            arrow.style.cssText = 'color: #64748b; font-size: 0.75rem;';
            arrow.innerText = '→';
            glossContainer.appendChild(arrow);
          }
        });

        // Update stats
        document.getElementById('statFrames').innerText = data.total_frames + ' frames @ ' + data.fps + ' FPS';
        document.getElementById('statDuration').innerText = data.duration_sec + 's duration';

        // Load new video
        video.src = data.video_url;
        video.load();
        video.play();
      } catch (err) {
        console.error(err);
        alert('Failed to connect to synthesis server');
      } finally {
        spinner.style.display = 'none';
        video.style.opacity = '1';
        btn.disabled = false;
        btn.innerText = "⚡ Synthesize ASL Motion";
      }
    }
  </script>
</body>
</html>
"""
        body = ui_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(port: int = 8090):
    server = HTTPServer(("0.0.0.0", port), ASLServerHandler)
    print(f"\n🚀 ASL Engine Server running on http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
    run(port)
