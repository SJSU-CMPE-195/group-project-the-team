"""
HTML/CSS/JS Template for Silent Voice Bridge v2
Pixel-perfect replication of Bridge Mode (Image 1) and Learn Mode (Image 2).
"""

def get_html_content() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Silent Voice Bridge - Sign Tutor & Two-Way Bridge</title>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --teal-primary: #0d695e;
      --teal-hover: #0a524a;
      --teal-light: #e6f4f1;
      --teal-light-hover: #d2ebe5;
      --dark-cam: #0c1524;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --signer-bubble: #e6f4f1;
      --hearing-bubble: #f1f5f9;
      --accent-cyan: #2dd4bf;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body {
      background: var(--bg);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* --- TOP NAVBAR --- */
    header {
      background: #ffffff;
      border-bottom: 1px solid var(--border);
      padding: 14px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      background: var(--teal-primary);
      color: #ffffff;
      font-weight: 700;
      font-size: 0.85rem;
      padding: 6px 10px;
      border-radius: 6px;
      letter-spacing: 0.5px;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
      letter-spacing: -0.3px;
    }
    .nav-tabs {
      display: flex;
      gap: 8px;
      background: #f1f5f9;
      padding: 4px;
      border-radius: 9999px;
    }
    .nav-tab {
      padding: 7px 18px;
      border-radius: 9999px;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s ease;
      border: none;
      background: transparent;
    }
    .nav-tab.active {
      background: var(--teal-light);
      color: var(--teal-primary);
    }
    .nav-tab:hover:not(.active) {
      color: var(--text-main);
    }
    .header-right {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-muted);
    }

    /* --- CONTAINER --- */
    .app-container {
      max-width: 1280px;
      width: 100%;
      margin: 24px auto;
      padding: 0 24px;
      flex: 1;
    }
    .tab-content {
      display: none;
    }
    .tab-content.active {
      display: block;
    }

    /* --- BRIDGE TAB LAYOUT (IMAGE 1) --- */
    .bridge-grid {
      display: grid;
      grid-template-columns: 1.15fr 1fr;
      gap: 24px;
    }
    .bridge-col {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* Camera Box (Image 1 Left Top) */
    .cam-card {
      background: var(--dark-cam);
      border-radius: 18px;
      position: relative;
      overflow: hidden;
      aspect-ratio: 16 / 10;
      min-height: 380px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .cam-badge {
      position: absolute;
      top: 16px;
      left: 16px;
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(8px);
      color: #ffffff;
      font-size: 0.75rem;
      font-weight: 500;
      padding: 6px 14px;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      gap: 6px;
      z-index: 10;
    }
    .cam-badge .pulse-dot {
      width: 7px;
      height: 7px;
      background: var(--accent-cyan);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-cyan);
    }
    video#webcamVideo {
      display: none;
    }
    canvas#camCanvas {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .recognized-overlay {
      position: absolute;
      bottom: 16px;
      left: 16px;
      right: 16px;
      background: #ffffff;
      border-radius: 12px;
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 8px 20px rgba(0,0,0,0.15);
      z-index: 10;
    }
    .rec-label {
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .rec-gloss {
      font-size: 1.45rem;
      font-weight: 800;
      color: #0b1e33;
      letter-spacing: -0.5px;
      margin-top: 2px;
    }
    .rec-conf-col {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 6px;
    }
    .conf-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .conf-title {
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .conf-val {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--teal-primary);
    }
    .conf-bar-bg {
      width: 140px;
      height: 8px;
      background: #e2e8f0;
      border-radius: 9999px;
      overflow: hidden;
    }
    .conf-bar-fill {
      height: 100%;
      background: var(--teal-primary);
      width: 91%;
      border-radius: 9999px;
      transition: width 0.3s ease;
    }

    /* English Speech Box (Image 1 Left Bottom) */
    .card-english {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px 26px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .card-english h3 {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }
    .card-english .eng-text {
      font-size: 1.7rem;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.5px;
      margin-bottom: 4px;
    }
    .card-english .eng-sub {
      font-size: 0.82rem;
      color: var(--text-muted);
    }
    .btn-teal {
      background: var(--teal-primary);
      color: #ffffff;
      border: none;
      padding: 12px 24px;
      border-radius: 10px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-teal:hover {
      background: var(--teal-hover);
    }

    /* Quick Sim Chips */
    .quick-chips-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .quick-chips-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .chips-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .sign-chip {
      background: #f1f5f9;
      color: var(--text-main);
      font-size: 0.8rem;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      border: 1px solid var(--border);
      transition: all 0.2s;
    }
    .sign-chip:hover {
      background: var(--teal-light);
      color: var(--teal-primary);
      border-color: var(--teal-primary);
    }

    /* Conversation Box (Image 1 Right Top) */
    .convo-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      height: 380px;
    }
    .convo-header {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .convo-messages {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding-right: 6px;
    }
    .msg-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-width: 82%;
    }
    .msg-group.hearing {
      align-self: flex-start;
    }
    .msg-group.signer {
      align-self: flex-end;
    }
    .msg-sender {
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.4px;
      text-transform: uppercase;
    }
    .msg-group.hearing .msg-sender {
      color: var(--text-muted);
    }
    .msg-group.signer .msg-sender {
      color: #0d695e;
      text-align: right;
    }
    .bubble {
      padding: 12px 18px;
      border-radius: 14px;
      font-size: 0.95rem;
      line-height: 1.4;
      font-weight: 500;
    }
    .bubble.hearing {
      background: var(--hearing-bubble);
      color: var(--text-main);
      border-top-left-radius: 4px;
    }
    .bubble.signer {
      background: var(--signer-bubble);
      color: #064e45;
      border-top-right-radius: 4px;
    }

    /* Avatar Signing Box (Image 1 Right Center) */
    .avatar-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-height: 200px;
    }
    .avatar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .avatar-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .avatar-gloss {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--teal-primary);
    }
    .avatar-viewport {
      background: #0c1524;
      border-radius: 12px;
      height: 160px;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    video#avatarVideo {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    canvas#avatarCanvas {
      width: 100%;
      height: 100%;
    }

    /* Hearing Input Bar (Image 1 Right Bottom) */
    .input-bar {
      display: flex;
      gap: 12px;
      align-items: center;
    }
    .btn-mic {
      background: var(--teal-light);
      color: var(--teal-primary);
      border: none;
      padding: 14px 20px;
      border-radius: 12px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: background 0.2s;
    }
    .btn-mic:hover {
      background: var(--teal-light-hover);
    }
    .input-signer {
      flex: 1;
      border: 1px solid var(--border);
      background: #ffffff;
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 0.95rem;
      color: var(--text-main);
      outline: none;
      transition: border-color 0.2s;
    }
    .input-signer:focus {
      border-color: var(--teal-primary);
    }
    .btn-sign {
      background: var(--teal-primary);
      color: #ffffff;
      border: none;
      padding: 14px 26px;
      border-radius: 12px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-sign:hover {
      background: var(--teal-hover);
    }

    /* --- LEARN TAB LAYOUT (IMAGE 2) --- */
    .learn-subnav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }
    .step-badges {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .step-badge {
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 700;
      background: #e2e8f0;
      color: var(--text-muted);
    }
    .step-badge.active {
      background: var(--teal-primary);
      color: #ffffff;
    }
    .learn-header-right {
      display: flex;
      align-items: baseline;
      gap: 16px;
    }
    .learn-sign-title {
      font-size: 1.8rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: var(--text-main);
    }
    .learn-lesson-num {
      font-size: 0.88rem;
      font-weight: 500;
      color: var(--text-muted);
    }

    .learn-cards-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 24px;
    }
    .learn-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .learn-card-title {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .avatar-learn-screen {
      background: #e6f4f1;
      border-radius: 14px;
      aspect-ratio: 16 / 10;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }
    .avatar-learn-screen video {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .user-cam-screen {
      background: var(--dark-cam);
      border-radius: 14px;
      aspect-ratio: 16 / 10;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }
    .user-cam-screen canvas {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .learn-actions {
      display: flex;
      gap: 10px;
    }
    .btn-light-mint {
      background: var(--teal-light);
      color: var(--teal-primary);
      border: none;
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-light-mint:hover {
      background: var(--teal-light-hover);
    }

    /* Score Card (Image 2 Bottom) */
    .score-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 24px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }
    .score-gauge-col {
      display: flex;
      align-items: center;
      gap: 24px;
    }
    .score-ring {
      width: 82px;
      height: 82px;
      border-radius: 50%;
      border: 7px solid var(--teal-primary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.8rem;
      font-weight: 800;
      color: var(--text-main);
      flex-shrink: 0;
    }
    .score-details {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .score-label {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .score-headline {
      font-size: 1.4rem;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.3px;
    }
    .score-tip {
      font-size: 0.88rem;
      color: var(--text-muted);
      line-height: 1.4;
      max-width: 650px;
    }

    /* --- SIGN LIBRARY TAB --- */
    .library-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 20px;
    }
    .lib-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .lib-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(0,0,0,0.04);
    }
    .lib-badge {
      background: #f1f5f9;
      color: var(--text-muted);
      font-size: 0.72rem;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 6px;
      align-self: flex-start;
      text-transform: uppercase;
    }
    .lib-title {
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--text-main);
    }
    .lib-sub {
      font-size: 0.88rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>
  <!-- TOP NAVBAR -->
  <header>
    <div class="brand">
      <div class="brand-logo">SV</div>
      <div class="brand-title">Silent Voice Bridge</div>
    </div>
    <div class="nav-tabs">
      <button class="nav-tab active" onclick="switchTab('bridge')">Bridge</button>
      <button class="nav-tab" onclick="switchTab('learn')">Learn</button>
      <button class="nav-tab" onclick="switchTab('library')">Sign library</button>
    </div>
    <div class="header-right" id="headerRightStatus">
      11 Core Signs · FastDTW Active
    </div>
  </header>

  <div class="app-container">
    <!-- ==================== TAB 1: BRIDGE MODE (IMAGE 1) ==================== -->
    <div id="tab-bridge" class="tab-content active">
      <div class="bridge-grid">
        <!-- LEFT COLUMN: Signer Camera & Speech -->
        <div class="bridge-col">
          <!-- Camera Box -->
          <div class="cam-card">
            <div class="cam-badge">
              <span class="pulse-dot"></span>
              <span>Camera on · hands tracked</span>
            </div>
            <video id="webcamVideo" autoplay playsinline muted></video>
            <canvas id="camCanvas"></canvas>

            <!-- Bottom Recognized Overlay -->
            <div class="recognized-overlay">
              <div>
                <div class="rec-label">RECOGNIZED SIGN</div>
                <div class="rec-gloss" id="bridgeGloss">HOW-ARE-YOU</div>
              </div>
              <div class="rec-conf-col">
                <div class="conf-row">
                  <span class="conf-title">Confidence</span>
                  <span class="conf-val" id="bridgeConfVal">91%</span>
                </div>
                <div class="conf-bar-bg">
                  <div class="conf-bar-fill" id="bridgeConfBar" style="width: 91%;"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- English Speech Card -->
          <div class="card-english">
            <div>
              <h3>ENGLISH</h3>
              <div class="eng-text" id="bridgeEnglish">How are you?</div>
              <div class="eng-sub">Spoken aloud · Matches a taught sign</div>
            </div>
            <button class="btn-teal" onclick="speakCurrentSign()">Speak again</button>
          </div>

          <!-- Quick Sign Simulator / Presets -->
          <div class="quick-chips-box">
            <div class="quick-chips-title">Simulate Sign Detection (or use live webcam)</div>
            <div class="chips-row">
              <span class="sign-chip" onclick="simulateSign('HOW-ARE-YOU')">HOW-ARE-YOU</span>
              <span class="sign-chip" onclick="simulateSign('HELLO')">HELLO</span>
              <span class="sign-chip" onclick="simulateSign('MY-NAME')">MY-NAME</span>
              <span class="sign-chip" onclick="simulateSign('WHAT-IS-YOUR-NAME')">WHAT-IS-YOUR-NAME</span>
              <span class="sign-chip" onclick="simulateSign('NICE-MEET-YOU')">NICE-MEET-YOU</span>
              <span class="sign-chip" onclick="simulateSign('THANK-YOU')">THANK-YOU</span>
              <span class="sign-chip" onclick="simulateSign('PLEASE')">PLEASE</span>
              <span class="sign-chip" onclick="simulateSign('DEAF')">DEAF</span>
              <span class="sign-chip" onclick="simulateSign('FINE')">FINE</span>
              <span class="sign-chip" onclick="simulateSign('HELP')">HELP</span>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN: Conversation & Avatar Signing -->
        <div class="bridge-col">
          <!-- Conversation Box -->
          <div class="convo-card">
            <div class="convo-header">CONVERSATION</div>
            <div class="convo-messages" id="convoMessages">
              <div class="msg-group hearing">
                <div class="msg-sender">HEARING PARTNER</div>
                <div class="bubble hearing">Hi, nice to meet you.</div>
              </div>
              <div class="msg-group signer">
                <div class="msg-sender">SIGNER, SPOKEN BY APP</div>
                <div class="bubble signer">Hello!</div>
              </div>
              <div class="msg-group hearing">
                <div class="msg-sender">HEARING PARTNER</div>
                <div class="bubble hearing">How are you?</div>
              </div>
              <div class="msg-group signer">
                <div class="msg-sender">SIGNER, SPOKEN BY APP</div>
                <div class="bubble signer">I'm doing well, thank you.</div>
              </div>
            </div>
          </div>

          <!-- Avatar Signing Card -->
          <div class="avatar-card">
            <div class="avatar-header">
              <div class="avatar-title">AVATAR SIGNING</div>
              <div class="avatar-gloss" id="avatarGlossIndicator">HOW-ARE-YOU</div>
            </div>
            <div class="avatar-viewport">
              <video id="avatarVideo" controls autoplay loop playsinline>
                <source src="/static/videos/sign_a066814783.mp4" type="video/mp4">
              </video>
              <canvas id="avatarCanvas" style="display: none;"></canvas>
            </div>
          </div>

          <!-- Hearing Input Bar -->
          <div class="input-bar">
            <button class="btn-mic" onclick="toggleMic()">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              <span>Mic</span>
            </button>
            <input type="text" id="signerInput" class="input-signer" placeholder="Speak or type to the signer" onkeydown="if(event.key==='Enter') signIt()">
            <button class="btn-sign" onclick="signIt()">Sign it</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 2: LEARN MODE (IMAGE 2) ==================== -->
    <div id="tab-learn" class="tab-content">
      <!-- Subnavigation & Lesson Header -->
      <div class="learn-subnav">
        <div class="step-badges">
          <div class="step-badge active">1 Watch</div>
          <div class="step-badge active">2 Try it</div>
          <div class="step-badge">3 Score</div>
        </div>
        <div class="learn-header-right">
          <div class="learn-sign-title" id="learnSignTitle">HOW-ARE-YOU</div>
          <div class="learn-lesson-num" id="learnLessonNum">Lesson 2 of 8 · Greetings</div>
        </div>
      </div>

      <!-- Two Side-by-Side Cards -->
      <div class="learn-cards-row">
        <!-- Card 1: Watch the Avatar -->
        <div class="learn-card">
          <div class="learn-card-title">WATCH THE AVATAR</div>
          <div class="avatar-learn-screen">
            <video id="learnAvatarVideo" controls autoplay loop playsinline>
              <source src="/static/videos/sign_a066814783.mp4" type="video/mp4">
            </video>
          </div>
          <div class="learn-actions">
            <button class="btn-teal" onclick="playLearnAvatar()">Play</button>
            <button class="btn-light-mint" id="slowMoBtn" onclick="toggleSlowMo()">Slow motion</button>
            <button class="btn-light-mint" onclick="handCloseUp()">Hand close-up</button>
          </div>
        </div>

        <!-- Card 2: Your Turn -->
        <div class="learn-card">
          <div class="learn-card-title">YOUR TURN</div>
          <div class="user-cam-screen">
            <div class="cam-badge" id="learnCamBadge">
              <span class="pulse-dot"></span>
              <span id="learnCamStatusText">Recording · 1.2s</span>
            </div>
            <canvas id="learnCamCanvas"></canvas>
          </div>
          <div class="learn-actions">
            <button class="btn-teal" id="recordAttemptBtn" onclick="recordAttempt()">Record attempt</button>
            <button class="btn-light-mint" onclick="tryAgain()">Try again</button>
          </div>
        </div>
      </div>

      <!-- Card 3: Your Score (Bottom) -->
      <div class="score-card">
        <div class="score-gauge-col">
          <div class="score-ring" id="learnScoreRing">82</div>
          <div class="score-details">
            <div class="score-label">YOUR SCORE</div>
            <div class="score-headline" id="learnScoreHeadline">Close to the example. Nice work.</div>
            <div class="score-tip" id="learnScoreTip">
              Tip: raise your wrist a little and keep your thumb open. This compares your motion to the example, not a full ASL check.
            </div>
          </div>
        </div>
        <button class="btn-teal" onclick="nextLesson()">Next sign</button>
      </div>
    </div>

    <!-- ==================== TAB 3: SIGN LIBRARY ==================== -->
    <div id="tab-library" class="tab-content">
      <div style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: baseline;">
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.4px;">ASL Core Vocabulary & Taught Templates</h2>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 4px;">11 Core Signs · 3 Attempts Per Sign (Section 4 Contract)</p>
        </div>
      </div>
      <div class="library-grid" id="libraryGrid">
        <!-- Rendered by JS -->
      </div>
    </div>
  </div>

  <script>
    // --- STATE ---
    let activeTab = 'bridge';
    let currentSign = 'HOW-ARE-YOU';
    let slowMo = false;
    let signsData = {};

    const signOrder = [
      'HELLO', 'HOW-ARE-YOU', 'NICE-MEET-YOU', 'MY-NAME',
      'WHAT-IS-YOUR-NAME', 'THANK-YOU', 'PLEASE', 'DEAF',
      'FINE', 'HELP', 'WRITE-PLEASE'
    ];
    let currentLessonIdx = 1;

    // --- NAVIGATION ---
    function switchTab(tab) {
      activeTab = tab;
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      if (tab === 'bridge') {
        document.querySelectorAll('.nav-tab')[0].classList.add('active');
        document.getElementById('tab-bridge').classList.add('active');
        document.getElementById('headerRightStatus').innerText = '11 Core Signs · FastDTW Active';
      } else if (tab === 'learn') {
        document.querySelectorAll('.nav-tab')[1].classList.add('active');
        document.getElementById('tab-learn').classList.add('active');
        document.getElementById('headerRightStatus').innerText = document.getElementById('learnLessonNum').innerText;
        loadLearnSign(currentSign);
      } else if (tab === 'library') {
        document.querySelectorAll('.nav-tab')[2].classList.add('active');
        document.getElementById('tab-library').classList.add('active');
        document.getElementById('headerRightStatus').innerText = '11 signs · 33 templates';
        renderLibrary();
      }
    }

    // --- SIGN SYNTHESIS & SIGN IT (BRIDGE MODE) ---
    async function signIt() {
      const input = document.getElementById('signerInput');
      const text = input.value.trim();
      if (!text) return;

      // Append hearing partner message
      appendMessage('hearing', text);
      input.value = '';

      // Synthesize avatar motion via backend
      try {
        const resp = await fetch('/api/synthesize?text=' + encodeURIComponent(text));
        const data = await resp.json();
        if (data.video_url) {
          const video = document.getElementById('avatarVideo');
          video.src = data.video_url;
          video.load();
          video.play();
          document.getElementById('avatarGlossIndicator').innerText = data.glosses.join(' ');
        }
      } catch (err) {
        console.error('Synthesis error:', err);
      }
    }

    function appendMessage(sender, text) {
      const convo = document.getElementById('convoMessages');
      const group = document.createElement('div');
      group.className = 'msg-group ' + sender;

      const senderLabel = document.createElement('div');
      senderLabel.className = 'msg-sender';
      senderLabel.innerText = sender === 'hearing' ? 'HEARING PARTNER' : 'SIGNER, SPOKEN BY APP';

      const bubble = document.createElement('div');
      bubble.className = 'bubble ' + sender;
      bubble.innerText = text;

      group.appendChild(senderLabel);
      group.appendChild(bubble);
      convo.appendChild(group);
      convo.scrollTop = convo.scrollHeight;
    }

    function simulateSign(gloss) {
      fetch('/api/recognize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gloss: gloss })
      })
      .then(r => r.json())
      .then(data => {
        document.getElementById('bridgeGloss').innerText = data.gloss;
        document.getElementById('bridgeConfVal').innerText = data.confidence + '%';
        document.getElementById('bridgeConfBar').style.width = data.confidence + '%';
        document.getElementById('bridgeEnglish').innerText = data.english;

        // Speak aloud
        speakText(data.english);

        // Add to chat
        appendMessage('signer', data.english);

        // Update avatar
        currentSign = data.gloss;
        synthesizeAvatarForGloss(data.gloss);
      });
    }

    function speakCurrentSign() {
      const text = document.getElementById('bridgeEnglish').innerText;
      speakText(text);
    }

    function speakText(text) {
      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1.0;
        window.speechSynthesis.speak(u);
      }
    }

    async function synthesizeAvatarForGloss(gloss) {
      try {
        const resp = await fetch('/api/synthesize?text=' + encodeURIComponent(gloss.replace(/-/g, ' ')));
        const data = await resp.json();
        if (data.video_url) {
          const video = document.getElementById('avatarVideo');
          video.src = data.video_url;
          video.load();
          video.play();
          document.getElementById('avatarGlossIndicator').innerText = gloss;
        }
      } catch (e) {}
    }

    // --- LEARN MODE LOGIC ---
    function loadLearnSign(gloss) {
      currentSign = gloss;
      document.getElementById('learnSignTitle').innerText = gloss;
      const idx = signOrder.indexOf(gloss);
      const lessonText = idx >= 0 ? `Lesson ${idx + 1} of ${signOrder.length} · Greetings` : 'Practice Sign';
      document.getElementById('learnLessonNum').innerText = lessonText;

      // Update avatar in learn
      fetch('/api/synthesize?text=' + encodeURIComponent(gloss.replace(/-/g, ' ')))
        .then(r => r.json())
        .then(data => {
          if (data.video_url) {
            const v = document.getElementById('learnAvatarVideo');
            v.src = data.video_url;
            v.load();
            v.play();
          }
        });

      // Update score tip for this sign
      fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gloss: gloss })
      })
      .then(r => r.json())
      .then(data => {
        document.getElementById('learnScoreRing').innerText = data.score;
        document.getElementById('learnScoreHeadline').innerText = data.grade;
        document.getElementById('learnScoreTip').innerText = 'Tip: ' + data.tip;
      });
    }

    function toggleSlowMo() {
      slowMo = !slowMo;
      const v = document.getElementById('learnAvatarVideo');
      v.playbackRate = slowMo ? 0.5 : 1.0;
      document.getElementById('slowMoBtn').innerText = slowMo ? 'Normal speed (1x)' : 'Slow motion';
    }

    function playLearnAvatar() {
      const v = document.getElementById('learnAvatarVideo');
      v.currentTime = 0;
      v.play();
    }

    function handCloseUp() {
      const v = document.getElementById('learnAvatarVideo');
      v.style.transform = v.style.transform === 'scale(1.4)' ? 'scale(1)' : 'scale(1.4)';
      v.style.transition = 'transform 0.3s ease';
    }

    function recordAttempt() {
      const btn = document.getElementById('recordAttemptBtn');
      const badge = document.getElementById('learnCamStatusText');
      btn.innerText = 'Recording...';
      badge.innerText = 'Recording · 2.5s';

      setTimeout(() => {
        btn.innerText = 'Record attempt';
        badge.innerText = 'Attempt Recorded!';

        // Trigger score update
        fetch('/api/score', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ gloss: currentSign })
        })
        .then(r => r.json())
        .then(data => {
          document.getElementById('learnScoreRing').innerText = data.score;
          document.getElementById('learnScoreHeadline').innerText = data.grade;
          document.getElementById('learnScoreTip').innerText = 'Tip: ' + data.tip;
        });
      }, 2500);
    }

    function tryAgain() {
      document.getElementById('learnCamStatusText').innerText = 'Ready to sign';
      recordAttempt();
    }

    function nextLesson() {
      currentLessonIdx = (currentLessonIdx + 1) % signOrder.length;
      loadLearnSign(signOrder[currentLessonIdx]);
    }

    // --- SIGN LIBRARY ---
    function renderLibrary() {
      fetch('/api/signs')
        .then(r => r.json())
        .then(data => {
          const grid = document.getElementById('libraryGrid');
          grid.innerHTML = '';
          for (const [gloss, info] of Object.entries(data)) {
            const card = document.createElement('div');
            card.className = 'lib-card';
            card.innerHTML = `
              <div class="lib-badge">${info.category}</div>
              <div class="lib-title">${gloss}</div>
              <div class="lib-sub">English: "${info.english}"</div>
              <div style="font-size: 0.8rem; color: #0d695e; font-weight: 600;">✓ 3 / 3 templates recorded</div>
              <div style="display: flex; gap: 8px; margin-top: 8px;">
                <button class="btn-light-mint" style="flex: 1;" onclick="practiceSign('${gloss}')">Practice in Learn</button>
              </div>
            `;
            grid.appendChild(card);
          }
        });
    }

    function practiceSign(gloss) {
      currentSign = gloss;
      switchTab('learn');
      loadLearnSign(gloss);
    }

    function toggleMic() {
      const btn = document.querySelector('.btn-mic span');
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new SpeechRec();
        rec.lang = 'en-US';
        btn.innerText = 'Listening...';
        rec.onresult = (e) => {
          document.getElementById('signerInput').value = e.results[0][0].transcript;
          btn.innerText = 'Mic';
          signIt();
        };
        rec.onerror = () => { btn.innerText = 'Mic'; };
        rec.start();
      } else {
        alert('Voice dictation active. Type your phrase or use preset chips.');
      }
    }

    // --- PROCEDURAL HAND SKELETON ANIMATION ON CANVAS ---
    const camCanvas = document.getElementById('camCanvas');
    const camCtx = camCanvas.getContext('2d');
    const learnCanvas = document.getElementById('learnCamCanvas');
    const learnCtx = learnCanvas.getContext('2d');

    function resizeCanvases() {
      camCanvas.width = camCanvas.parentElement.clientWidth;
      camCanvas.height = camCanvas.parentElement.clientHeight;
      learnCanvas.width = learnCanvas.parentElement.clientWidth;
      learnCanvas.height = learnCanvas.parentElement.clientHeight;
    }
    window.addEventListener('resize', resizeCanvases);
    setTimeout(resizeCanvases, 200);

    let animTime = 0;
    function drawHandSkeleton(ctx, width, height) {
      ctx.clearRect(0, 0, width, height);

      // Deep dark navy camera background
      ctx.fillStyle = '#0c1524';
      ctx.fillRect(0, 0, width, height);

      // Draw stylized 5-finger turquoise fan matching mockup graphic!
      const rootX = width * 0.52;
      const rootY = height * 0.76;
      animTime += 0.03;

      const fingerAngles = [-0.65, -0.35, 0.0, 0.35, 0.65];
      const fingerLengths = [height * 0.38, height * 0.44, height * 0.48, height * 0.43, height * 0.36];

      ctx.lineWidth = 4;
      ctx.lineCap = 'round';

      for (let i = 0; i < 5; i++) {
        const angle = fingerAngles[i] - Math.PI / 2 + Math.sin(animTime + i * 0.5) * 0.05;
        const len = fingerLengths[i];
        const tipX = rootX + Math.cos(angle) * len;
        const tipY = rootY + Math.sin(angle) * len;

        // Line
        ctx.strokeStyle = '#2dd4bf';
        ctx.beginPath();
        ctx.moveTo(rootX, rootY);
        ctx.lineTo(tipX, tipY);
        ctx.stroke();

        // Glowing circular joint dot
        ctx.fillStyle = '#2dd4bf';
        ctx.beginPath();
        ctx.arc(tipX, tipY, 7, 0, Math.PI * 2);
        ctx.fill();
      }

      // Root wrist dot
      ctx.fillStyle = '#2dd4bf';
      ctx.beginPath();
      ctx.arc(rootX, rootY, 9, 0, Math.PI * 2);
      ctx.fill();
    }

    function renderLoop() {
      if (camCanvas.width > 0) drawHandSkeleton(camCtx, camCanvas.width, camCanvas.height);
      if (learnCanvas.width > 0) drawHandSkeleton(learnCtx, learnCanvas.width, learnCanvas.height);
      requestAnimationFrame(renderLoop);
    }
    renderLoop();

    // Start with default sign
    simulateSign('HOW-ARE-YOU');
  </script>
</body>
</html>
"""
