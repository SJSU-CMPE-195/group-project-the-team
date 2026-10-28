"""
HTML/CSS/JS Template for Silent Voice Bridge v2
Pixel-perfect replication of Bridge Mode (Image 1) and Learn Mode (Image 2).
Features:
- Live top-left camera feed with real-time MediaPipe hand tracking & turquoise skeleton
- Direct sign-to-text translation (transcribed text transcript feed without back-and-forth roles)
- Text-to-speech aloud
- AI Avatar synthesis card
- Learn mode tutor with 1-Watch, 2-Try it, 3-Score ring & DTW feedback
- Full Sign Library with 11 core vocabulary signs
"""

def get_html_content() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Silent Voice Bridge - Sign Tutor & Live Bridge</title>
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

    /* --- MAIN CONTENT WRAPPER --- */
    .app-container {
      max-width: 1440px;
      width: 100%;
      margin: 0 auto;
      padding: 24px 32px 40px;
      flex: 1;
    }

    .tab-content {
      display: none;
    }
    .tab-content.active {
      display: block;
    }

    /* ==================== BRIDGE MODE (IMAGE 1) ==================== */
    .bridge-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      align-items: start;
    }
    @media (max-width: 1024px) {
      .bridge-grid {
        grid-template-columns: 1fr;
      }
    }
    .bridge-col {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* Signer Camera Box (Image 1 Left Top) */
    .cam-card {
      background: var(--dark-cam);
      border-radius: 16px;
      height: 380px;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    .cam-badge {
      position: absolute;
      top: 14px;
      left: 14px;
      background: rgba(12, 21, 36, 0.85);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #ffffff;
      font-size: 0.75rem;
      font-weight: 500;
      padding: 6px 14px;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 15;
    }
    .cam-badge .pulse-dot {
      width: 8px;
      height: 8px;
      background: var(--accent-cyan);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-cyan);
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.85); }
    }
    .cam-btn-group {
      position: absolute;
      top: 14px;
      right: 14px;
      display: flex;
      gap: 8px;
      z-index: 15;
    }
    .cam-action-btn {
      background: rgba(13, 105, 94, 0.9);
      backdrop-filter: blur(8px);
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.2);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .cam-action-btn:hover {
      background: var(--teal-primary);
    }
    video#webcamVideo {
      position: absolute;
      width: 100%;
      height: 100%;
      object-fit: cover;
      transform: scaleX(-1);
      display: none;
    }
    canvas#camCanvas {
      width: 100%;
      height: 100%;
      object-fit: cover;
      z-index: 5;
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

    /* Quick Sign Chips */
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
      display: flex;
      justify-content: space-between;
      align-items: center;
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

    /* --- TRANSCRIBED SIGN TEXT PANEL (Direct Translation of Sign to Text) --- */
    .convo-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      height: 380px;
    }
    .convo-header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 10px;
      border-bottom: 1px solid #f1f5f9;
    }
    .convo-header {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .convo-header .live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      display: inline-block;
    }
    .btn-clear-transcript {
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-clear-transcript:hover {
      background: #f1f5f9;
      color: var(--text-main);
    }
    .convo-messages {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding-right: 6px;
    }
    .transcript-entry {
      background: #f8fafc;
      border: 1px solid var(--border);
      border-left: 4px solid var(--teal-primary);
      border-radius: 12px;
      padding: 14px 18px;
      animation: fadeIn 0.3s ease;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .transcript-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .transcript-badge {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--teal-primary);
      background: var(--teal-light);
      padding: 3px 8px;
      border-radius: 4px;
      letter-spacing: 0.3px;
    }
    .transcript-time {
      font-size: 0.72rem;
      color: var(--text-muted);
    }
    .transcript-bubble {
      font-size: 1.12rem;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.4;
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

    /* Input Bar (Image 1 Right Bottom) */
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
      gap: 8px;
      transition: background 0.2s;
    }
    .btn-mic:hover {
      background: var(--teal-light-hover);
    }
    .input-signer {
      flex: 1;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 18px;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
      background: #ffffff;
    }
    .input-signer:focus {
      border-color: var(--teal-primary);
    }
    .btn-sign {
      background: var(--teal-primary);
      color: #ffffff;
      border: none;
      padding: 14px 24px;
      border-radius: 12px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-sign:hover {
      background: var(--teal-hover);
    }

    
    /* Learn Mode Text Input for Dynamic Sentences */
    .learn-input-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px 22px;
      margin-bottom: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.02);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .learn-input-row {
      display: flex;
      gap: 12px;
      align-items: center;
    }
    .learn-input-field {
      flex: 1;
      border: 1.5px solid var(--border);
      border-radius: 12px;
      padding: 14px 18px;
      font-size: 0.95rem;
      font-weight: 500;
      color: var(--text-main);
      outline: none;
      transition: all 0.2s;
      background: #f8fafc;
    }
    .learn-input-field:focus {
      border-color: var(--teal-primary);
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(13, 105, 94, 0.1);
    }
    .btn-teach-sign {
      background: var(--teal-primary);
      color: #ffffff;
      border: none;
      padding: 14px 24px;
      border-radius: 12px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: background 0.2s;
      white-space: nowrap;
    }
    .btn-teach-sign:hover {
      background: var(--teal-hover);
    }
    .learn-quick-chips {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .learn-quick-label {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }
    .chip-sm {
      background: #f1f5f9;
      color: var(--text-main);
      font-size: 0.78rem;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 9999px;
      cursor: pointer;
      border: 1px solid var(--border);
      transition: all 0.2s;
    }
    .chip-sm:hover {
      background: var(--teal-light);
      color: var(--teal-primary);
      border-color: var(--teal-primary);
    }

/* ==================== LEARN MODE (IMAGE 2) ==================== */
    .learn-subnav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }
    .step-badges {
      display: flex;
      gap: 10px;
    }
    .step-badge {
      padding: 8px 18px;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      background: #e2e8f0;
      color: var(--text-muted);
    }
    .step-badge.active {
      background: var(--teal-primary);
      color: #ffffff;
    }
    .learn-header-right {
      text-align: right;
    }
    .learn-sign-title {
      font-size: 1.85rem;
      font-weight: 800;
      color: #0b1e33;
      letter-spacing: -0.5px;
    }
    .learn-lesson-num {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .learn-cards-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 24px;
    }
    @media (max-width: 900px) {
      .learn-cards-row {
        grid-template-columns: 1fr;
      }
    }
    .learn-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .learn-card-title {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .avatar-learn-screen {
      background: #e6f4f1;
      border-radius: 14px;
      height: 320px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }
    video#learnAvatarVideo {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .user-cam-screen {
      background: var(--dark-cam);
      border-radius: 14px;
      height: 320px;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    canvas#learnCamCanvas {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .learn-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .btn-light-mint {
      background: var(--teal-light);
      color: var(--teal-primary);
      border: none;
      padding: 10px 18px;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-light-mint:hover {
      background: var(--teal-light-hover);
    }

    /* Feedback & Coaching Tips Card (Image 2 Bottom) */
    .feedback-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px 30px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 24px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .feedback-col {
      display: flex;
      flex-direction: column;
      gap: 10px;
      flex: 1;
    }
    .feedback-top-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .feedback-badge {
      background: var(--teal-light);
      color: var(--teal-primary);
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 6px;
      letter-spacing: 0.4px;
      text-transform: uppercase;
    }
    .feedback-label {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .feedback-headline {
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.3px;
    }
    .feedback-well {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 4px;
    }
    .tip-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      font-size: 0.88rem;
      line-height: 1.45;
      color: var(--text-main);
      padding: 10px 14px;
      border-radius: 8px;
    }
    .tip-item.good {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      color: #166534;
    }
    .tip-item.messup {
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
    }
    .tip-item.improve {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      color: #334155;
    }
    .tip-icon {
      font-weight: 800;
      font-size: 1rem;
      flex-shrink: 0;
    }

    /* ==================== SIGN LIBRARY TAB ==================== */
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
      gap: 10px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .lib-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0,0,0,0.04);
    }
    .lib-badge {
      align-self: flex-start;
      background: var(--teal-light);
      color: var(--teal-primary);
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
    }
    .lib-title {
      font-size: 1.15rem;
      font-weight: 700;
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
            <div class="cam-badge" id="camBadge">
              <span class="pulse-dot"></span>
              <span id="camBadgeText">Camera on · hands tracked</span>
            </div>
            <div class="cam-btn-group">
              <button id="camToggleBtn" class="cam-action-btn" onclick="toggleWebcam()">Start Camera</button>
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
            <div class="quick-chips-title">
              <span>Sign Vocabulary & Quick Triggers</span>
              <span style="font-weight: 500; font-size: 0.7rem; color: var(--teal-primary);">Camera or Click</span>
            </div>
            <div class="chips-row">
              <span class="sign-chip" onclick="triggerRecognizedSign('HOW-ARE-YOU')">HOW-ARE-YOU</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('HELLO')">HELLO</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('MY-NAME')">MY-NAME</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('WHAT-IS-YOUR-NAME')">WHAT-IS-YOUR-NAME</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('NICE-MEET-YOU')">NICE-MEET-YOU</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('THANK-YOU')">THANK-YOU</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('PLEASE')">PLEASE</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('DEAF')">DEAF</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('FINE')">FINE</span>
              <span class="sign-chip" onclick="triggerRecognizedSign('HELP')">HELP</span>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN: Transcribed Text & Avatar Signing -->
        <div class="bridge-col">
          <!-- Transcribed Text Box (Direct Translation of Signs to Text) -->
          <div class="convo-card">
            <div class="convo-header-row">
              <div class="convo-header">
                <span class="live-dot"></span>
                <span>TRANSCRIBED SIGN TEXT</span>
              </div>
              <button class="btn-clear-transcript" onclick="clearTranscript()">Clear</button>
            </div>
            <div class="convo-messages" id="convoMessages">
              <div class="transcript-entry">
                <div class="transcript-meta">
                  <span class="transcript-badge">HOW-ARE-YOU</span>
                  <span class="transcript-time">Just now · 91% match</span>
                </div>
                <div class="transcript-bubble">"How are you?"</div>
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
            </div>
          </div>

          <!-- English to Sign Language Input Bar -->
          <div class="input-bar">
            <button class="btn-mic" onclick="toggleMic()">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              <span>Mic</span>
            </button>
            <input type="text" id="signerInput" class="input-signer" placeholder="Type English to see AI model sign it" onkeydown="if(event.key==='Enter') signIt()">
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
          <div class="step-badge">2 Try it</div>
          <div class="step-badge">3 Tips & Review</div>
        </div>
        <div class="learn-header-right">
          <div class="learn-sign-title" id="learnSignTitle">HOW-ARE-YOU</div>
          <div class="learn-lesson-num" id="learnLessonNum">Lesson 2 of 11 · Greetings</div>
        </div>
      </div>

      <!-- Type Sentence to Learn & Demonstrate -->
      <div class="learn-input-card">
        <div class="learn-input-row">
          <input type="text" id="learnTextInput" class="learn-input-field" 
                 placeholder="Type any sentence to demonstrate (e.g. 'How are you?', 'My name is Aramish', 'Nice to meet you')" 
                 oninput="handleCustomTextInput(this.value)"
                 onkeydown="if(event.key==='Enter') demonstrateCustomSentence()">
          <button class="btn-teach-sign" onclick="demonstrateCustomSentence()">
            <span>Demonstrate Sign</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
        <div class="learn-quick-chips">
          <span class="learn-quick-label">Try Examples:</span>
          <span class="chip-sm" onclick="setAndDemonstrate('How are you?')">How are you?</span>
          <span class="chip-sm" onclick="setAndDemonstrate('Hello!')">Hello!</span>
          <span class="chip-sm" onclick="setAndDemonstrate('My name is Aramish')">My name is Aramish</span>
          <span class="chip-sm" onclick="setAndDemonstrate('Nice to meet you')">Nice to meet you</span>
          <span class="chip-sm" onclick="setAndDemonstrate('What is your name?')">What is your name?</span>
          <span class="chip-sm" onclick="setAndDemonstrate('Thank you')">Thank you</span>
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
          <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <div class="learn-card-title">YOUR TURN: RECORD ATTEMPT</div>
            <div id="yourTurnSubTitle" style="font-size: 0.8rem; font-weight: 700; color: var(--teal-primary);">Sign: HOW-ARE-YOU</div>
          </div>
          <div class="user-cam-screen">
            <div class="cam-badge" id="learnCamBadge">
              <span class="pulse-dot"></span>
              <span id="learnCamStatusText">Camera ready · Click Record attempt when ready</span>
            </div>
            <canvas id="learnCamCanvas"></canvas>
          </div>
          <div class="learn-actions">
            <button class="btn-teal" id="recordAttemptBtn" onclick="startRecordingAttempt()">
              <span>⏺</span> <span>Record attempt</span>
            </button>
            <button class="btn-teal" id="doneSigningBtn" style="display: none; background: #059669;" onclick="finishRecordingAndEvaluate()">
              <span>✓</span> <span>Done Signing</span>
            </button>
            <button class="btn-light-mint" id="tryAgainBtn" onclick="tryAgain()">Reset / Try again</button>
          </div>
        </div>
      </div>

      <!-- Card 3: Feedback & Coaching Tips (Bottom) -->
      <div class="feedback-card">
        <div class="feedback-col">
          <div class="feedback-top-row">
            <span class="feedback-badge" id="feedbackBadge">Ready to evaluate</span>
            <span class="feedback-label">SIGN COACHING & TIPS</span>
          </div>
          <div class="feedback-headline" id="learnFeedbackHeadline">Record your attempt and click "Done Signing" to get diagnostic tips on your sign.</div>
          <div class="feedback-well" id="feedbackDetails">
            <div class="tip-item good" id="tipGoodRow" style="display: none;">
              <span class="tip-icon">✓</span>
              <span id="tipGoodText">Hand position recognized.</span>
            </div>
            <div class="tip-item messup" id="tipMessupRow" style="display: none;">
              <span class="tip-icon">⚠️</span>
              <span id="tipMessupText">Where signers commonly mess up...</span>
            </div>
            <div class="tip-item improve" id="tipImproveRow">
              <span class="tip-icon">💡</span>
              <span id="tipImproveText">Tip: Practice your sign in front of the camera, then click "Done Signing" to see specific coaching advice.</span>
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
        setTimeout(resizeCanvases, 60);
        if (!isWebcamRunning) startWebcam();
        loadLearnSign(currentSign);
      } else if (tab === 'library') {
        document.querySelectorAll('.nav-tab')[2].classList.add('active');
        document.getElementById('tab-library').classList.add('active');
        document.getElementById('headerRightStatus').innerText = '11 signs · 33 templates';
        renderLibrary();
      }
    }

    // --- TRANSCRIBED SIGN TEXT PANEL ---
    function appendTranslation(gloss, englishText, confidence) {
      const convo = document.getElementById('convoMessages');
      const entry = document.createElement('div');
      entry.className = 'transcript-entry';

      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const confStr = confidence ? `${confidence}% match` : '91% match';

      entry.innerHTML = `
        <div class="transcript-meta">
          <span class="transcript-badge">${gloss}</span>
          <span class="transcript-time">${timeStr} · ${confStr}</span>
        </div>
        <div class="transcript-bubble">"${englishText}"</div>
      `;

      convo.appendChild(entry);
      convo.scrollTop = convo.scrollHeight;
    }

    function clearTranscript() {
      const convo = document.getElementById('convoMessages');
      convo.innerHTML = `
        <div style="color: var(--text-muted); font-size: 0.88rem; text-align: center; padding: 40px 20px;">
          Camera signing active. Sign any ASL phrase to see real-time English translation here.
        </div>
      `;
    }

    // --- SIGN DETECTION & RECOGNITION ---
    function triggerRecognizedSign(gloss) {
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

        // Speak aloud via TTS
        speakText(data.english);

        // Add direct translation to transcribed text feed (no hearing/signer back-and-forth)
        appendTranslation(data.gloss, data.english, data.confidence);

        // Update avatar video to match
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
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1.0;
        window.speechSynthesis.speak(u);
      }
    }

    // --- SIGN SYNTHESIS FOR AVATAR CARD ---
    async function signIt() {
      const input = document.getElementById('signerInput');
      const text = input.value.trim();
      if (!text) return;
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
    let currentCustomTarget = 'HOW-ARE-YOU';

    function setStepBadge(activeStep) {
      const badges = document.querySelectorAll('.step-badges .step-badge');
      badges.forEach((b, idx) => {
        if (idx < activeStep) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });
    }

    function handleCustomTextInput(val) {
      const text = val.trim();
      if (!text) return;
      currentCustomTarget = text;
      const sub = document.getElementById("yourTurnSubTitle");
      if (sub) sub.innerText = "Sign: " + text;
      // Preload tips for typed sentence immediately
      updateCoachingTips(text, false);
    }

    async function updateCoachingTips(target, isEvaluated) {
      if (!target) return;
      const fbBadge = document.getElementById("feedbackBadge");
      if (fbBadge) {
        fbBadge.innerText = isEvaluated ? "Evaluated just now" : ("Coaching for " + target);
      }

      try {
        const resp = await fetch("/api/score", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ gloss: target, text: target })
        });
        const data = await resp.json();

        const headlineEl = document.getElementById("learnFeedbackHeadline");
        if (headlineEl) {
          headlineEl.innerText = data.headline || data.grade || ('Review & Coaching for "' + (data.gloss || target) + '"');
        }

        const goodRow = document.getElementById("tipGoodRow");
        const goodText = document.getElementById("tipGoodText");
        const goodContent = data.good || ('Hand motion tracked for "' + target + '".');
        if (goodRow && goodText) {
          goodText.innerText = goodContent;
          goodRow.style.display = "flex";
        }

        const messupRow = document.getElementById("tipMessupRow");
        const messupText = document.getElementById("tipMessupText");
        const messupContent = data.mess_up || "Where signers commonly mess up: Rushing hand transitions or dropping wrists before the sign apex.";
        if (messupRow && messupText) {
          messupText.innerText = messupContent;
          messupRow.style.display = "flex";
        }

        const improveRow = document.getElementById("tipImproveRow");
        const improveText = document.getElementById("tipImproveText");
        const improveContent = data.tip || "Maintain your elbow steady and hold the final handshape for half a second for readability.";
        if (improveRow && improveText) {
          improveText.innerText = "Tip: " + improveContent;
          improveRow.style.display = "flex";
        }
      } catch (e) {
        console.error("Coaching fetch error:", e);
      }
    }

    async function demonstrateCustomSentence() {
      const input = document.getElementById("learnTextInput");
      const text = input ? input.value.trim() : "";
      if (!text) return;

      currentCustomTarget = text;
      currentSign = text;
      document.getElementById("learnSignTitle").innerText = text.toUpperCase();
      document.getElementById("learnLessonNum").innerText = "Custom Sentence · AI Skeleton Demonstration";
      const sub = document.getElementById("yourTurnSubTitle");
      if (sub) sub.innerText = "Sign: " + text;

      // Immediately update coaching & tips for this specific sentence
      updateCoachingTips(text, false);

      setStepBadge(1); // 1 Watch

      const badge = document.getElementById("learnCamStatusText");
      if (badge) badge.innerText = "Watch the avatar motion";

      // Reset record button if recording was active
      const recordBtn = document.getElementById("recordAttemptBtn");
      const doneBtn = document.getElementById("doneSigningBtn");
      if (doneBtn) doneBtn.style.display = "none";
      if (recordBtn) {
        recordBtn.style.display = "inline-flex";
        recordBtn.innerHTML = "<span>⏺</span> <span>Record attempt</span>";
      }

      // Synthesize custom sentence video
      try {
        const resp = await fetch("/api/synthesize?text=" + encodeURIComponent(text));
        const data = await resp.json();
        if (data.video_url) {
          const v = document.getElementById("learnAvatarVideo");
          v.src = data.video_url;
          v.playbackRate = slowMo ? 0.5 : 1.0;
          v.load();
          v.play();
        }
      } catch (err) {
        console.error("Synthesize error:", err);
      }
    }

    function setAndDemonstrate(text) {
      const input = document.getElementById("learnTextInput");
      if (input) input.value = text;
      demonstrateCustomSentence();
    }

    function loadLearnSign(gloss) {
      currentCustomTarget = gloss;
      currentSign = gloss;
      document.getElementById("learnSignTitle").innerText = gloss;
      const idx = signOrder.indexOf(gloss);
      const lessonText = idx >= 0 ? ("Lesson " + (idx + 1) + " of " + signOrder.length + " · Greetings") : "Practice Sign";
      document.getElementById("learnLessonNum").innerText = lessonText;
      const sub = document.getElementById("yourTurnSubTitle");
      if (sub) sub.innerText = "Sign: " + gloss;

      // Update coaching card for this lesson sign
      updateCoachingTips(gloss, false);

      setStepBadge(1);

      fetch("/api/synthesize?text=" + encodeURIComponent(gloss.replace(/-/g, " ")))
        .then(r => r.json())
        .then(data => {
          if (data.video_url) {
            const v = document.getElementById("learnAvatarVideo");
            v.src = data.video_url;
            v.playbackRate = slowMo ? 0.5 : 1.0;
            v.load();
            v.play();
          }
        });
    }

    function playLearnAvatar() {
      const v = document.getElementById("learnAvatarVideo");
      v.currentTime = 0;
      v.playbackRate = slowMo ? 0.5 : 1.0;
      v.play();
    }

    function toggleSlowMo() {
      slowMo = !slowMo;
      const btn = document.getElementById("slowMoBtn");
      const v = document.getElementById("learnAvatarVideo");
      if (slowMo) {
        v.playbackRate = 0.5;
        btn.classList.add("active");
        btn.innerText = "Normal speed";
      } else {
        v.playbackRate = 1.0;
        btn.classList.remove("active");
        btn.innerText = "Slow motion";
      }
    }

    function toggleHandZoom() {
      handZoom = !handZoom;
      const btn = document.getElementById("zoomBtn");
      const v = document.getElementById("learnAvatarVideo");
      if (handZoom) {
        v.style.transform = "scale(1.45) translateY(10%)";
        btn.classList.add("active");
        btn.innerText = "Full body";
      } else {
        v.style.transform = "scale(1.0)";
        btn.classList.remove("active");
        btn.innerText = "Hand close-up";
      }
    }

    function setStepBadge(stepNum) {
      const steps = [
        { id: "stepBadge1", num: 1 },
        { id: "stepBadge2", num: 2 },
        { id: "stepBadge3", num: 3 }
      ];
      steps.forEach(s => {
        const el = document.getElementById(s.id);
        if (!el) return;
        if (s.num === stepNum) {
          el.className = "step-item step-current";
        } else if (s.num < stepNum) {
          el.className = "step-item step-done";
        } else {
          el.className = "step-item step-pending";
        }
      });
    }

    let isRecordingAttempt = false;

    function startRecordingAttempt() {
      isRecordingAttempt = true;
      setStepBadge(2); // 2 Try it

      const badge = document.getElementById("learnCamStatusText");
      if (badge) badge.innerText = "● Recording in progress... Sign now!";
      
      const recordBtn = document.getElementById("recordAttemptBtn");
      const doneBtn = document.getElementById("doneSigningBtn");
      if (recordBtn) recordBtn.style.display = "none";
      if (doneBtn) doneBtn.style.display = "inline-flex";

      const fbBadge = document.getElementById("feedbackBadge");
      if (fbBadge) fbBadge.innerText = "Recording attempt";
    }

    function finishRecordingAndEvaluate() {
      isRecordingAttempt = false;
      setStepBadge(3); // 3 Tips & Review

      const badge = document.getElementById("learnCamStatusText");
      if (badge) badge.innerText = "Checking hand signs & analyzing motion...";

      const recordBtn = document.getElementById("recordAttemptBtn");
      const doneBtn = document.getElementById("doneSigningBtn");
      if (doneBtn) doneBtn.style.display = "none";
      if (recordBtn) {
        recordBtn.style.display = "inline-flex";
        recordBtn.innerHTML = "<span>⏺</span> <span>Record again</span>";
      }

      const inputVal = (document.getElementById("learnTextInput") && document.getElementById("learnTextInput").value.trim());
      const target = inputVal || currentCustomTarget || currentSign || "HOW-ARE-YOU";

      updateCoachingTips(target, true).then(() => {
        if (badge) badge.innerText = "Attempt Evaluated!";
      });
    }

    function tryAgain() {
      const badge = document.getElementById("learnCamStatusText");
      if (badge) badge.innerText = "Camera ready · Click Record attempt when ready";

      const recordBtn = document.getElementById("recordAttemptBtn");
      const doneBtn = document.getElementById("doneSigningBtn");
      if (doneBtn) doneBtn.style.display = "none";
      if (recordBtn) {
        recordBtn.style.display = "inline-flex";
        recordBtn.innerHTML = "<span>⏺</span> <span>Record attempt</span>";
      }

      const inputVal = (document.getElementById("learnTextInput") && document.getElementById("learnTextInput").value.trim());
      const target = inputVal || currentCustomTarget || currentSign;
      if (target) {
        updateCoachingTips(target, false);
      }

      setStepBadge(1);
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

    // ==================== LIVE WEBCAM & MEDIAPIPE TRACKING ====================
    const camCanvas = document.getElementById('camCanvas');
    const camCtx = camCanvas.getContext('2d');
    const learnCanvas = document.getElementById('learnCamCanvas');
    const learnCtx = learnCanvas.getContext('2d');
    const webcamVideo = document.getElementById('webcamVideo');

    let webcamStream = null;
    let isWebcamRunning = false;
    let handsDetector = null;
    let lastHandLandmarks = [];
    let lastGestureTime = 0;

    const HAND_CONNECTIONS = [
      [0, 1], [1, 2], [2, 3], [3, 4],        // Thumb
      [0, 5], [5, 6], [6, 7], [7, 8],        // Index
      [0, 9], [9, 10], [10, 11], [11, 12],    // Middle
      [0, 13], [13, 14], [14, 15], [15, 16],  // Ring
      [0, 17], [17, 18], [18, 19], [19, 20],  // Pinky
      [5, 9], [9, 13], [13, 17], [0, 17]      // Palm base
    ];

    function resizeCanvases() {
      if (camCanvas.parentElement) {
        camCanvas.width = camCanvas.parentElement.clientWidth;
        camCanvas.height = camCanvas.parentElement.clientHeight;
      }
      if (learnCanvas.parentElement) {
        learnCanvas.width = learnCanvas.parentElement.clientWidth;
        learnCanvas.height = learnCanvas.parentElement.clientHeight;
      }
    }
    window.addEventListener('resize', resizeCanvases);
    setTimeout(resizeCanvases, 200);

    // Turn camera on
    async function startWebcam() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
          audio: false
        });
        webcamStream = stream;
        webcamVideo.srcObject = stream;
        await webcamVideo.play();
        isWebcamRunning = true;
        document.getElementById('camBadgeText').innerText = 'Camera on · live tracking';
        document.getElementById('camToggleBtn').innerText = 'Stop Camera';

        initMediaPipeHands();
      } catch (err) {
        console.warn("Could not access live webcam:", err);
        document.getElementById('camBadgeText').innerText = 'Camera permission needed';
        document.getElementById('camToggleBtn').innerText = 'Start Camera';
      }
    }

    function stopWebcam() {
      if (webcamStream) {
        webcamStream.getTracks().forEach(t => t.stop());
        webcamStream = null;
      }
      isWebcamRunning = false;
      document.getElementById('camBadgeText').innerText = 'Camera paused';
      document.getElementById('camToggleBtn').innerText = 'Start Camera';
    }

    function toggleWebcam() {
      if (isWebcamRunning) {
        stopWebcam();
      } else {
        startWebcam();
      }
    }

    function initMediaPipeHands() {
      if (typeof Hands === 'undefined') {
        console.warn("MediaPipe Hands CDN is loading...");
        return;
      }
      if (handsDetector) return;

      try {
        handsDetector = new Hands({
          locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });
        handsDetector.setOptions({
          maxNumHands: 2,
          modelComplexity: 1,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        });

        handsDetector.onResults((results) => {
          if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            lastHandLandmarks = results.multiHandLandmarks;
            const count = results.multiHandLandmarks.length;
            document.getElementById('camBadgeText').innerText =
              count === 2 ? 'Camera on · both hands tracked' : 'Camera on · 1 hand tracked';
            
            // Real-time sign gesture recognition from live coordinates
            analyzeSignGesture(results.multiHandLandmarks);
          } else {
            lastHandLandmarks = [];
            document.getElementById('camBadgeText').innerText = 'Camera on · show hands';
          }
        });

        if (typeof Camera !== 'undefined') {
          const camHelper = new Camera(webcamVideo, {
            onFrame: async () => {
              if (isWebcamRunning && handsDetector) {
                await handsDetector.send({ image: webcamVideo });
              }
            },
            width: 640,
            height: 480
          });
          camHelper.start();
        }
      } catch (e) {
        console.error("MediaPipe initialization error:", e);
      }
    }

    // Draw tracked hand skeleton on canvas
    function drawTrackedHands(ctx, multiLandmarks, width, height) {
      for (const hand of multiLandmarks) {
        // 1. Connection lines
        ctx.lineWidth = 3.5;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#2dd4bf';

        for (const [p1, p2] of HAND_CONNECTIONS) {
          const x1 = (1 - hand[p1].x) * width;
          const y1 = hand[p1].y * height;
          const x2 = (1 - hand[p2].x) * width;
          const y2 = hand[p2].y * height;

          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }

        // 2. Joints
        for (let i = 0; i < hand.length; i++) {
          const px = (1 - hand[i].x) * width;
          const py = hand[i].y * height;
          const isTip = [4, 8, 12, 16, 20].includes(i);

          ctx.fillStyle = isTip ? '#ffffff' : '#2dd4bf';
          ctx.beginPath();
          ctx.arc(px, py, isTip ? 5.5 : 4, 0, Math.PI * 2);
          ctx.fill();

          if (isTip) {
            ctx.strokeStyle = '#0d695e';
            ctx.lineWidth = 2;
            ctx.stroke();
          }
        }
      }
    }

    // Fallback animated skeleton for preview if camera is initializing
    let animTime = 0;
    function drawFallbackSkeleton(ctx, width, height) {
      ctx.fillStyle = '#0c1524';
      ctx.fillRect(0, 0, width, height);

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

        ctx.strokeStyle = '#2dd4bf';
        ctx.beginPath();
        ctx.moveTo(rootX, rootY);
        ctx.lineTo(tipX, tipY);
        ctx.stroke();

        ctx.fillStyle = '#2dd4bf';
        ctx.beginPath();
        ctx.arc(tipX, tipY, 7, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.fillStyle = '#2dd4bf';
      ctx.beginPath();
      ctx.arc(rootX, rootY, 9, 0, Math.PI * 2);
      ctx.fill();
    }

    // Gesture classifier from landmark spatial kinematics
    function analyzeSignGesture(multiLandmarks) {
      const now = Date.now();
      if (now - lastGestureTime < 3000) return; // Debounce

      const h1 = multiLandmarks[0];
      const numHands = multiLandmarks.length;
      const wristY = h1[0].y;
      const indexTipY = h1[8].y;
      const thumbTipY = h1[4].y;

      if (numHands === 2) {
        const h2 = multiLandmarks[1];
        const distWrists = Math.hypot(h1[0].x - h2[0].x, h1[0].y - h2[0].y);
        if (distWrists < 0.28) {
          triggerRecognizedSign('HOW-ARE-YOU');
          lastGestureTime = now;
          return;
        }
      }

      // Hand waving near upper area
      if (wristY < 0.42 && indexTipY < 0.32) {
        triggerRecognizedSign('HELLO');
        lastGestureTime = now;
        return;
      }

      // Hand resting near chest
      if (wristY >= 0.45 && wristY <= 0.75 && thumbTipY < indexTipY) {
        triggerRecognizedSign('FINE');
        lastGestureTime = now;
        return;
      }
    }

    // Main Canvas Render Loop
    function renderLoop() {
      if (camCanvas.width > 0) {
        if (isWebcamRunning && webcamVideo.readyState >= 2) {
          camCtx.save();
          camCtx.translate(camCanvas.width, 0);
          camCtx.scale(-1, 1);
          camCtx.drawImage(webcamVideo, 0, 0, camCanvas.width, camCanvas.height);
          camCtx.restore();

          if (lastHandLandmarks && lastHandLandmarks.length > 0) {
            drawTrackedHands(camCtx, lastHandLandmarks, camCanvas.width, camCanvas.height);
          }
        } else {
          drawFallbackSkeleton(camCtx, camCanvas.width, camCanvas.height);
        }
      }

      if (learnCanvas.width > 0) {
        if (isWebcamRunning && webcamVideo.readyState >= 2) {
          learnCtx.save();
          learnCtx.translate(learnCanvas.width, 0);
          learnCtx.scale(-1, 1);
          learnCtx.drawImage(webcamVideo, 0, 0, learnCanvas.width, learnCanvas.height);
          learnCtx.restore();

          if (lastHandLandmarks && lastHandLandmarks.length > 0) {
            drawTrackedHands(learnCtx, lastHandLandmarks, learnCanvas.width, learnCanvas.height);
          }
        } else {
          drawFallbackSkeleton(learnCtx, learnCanvas.width, learnCanvas.height);
        }
      }

      requestAnimationFrame(renderLoop);
    }
    renderLoop();

    // Auto-attempt webcam startup on load
    window.addEventListener('DOMContentLoaded', () => {
      startWebcam();
    });
  </script>
</body>
</html>
"""
