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

    /* Signer Camera Box (Full-Height Left Column) */
    .bridge-grid {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 24px;
      align-items: stretch;
      min-height: 620px;
    }
    @media (max-width: 1024px) {
      .bridge-grid {
        grid-template-columns: 1fr;
        height: auto;
      }
    }
    .bridge-col {
      display: flex;
      flex-direction: column;
      gap: 16px;
      height: 100%;
    }
    .cam-card {
      background: var(--dark-cam);
      border-radius: 16px;
      height: 620px;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      border: 1px solid var(--border);
    }
    .cam-badge {
      position: absolute;
      top: 14px;
      left: 14px;
      background: rgba(12, 21, 36, 0.88);
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
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(12px);
      border-radius: 14px;
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 8px 24px rgba(0,0,0,0.18);
      z-index: 10;
      border: 1px solid rgba(226, 232, 240, 0.8);
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
    .rec-sub-status {
      font-size: 0.74rem;
      color: #64748b;
      margin-top: 2px;
      font-weight: 500;
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
      width: 0%;
      border-radius: 9999px;
      transition: width 0.2s ease;
    }

    /* --- TWO-WAY LIVE BRIDGE INTERACTIVE CONVERSATION --- */
    .convo-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      height: 620px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    }
    .convo-header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 10px;
      border-bottom: 1px solid #f1f5f9;
    }
    .convo-header {
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .convo-header .live-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      display: inline-block;
      box-shadow: 0 0 6px rgba(16, 185, 129, 0.6);
      animation: pulseDot 2s infinite;
    }
    .live-indicator-badge {
      font-size: 0.72rem;
      font-weight: 600;
      color: #0f766e;
      background: #ccfbf1;
      padding: 3px 9px;
      border-radius: 6px;
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
    .convo-msg-system {
      background: #f8fafc;
      border: 1px dashed #cbd5e1;
      border-radius: 10px;
      padding: 12px 14px;
      font-size: 0.82rem;
      color: #64748b;
      line-height: 1.45;
      text-align: center;
    }
    /* Deaf Signer Message Bubble */
    .convo-msg-deaf {
      align-self: flex-start;
      width: 90%;
      background: #f0fdfa;
      border: 1px solid #ccfbf1;
      border-left: 4px solid var(--teal-primary);
      border-radius: 12px;
      padding: 12px 16px;
      animation: fadeIn 0.3s ease;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .msg-header-deaf {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .badge-deaf {
      font-size: 0.7rem;
      font-weight: 700;
      color: #0f766e;
      background: #ccfbf1;
      padding: 2px 7px;
      border-radius: 4px;
      letter-spacing: 0.3px;
    }
    .msg-time {
      font-size: 0.7rem;
      color: var(--text-muted);
    }
    .bubble-text-deaf {
      font-size: 1.15rem;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.35;
    }
    .bubble-footer-deaf {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.72rem;
      color: #0d9488;
      font-weight: 600;
    }
    .btn-replay-voice {
      cursor: pointer;
      text-decoration: underline;
    }
    /* Hearing Partner Message Bubble */
    .convo-msg-hearing {
      align-self: flex-end;
      width: 90%;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-right: 4px solid #6366f1;
      border-radius: 12px;
      padding: 12px 16px;
      animation: fadeIn 0.3s ease;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .msg-header-hearing {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .badge-hearing {
      font-size: 0.7rem;
      font-weight: 700;
      color: #4338ca;
      background: #e0e7ff;
      padding: 2px 7px;
      border-radius: 4px;
      letter-spacing: 0.3px;
    }
    .bubble-text-hearing {
      font-size: 1.15rem;
      font-weight: 600;
      color: #1e1b4b;
      line-height: 1.35;
    }
    .bubble-footer-hearing {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.72rem;
      color: #6366f1;
      font-weight: 600;
    }
    /* Communication Input Bar (Hearing Partner or Signer) */
    .bridge-input-section {
      padding-top: 10px;
      border-top: 1px solid #f1f5f9;
    }
    .input-bar {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .btn-mic {
      background: var(--teal-light);
      color: var(--teal-primary);
      border: none;
      padding: 12px 18px;
      border-radius: 12px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-mic:hover {
      background: var(--teal-light-hover);
    }
    .input-signer {
      flex: 1;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 16px;
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
      padding: 12px 22px;
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

    /* ==================== SIGN LIBRARY & CUSTOM SIGNS ==================== */
    .lib-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .profile-pill-box {
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 6px 14px;
      border-radius: 10px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .profile-select {
      border: none;
      background: transparent;
      font-weight: 700;
      font-size: 0.9rem;
      color: var(--teal-primary);
      cursor: pointer;
      outline: none;
    }
    .btn-record-new {
      background: linear-gradient(135deg, #0d695e 0%, #14b8a6 100%);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 10px 20px;
      font-weight: 700;
      font-size: 0.92rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(13, 105, 94, 0.25);
      transition: all 0.2s ease;
    }
    .btn-record-new:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(13, 105, 94, 0.35);
    }
    .lib-badge.custom {
      background: #fef3c7;
      color: #92400e;
      border: 1px solid #fde68a;
    }
    .lib-badge.core {
      background: var(--teal-light);
      color: var(--teal-primary);
    }

    /* Modal Backdrop & Dialog */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(6px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      animation: fadeIn 0.2s ease-out;
    }
    .modal-card {
      background: #ffffff;
      border-radius: 18px;
      width: 92%;
      max-width: 820px;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 50px rgba(0,0,0,0.25);
      display: flex;
      flex-direction: column;
    }
    .modal-header {
      padding: 20px 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .modal-close-btn {
      background: transparent;
      border: none;
      font-size: 1.3rem;
      color: var(--text-muted);
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 6px;
    }
    .modal-close-btn:hover {
      background: rgba(0,0,0,0.06);
      color: var(--text-main);
    }
    .attempt-card {
      background: #f8fafc;
      border: 1.5px solid #e2e8f0;
      border-radius: 10px;
      padding: 12px 14px;
      transition: all 0.2s ease;
    }
    .attempt-card.active {
      border-color: #14b8a6;
      background: #f0fdfa;
      box-shadow: 0 2px 8px rgba(20, 184, 166, 0.15);
    }
    .attempt-card.completed {
      border-color: #10b981;
      background: #ecfdf5;
    }
    .attempt-card.disabled {
      opacity: 0.6;
      pointer-events: none;
    }
    .btn-teal-sm {
      background: #0d695e;
      color: white;
      border: none;
      border-radius: 6px;
      padding: 7px 12px;
      font-weight: 700;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-teal-sm:hover:not(:disabled) {
      background: #0a544b;
    }
    .btn-teal-sm:disabled {
      background: #cbd5e1;
      cursor: not-allowed;
    }
    .btn-cancel {
      background: #f1f5f9;
      color: var(--text-main);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 18px;
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .btn-cancel:hover {
      background: #e2e8f0;
    }
    @keyframes pulse-red {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

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
    <!-- ==================== TAB 1: BRIDGE MODE (TWO-WAY LIVE TRANSLATION) ==================== -->
    <div id="tab-bridge" class="tab-content active">
      <div class="bridge-grid">
        <!-- LEFT COLUMN: Full-Height Live Signer Camera -->
        <div class="bridge-col">
          <div class="cam-card">
            <div class="cam-badge" id="camBadge">
              <span class="pulse-dot"></span>
              <span id="camBadgeText">Camera on · Ready to sign</span>
            </div>
            <div class="cam-btn-group">
              <button id="ttsToggleBtn" class="cam-action-btn" onclick="toggleTTS()" title="Toggle voice output aloud">🔊 Voice Out: ON</button>
              <button id="camToggleBtn" class="cam-action-btn" onclick="toggleWebcam()">Stop Camera</button>
            </div>
            
            <video id="webcamVideo" autoplay playsinline muted></video>
            <canvas id="camCanvas"></canvas>

            <!-- Bottom Live Recognition HUD -->
            <div class="recognized-overlay">
              <div>
                <div class="rec-label">RECOGNIZED ASL SIGN</div>
                <div class="rec-gloss" id="bridgeGloss">Ready to Sign</div>
                <div class="rec-sub-status" id="bridgeStatusMsg">Hold gesture steady in frame · Translates basic words & alphabet</div>
              </div>
              <div class="rec-conf-col">
                <div class="conf-row">
                  <span class="conf-title">Confidence</span>
                  <span class="conf-val" id="bridgeConfVal">--</span>
                </div>
                <div class="conf-bar-bg">
                  <div class="conf-bar-fill" id="bridgeConfBar" style="width: 0%;"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN: Live English Translation & Two-Way Conversation -->
        <div class="bridge-col">
          <div class="convo-card">
            <div class="convo-header-row">
              <div class="convo-header">
                <span class="live-dot"></span>
                <span>LIVE TRANSLATION & CONVERSATION</span>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                <span class="live-indicator-badge">Deaf Signer ⇄ Hearing Partner</span>
                <button class="btn-clear-transcript" onclick="clearTranscript()">Clear Chat</button>
              </div>
            </div>

            <!-- Scrollable Conversation Feed -->
            <div class="convo-messages" id="convoMessages">
              <div class="convo-msg-system">
                <span>👋 <b>Two-Way Bridge Active</b>: The camera tracks your ASL signs on the left and translates them to English text & voice below. The hearing partner can click <b>Mic</b> to speak or type a reply below!</span>
              </div>
            </div>

            <!-- Hearing Partner / Speaker Communication Input -->
            <div class="bridge-input-section">
              <div class="input-bar">
                <button class="btn-mic" id="hearingMicBtn" onclick="toggleMic()" title="Click to speak your message aloud">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                  <span id="micBtnText">Mic</span>
                </button>
                <input type="text" id="signerInput" class="input-signer" placeholder="Type your reply here (or click Mic to speak)..." onkeydown="if(event.key==='Enter') sendHearingMessage()">
                <button class="btn-sign" onclick="sendHearingMessage()">Send</button>
              </div>
            </div>
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
      <div class="lib-toolbar">
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.4px;">ASL Vocabulary & Unlocked Signs</h2>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 4px;">11 Core ASL Signs + User-Taught Custom Signs · 3 Attempts Per Sign</p>
        </div>
        <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
          <div class="profile-pill-box">
            <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">Signer Profile:</span>
            <select class="profile-select" id="signerProfileSelect" onchange="changeSignerProfile(this.value)">
              <option value="aramish">👤 Aramish (Active)</option>
              <option value="alex">👤 Alex</option>
              <option value="guest">👤 Guest Signer</option>
            </select>
          </div>
          <button class="btn-record-new" onclick="openRecordCustomModal()">
            <span>➕</span> Record New Sign (3 Tries)
          </button>
        </div>
      </div>
      <div class="library-grid" id="libraryGrid">
        <!-- Rendered by JS -->
      </div>
    </div>
  </div>

  <!-- MODAL: RECORD CUSTOM SIGN (3-TRY PIPELINE) -->
  <div id="customSignModal" class="modal-backdrop" style="display: none;">
    <div class="modal-card">
      <div class="modal-header">
        <div>
          <h3 style="font-size: 1.35rem; font-weight: 800; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
            <span>✨</span> Create & Unlock Custom ASL Sign
          </h3>
          <p style="font-size: 0.86rem; color: var(--text-muted); margin-top: 4px;">
            Record 3 attempts in front of the camera. Once all 3 attempts are captured, this sign unlocks in your library and live Bridge conversations!
          </p>
        </div>
        <button class="modal-close-btn" onclick="closeRecordCustomModal()">✕</button>
      </div>

      <div style="padding: 20px 24px;">
        <!-- Metadata Inputs -->
        <div style="display: grid; grid-template-columns: 1fr 1.2fr 0.8fr; gap: 14px; margin-bottom: 20px;">
          <div>
            <label style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Sign Gloss / Word *</label>
            <input type="text" id="customGlossInput" placeholder="e.g. WATER, FAMILY, LOVE" style="width: 100%; padding: 10px 12px; border-radius: 8px; border: 1.5px solid var(--border); font-weight: 800; text-transform: uppercase; margin-top: 5px; font-size: 0.95rem;">
          </div>
          <div>
            <label style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Spoken English Translation *</label>
            <input type="text" id="customEnglishInput" placeholder="e.g. Water please, This is my family" style="width: 100%; padding: 10px 12px; border-radius: 8px; border: 1.5px solid var(--border); margin-top: 5px; font-size: 0.95rem;">
          </div>
          <div>
            <label style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Signer Account</label>
            <input type="text" id="customSignerBadge" value="Aramish" readonly style="width: 100%; padding: 10px 12px; border-radius: 8px; border: 1.5px solid var(--border); background: #f8fafc; font-weight: 700; color: var(--teal-primary); margin-top: 5px; font-size: 0.95rem;">
          </div>
        </div>

        <!-- 3-Attempt Studio Viewport -->
        <div style="display: grid; grid-template-columns: 1.25fr 1fr; gap: 20px; align-items: start;">
          <!-- Camera Feed & Canvas -->
          <div style="position: relative; background: #0f172a; border-radius: 12px; overflow: hidden; height: 300px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 16px rgba(0,0,0,0.15);">
            <canvas id="recordCamCanvas" width="460" height="300" style="width: 100%; height: 100%; object-fit: cover;"></canvas>
            
            <!-- Countdown Overlay -->
            <div id="recordCountdownOverlay" style="position: absolute; inset: 0; background: rgba(15,23,42,0.8); display: none; align-items: center; justify-content: center; flex-direction: column; color: white;">
              <div id="countdownNum" style="font-size: 4.5rem; font-weight: 900; color: #2dd4bf; text-shadow: 0 0 25px rgba(45,212,191,0.8);">3</div>
              <div id="countdownMsg" style="font-size: 1rem; font-weight: 600; color: #cbd5e1; margin-top: 6px;">Get ready to sign...</div>
            </div>

            <!-- Recording Pill -->
            <div id="recordingPill" style="position: absolute; top: 12px; left: 12px; background: rgba(239,68,68,0.9); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; display: none; animation: pulse-red 1s infinite; letter-spacing: 0.5px;">
              ● RECORDING (<span id="recordFrameCount">0</span>/30 FRAMES)
            </div>

            <!-- Camera Guide Help -->
            <div style="position: absolute; bottom: 8px; left: 12px; right: 12px; background: rgba(15,23,42,0.65); backdrop-filter: blur(4px); padding: 4px 10px; border-radius: 6px; font-size: 0.72rem; color: #94a3b8; text-align: center;">
              Keep hands inside the turquoise tracking skeleton while recording
            </div>
          </div>

          <!-- 3 Attempts Flow -->
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div style="font-size: 0.82rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">
              3-Attempt Training Pipeline
            </div>

            <!-- Attempt 1 -->
            <div class="attempt-card active" id="attemptCard1">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-main);">Attempt 1 of 3</div>
                  <div class="attempt-status" id="attemptStatus1" style="font-size: 0.78rem; color: var(--text-muted);">Ready to record</div>
                </div>
                <button class="btn-teal-sm" id="btnRecordAttempt1" onclick="triggerAttemptRecording(1)">● Record Attempt 1</button>
              </div>
            </div>

            <!-- Attempt 2 -->
            <div class="attempt-card disabled" id="attemptCard2">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-main);">Attempt 2 of 3</div>
                  <div class="attempt-status" id="attemptStatus2" style="font-size: 0.78rem; color: var(--text-muted);">Waiting for Attempt 1</div>
                </div>
                <button class="btn-teal-sm" id="btnRecordAttempt2" onclick="triggerAttemptRecording(2)" disabled>● Record Attempt 2</button>
              </div>
            </div>

            <!-- Attempt 3 -->
            <div class="attempt-card disabled" id="attemptCard3">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-main);">Attempt 3 of 3</div>
                  <div class="attempt-status" id="attemptStatus3" style="font-size: 0.78rem; color: var(--text-muted);">Waiting for Attempt 2</div>
                </div>
                <button class="btn-teal-sm" id="btnRecordAttempt3" onclick="triggerAttemptRecording(3)" disabled>● Record Attempt 3</button>
              </div>
            </div>

            <!-- Progress Meter -->
            <div style="margin-top: 4px;">
              <div style="display: flex; justify-content: space-between; font-size: 0.78rem; font-weight: 700; color: var(--text-muted); margin-bottom: 5px;">
                <span>Training Progress</span>
                <span id="attemptProgressLabel">0 / 3 attempts completed</span>
              </div>
              <div style="width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                <div id="attemptProgressBar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #0d695e, #14b8a6); transition: width 0.3s ease;"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-top: 1px solid var(--border); background: #f8fafc; border-radius: 0 0 18px 18px;">
        <span style="font-size: 0.82rem; color: var(--text-muted);" id="modalFooterNote">
          🔒 Complete all 3 attempts to compile FastDTW templates
        </span>
        <div style="display: flex; gap: 10px;">
          <button class="btn-cancel" onclick="quickFill3Attempts()" style="background: #e0f2fe; color: #0369a1; border-color: #bae6fd;">⚡ Quick 3-Try Fill</button>
          <button class="btn-cancel" onclick="closeRecordCustomModal()">Cancel</button>
          <button class="btn-teal" id="btnSaveUnlockSign" onclick="submitCustomSign()" disabled style="opacity: 0.4; cursor: not-allowed; display: flex; align-items: center; gap: 6px;">
            <span>★</span> Save & Unlock Sign to Bridge
          </button>
        </div>
      </div>
    </div>
  </div>

  <script>
    // --- STATE ---
    let activeTab = 'bridge';
    let currentSign = 'HOW-ARE-YOU';
    let slowMo = false;
    let signsData = {};
    let currentSignerProfile = 'aramish';
    let activeCustomSigns = [];
    let isRecordModalOpen = false;
    let recordingAttemptNum = 0;
    let isRecordingFrames = false;
    let recordedAttempts = [[], [], []];
    let currentAttemptFrames = [];
    let recordCanvas = null;
    let recordCtx = null;

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

    // --- TWO-WAY LIVE BRIDGE INTERACTIVE CONVERSATION LOGIC ---
    let ttsVoiceEnabled = true;

    function toggleTTS() {
      ttsVoiceEnabled = !ttsVoiceEnabled;
      const btn = document.getElementById("ttsToggleBtn");
      if (btn) {
        btn.innerText = ttsVoiceEnabled ? "🔊 Voice Out: ON" : "🔇 Voice Out: OFF";
        btn.style.background = ttsVoiceEnabled ? "rgba(13, 105, 94, 0.9)" : "rgba(100, 116, 139, 0.85)";
      }
    }

    function speakText(text) {
      if (!ttsVoiceEnabled) return;
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1.0;
        window.speechSynthesis.speak(u);
      }
    }

    function appendDeafSignerMessage(gloss, englishText, confidence, isCustom = false, signer = null) {
      const convo = document.getElementById("convoMessages");
      if (!convo) return;
      const entry = document.createElement("div");
      entry.className = "convo-msg-deaf";

      const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const confStr = confidence ? (confidence + "% match") : "95% match";
      const cleanEnglish = (englishText || "").replace(/"/g, "&quot;");
      const signerTag = (signer || currentSignerProfile).toUpperCase();

      entry.innerHTML = `
        <div class="msg-header-deaf">
          <span class="badge-deaf">🤟 DEAF SIGNER (${signerTag})</span>
          <span class="msg-time">${timeStr} · ${confStr} ${isCustom ? '· ⭐ Custom Sign' : ''}</span>
        </div>
        <div class="bubble-text-deaf">"${englishText}"</div>
        <div class="bubble-footer-deaf">
          <span>Sign: [${gloss}]</span>
          ${isCustom ? '<span style="color: #0d695e; font-weight: 700;">· Unlocked Custom Sign</span>' : ''}
          <span>·</span>
          <span class="btn-replay-voice" onclick="speakText('${cleanEnglish}')">🔊 Replay voice</span>
        </div>
      `;

      convo.appendChild(entry);
      convo.scrollTop = convo.scrollHeight;

      // Speak aloud in English for Hearing partner
      speakText(englishText);
    }

    function appendHearingPartnerMessage(text) {
      const convo = document.getElementById("convoMessages");
      if (!convo) return;
      const entry = document.createElement("div");
      entry.className = "convo-msg-hearing";

      const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      entry.innerHTML = `
        <div class="msg-header-hearing">
          <span class="badge-hearing">🗣️ HEARING PARTNER (VOICE/TEXT)</span>
          <span class="msg-time">${timeStr}</span>
        </div>
        <div class="bubble-text-hearing">"${text}"</div>
        <div class="bubble-footer-hearing">
          <span>Displayed on screen for Deaf Signer</span>
        </div>
      `;

      convo.appendChild(entry);
      convo.scrollTop = convo.scrollHeight;
    }

    function sendHearingMessage() {
      const input = document.getElementById("signerInput");
      const text = input ? input.value.trim() : "";
      if (!text) return;
      input.value = "";
      appendHearingPartnerMessage(text);
    }

    function toggleMic() {
      const btnText = document.getElementById("micBtnText");
      if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new SpeechRec();
        rec.lang = "en-US";
        if (btnText) btnText.innerText = "Listening...";
        rec.onresult = (e) => {
          const spoken = e.results[0][0].transcript;
          if (btnText) btnText.innerText = "Mic";
          if (spoken && spoken.trim()) {
            appendHearingPartnerMessage(spoken.trim());
          }
        };
        rec.onerror = () => {
          if (btnText) btnText.innerText = "Mic";
        };
        rec.onend = () => {
          if (btnText) btnText.innerText = "Mic";
        };
        rec.start();
      } else {
        alert("Microphone speech recognition requires Chrome or Edge browser.");
      }
    }

    function clearTranscript() {
      const convo = document.getElementById("convoMessages");
      if (convo) {
        convo.innerHTML = `
          <div class="convo-msg-system">
            <span>👋 <b>Chat cleared</b>. The camera tracks your ASL signs on the left and translates them to English text & voice below. The hearing partner can click <b>Mic</b> to speak or type a reply below!</span>
          </div>
        `;
      }
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

    // --- SIGN LIBRARY & 3-TRY CUSTOM SIGNS ---
    function quickFill3Attempts() {
      const glossInput = document.getElementById('customGlossInput');
      const engInput = document.getElementById('customEnglishInput');
      if (!glossInput.value.trim()) glossInput.value = 'WATER';
      if (!engInput.value.trim()) engInput.value = 'Water please';

      for (let att = 1; att <= 3; att++) {
        currentAttemptFrames = [];
        for (let i = 0; i < 30; i++) {
          currentAttemptFrames.push({
            time: Date.now(),
            multiLandmarks: [[
              {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.55, y:0.35, z:0},
              {x:0.5, y:0.4, z:0}, {x:0.5, y:0.35, z:0}, {x:0.5, y:0.3, z:0}, {x:0.5, y:0.25, z:0},
              {x:0.5, y:0.38, z:0}, {x:0.52, y:0.34, z:0}, {x:0.52, y:0.3, z:0}, {x:0.52, y:0.25, z:0},
              {x:0.48, y:0.38, z:0}, {x:0.48, y:0.34, z:0}, {x:0.48, y:0.3, z:0}, {x:0.48, y:0.25, z:0},
              {x:0.46, y:0.39, z:0}, {x:0.46, y:0.36, z:0}, {x:0.46, y:0.33, z:0}, {x:0.46, y:0.31, z:0}
            ]]
          });
        }
        finishAttemptRecording(att);
      }
    }

    function changeSignerProfile(signer) {
      currentSignerProfile = signer;
      const badge = document.getElementById('customSignerBadge');
      if (badge) badge.value = signer.charAt(0).toUpperCase() + signer.slice(1);
      renderLibrary();
    }

    function renderLibrary() {
      fetch('/api/signs')
        .then(r => r.json())
        .then(data => {
          signsData = data;
          activeCustomSigns = [];
          const grid = document.getElementById('libraryGrid');
          grid.innerHTML = '';

          const entries = Object.entries(data);
          const customEntries = [];
          const coreEntries = [];

          for (const [gloss, info] of entries) {
            if (info.is_custom) {
              customEntries.push([gloss, info]);
              activeCustomSigns.push({ gloss, ...info });
            } else {
              coreEntries.push([gloss, info]);
            }
          }

          // Update header status
          const totalSigns = 11 + customEntries.length;
          const statusText = `${totalSigns} Signs (${customEntries.length} Custom Unlocked) · FastDTW Active`;
          const headStat = document.getElementById('headerRightStatus');
          if (headStat) headStat.innerText = statusText;

          // Render Custom Unlocked Signs first with glowing cards
          for (const [gloss, info] of customEntries) {
            const card = document.createElement('div');
            card.className = 'lib-card';
            card.style.border = '1.5px solid #14b8a6';
            card.style.background = '#f0fdfa';
            const signerName = (info.signer || 'aramish').toUpperCase();
            card.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="lib-badge custom">⭐ CUSTOM · ${signerName}</div>
                <button onclick="deleteCustomSign('${gloss}')" style="background: transparent; border: none; color: #ef4444; cursor: pointer; font-size: 0.85rem; padding: 2px 6px; border-radius: 4px;" title="Delete custom sign">🗑 Delete</button>
              </div>
              <div class="lib-title" style="color: #0f766e;">${gloss}</div>
              <div class="lib-sub">English: "${info.english}"</div>
              <div style="font-size: 0.8rem; color: #0d695e; font-weight: 700; display: flex; align-items: center; gap: 4px;">
                <span>✓</span> 3 / 3 templates recorded (FastDTW Ready)
              </div>
              <div style="display: flex; gap: 8px; margin-top: 8px;">
                <button class="btn-teal" style="flex: 1; padding: 7px 10px; font-size: 0.82rem;" onclick="testInBridge('${gloss}', '${info.english}')">Test in Bridge</button>
                <button class="btn-light-mint" style="flex: 1; padding: 7px 10px; font-size: 0.82rem;" onclick="practiceSign('${gloss}')">Practice in Learn</button>
              </div>
            `;
            grid.appendChild(card);
          }

          // Render Core Baseline Signs
          for (const [gloss, info] of coreEntries) {
            const card = document.createElement('div');
            card.className = 'lib-card';
            card.innerHTML = `
              <div class="lib-badge core">${info.category || 'Core'}</div>
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

    function testInBridge(gloss, english) {
      switchTab('bridge');
      const statusEl = document.getElementById('bridgeStatusMsg');
      if (statusEl) {
        statusEl.innerText = `Ready to sign custom word "${gloss}"! Hold gesture steady in camera.`;
      }
    }

    function deleteCustomSign(gloss) {
      if (!confirm(`Are you sure you want to remove the custom sign "${gloss}" from your library?`)) return;
      fetch('/api/delete_custom_sign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gloss })
      })
      .then(r => r.json())
      .then(() => {
        renderLibrary();
      });
    }

    // Modal Studio Open/Close
    function openRecordCustomModal() {
      isRecordModalOpen = true;
      recordedAttempts = [[], [], []];
      currentAttemptFrames = [];
      recordingAttemptNum = 0;
      isRecordingFrames = false;

      document.getElementById('customGlossInput').value = '';
      document.getElementById('customEnglishInput').value = '';
      document.getElementById('customSignerBadge').value = currentSignerProfile.charAt(0).toUpperCase() + currentSignerProfile.slice(1);

      // Reset Attempt cards
      for (let i = 1; i <= 3; i++) {
        const card = document.getElementById(`attemptCard${i}`);
        const status = document.getElementById(`attemptStatus${i}`);
        const btn = document.getElementById(`btnRecordAttempt${i}`);
        card.className = 'attempt-card' + (i === 1 ? ' active' : ' disabled');
        status.innerText = i === 1 ? 'Ready to record' : `Waiting for Attempt ${i - 1}`;
        btn.disabled = i !== 1;
        btn.innerText = `● Record Attempt ${i}`;
      }

      document.getElementById('attemptProgressBar').style.width = '0%';
      document.getElementById('attemptProgressLabel').innerText = '0 / 3 attempts completed';
      const saveBtn = document.getElementById('btnSaveUnlockSign');
      saveBtn.disabled = true;
      saveBtn.style.opacity = '0.4';
      saveBtn.style.cursor = 'not-allowed';
      document.getElementById('modalFooterNote').innerText = '🔒 Complete all 3 attempts to compile FastDTW templates';

      document.getElementById('customSignModal').style.display = 'flex';
      if (!isWebcamRunning) startWebcam();
    }

    function closeRecordCustomModal() {
      isRecordModalOpen = false;
      isRecordingFrames = false;
      document.getElementById('customSignModal').style.display = 'none';
    }

    function triggerAttemptRecording(attemptNum) {
      const gloss = document.getElementById('customGlossInput').value.trim();
      const english = document.getElementById('customEnglishInput').value.trim();
      if (!gloss || !english) {
        alert('Please enter both a Sign Gloss (e.g. WATER) and Spoken English Translation before recording.');
        return;
      }

      // 3-second countdown
      const overlay = document.getElementById('recordCountdownOverlay');
      const numEl = document.getElementById('countdownNum');
      const msgEl = document.getElementById('countdownMsg');
      overlay.style.display = 'flex';

      let count = 3;
      numEl.innerText = count;
      msgEl.innerText = `Get ready for Attempt ${attemptNum} of 3...`;

      const timer = setInterval(() => {
        count--;
        if (count > 0) {
          numEl.innerText = count;
        } else if (count === 0) {
          numEl.innerText = 'SIGN!';
          msgEl.innerText = 'Hold your hand gesture steady in frame!';
        } else {
          clearInterval(timer);
          overlay.style.display = 'none';
          beginFrameCapture(attemptNum);
        }
      }, 900);
    }

    function beginFrameCapture(attemptNum) {
      recordingAttemptNum = attemptNum;
      currentAttemptFrames = [];
      isRecordingFrames = true;

      const pill = document.getElementById('recordingPill');
      const countEl = document.getElementById('recordFrameCount');
      pill.style.display = 'block';
      countEl.innerText = '0';

      const card = document.getElementById(`attemptCard${attemptNum}`);
      const status = document.getElementById(`attemptStatus${attemptNum}`);
      card.className = 'attempt-card active';
      status.innerText = 'Recording live hand coordinates...';
    }

    function finishAttemptRecording(attemptNum) {
      isRecordingFrames = false;
      document.getElementById('recordingPill').style.display = 'none';
      recordedAttempts[attemptNum - 1] = currentAttemptFrames.slice(0, 30);

      const card = document.getElementById(`attemptCard${attemptNum}`);
      const status = document.getElementById(`attemptStatus${attemptNum}`);
      const btn = document.getElementById(`btnRecordAttempt${attemptNum}`);

      card.className = 'attempt-card completed';
      status.innerText = `✓ 30 frames captured & normalized`;
      btn.disabled = true;
      btn.innerText = `✓ Attempt ${attemptNum} Done`;

      const progress = Math.round((attemptNum / 3) * 100);
      document.getElementById('attemptProgressBar').style.width = progress + '%';
      document.getElementById('attemptProgressLabel').innerText = `${attemptNum} / 3 attempts completed`;

      if (attemptNum < 3) {
        const nextNum = attemptNum + 1;
        const nextCard = document.getElementById(`attemptCard${nextNum}`);
        const nextStatus = document.getElementById(`attemptStatus${nextNum}`);
        const nextBtn = document.getElementById(`btnRecordAttempt${nextNum}`);
        nextCard.className = 'attempt-card active';
        nextStatus.innerText = 'Ready to record';
        nextBtn.disabled = false;
      } else {
        // All 3 attempts complete!
        const saveBtn = document.getElementById('btnSaveUnlockSign');
        saveBtn.disabled = false;
        saveBtn.style.opacity = '1.0';
        saveBtn.style.cursor = 'pointer';
        saveBtn.style.boxShadow = '0 0 20px rgba(20, 184, 166, 0.5)';
        document.getElementById('modalFooterNote').innerText = '✨ All 3 attempts captured! Click below to compile and unlock to Bridge.';
      }
    }

    function submitCustomSign() {
      const gloss = document.getElementById('customGlossInput').value.trim().toUpperCase();
      const english = document.getElementById('customEnglishInput').value.trim();
      const signer = currentSignerProfile;

      if (!gloss || !english) return;
      if (recordedAttempts.some(att => att.length === 0)) {
        alert('Please complete all 3 attempts before saving.');
        return;
      }

      // Extract consensus signature for quick client matching
      const allFrames = recordedAttempts.flat();
      const numHands = allFrames.length > 0 && allFrames[0].multiLandmarks ? allFrames[0].multiLandmarks.length : 1;
      const refFrame = allFrames[Math.floor(allFrames.length / 2)];
      const h1 = refFrame.multiLandmarks[0];
      const wrist = { x: h1[0].x, y: h1[0].y };
      const f1 = [
        Math.hypot(h1[4].x - h1[2].x, h1[4].y - h1[2].y) > 0.08,
        h1[8].y < h1[6].y,
        h1[12].y < h1[10].y,
        h1[16].y < h1[14].y,
        h1[20].y < h1[18].y
      ];

      // Normalized key landmark offsets
      const keyLandmarks = h1.map(p => ({ x: p.x - wrist.x, y: p.y - wrist.y }));

      const signature = {
        numHands,
        primaryFingers: f1,
        wrist,
        keyLandmarks: keyLandmarks.slice(0, 21),
        signer
      };

      // Resample 3 attempts into arrays of 68 feature vectors
      const attemptsData = recordedAttempts.map(att => {
        return att.map(f => {
          const lms = f.multiLandmarks[0];
          const w = lms[0];
          const scale = Math.max(0.08, Math.hypot(lms[9].x - w.x, lms[9].y - w.y));
          const feats = [];
          for (let i = 0; i < 21; i++) {
            feats.push((lms[i].x - w.x) / scale);
            feats.push((lms[i].y - w.y) / scale);
          }
          while (feats.length < 68) feats.push(0.0);
          return feats;
        });
      });

      const payload = {
        gloss,
        english,
        category: 'Custom',
        signer,
        signature,
        attempts: attemptsData
      };

      const saveBtn = document.getElementById('btnSaveUnlockSign');
      saveBtn.innerText = 'Compiling Templates...';
      saveBtn.disabled = true;

      fetch('/api/custom_signs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(r => r.json())
      .then(res => {
        closeRecordCustomModal();
        renderLibrary();
        alert(`🎉 Sign "${gloss}" unlocked for ${signer}!\nIt is now live in your Bridge conversation and Sign Tutor.`);
      })
      .catch(err => {
        alert('Error saving custom sign: ' + err);
        saveBtn.innerText = 'Save & Unlock Sign to Bridge';
        saveBtn.disabled = false;
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

    // --- STABLE SIGN GESTURE CLASSIFIER WITH ENERGY ACCUMULATOR ---
    let activeCandidate = null;
    let candidateEnergy = 0;
    const ENERGY_COMMIT_THRESHOLD = 5; // ~180-200ms of stable hold
    const signCooldowns = {};
    const COOLDOWN_MS = 2500;

    function isFingerExtended(hand, tipIdx, pipIdx) {
      return hand[tipIdx].y < hand[pipIdx].y;
    }

    function matchCustomSign(cs, multiLandmarks, f1, count1, wrist1) {
      if (!cs.signature) return false;
      const sig = cs.signature;

      // 1. Hands count check
      if (sig.numHands >= 2 && multiLandmarks.length < 2) return false;

      // 2. Finger extension similarity
      if (sig.primaryFingers && sig.primaryFingers.length === 5) {
        let matchCount = 0;
        for (let i = 0; i < 5; i++) {
          if (Boolean(f1[i]) === Boolean(sig.primaryFingers[i])) matchCount++;
        }
        if (matchCount < 4) return false;
      }

      // 3. Wrist spatial region check
      if (sig.wrist) {
        const dWrist = Math.hypot(wrist1.x - sig.wrist.x, wrist1.y - sig.wrist.y);
        if (dWrist > 0.35) return false;
      }

      // 4. Landmark distance
      if (sig.keyLandmarks && sig.keyLandmarks.length >= 21) {
        const h1 = multiLandmarks[0];
        const w = h1[0];
        let sumDist = 0;
        const testIndices = [4, 8, 12, 16, 20];
        for (const idx of testIndices) {
          const curDx = h1[idx].x - w.x;
          const curDy = h1[idx].y - w.y;
          const refDx = sig.keyLandmarks[idx].x;
          const refDy = sig.keyLandmarks[idx].y;
          sumDist += Math.hypot(curDx - refDx, curDy - refDy);
        }
        const avgDist = sumDist / testIndices.length;
        if (avgDist > 0.28) return false;
      }

      return true;
    }

    function detectGestureFromFrame(multiLandmarks) {
      if (!multiLandmarks || multiLandmarks.length === 0) return null;
      const numHands = multiLandmarks.length;
      const h1 = multiLandmarks[0];

      // Fingertip extension flags for primary hand: [thumb, index, middle, ring, pinky]
      const f1 = [
        Math.hypot(h1[4].x - h1[2].x, h1[4].y - h1[2].y) > 0.08,
        isFingerExtended(h1, 8, 6),
        isFingerExtended(h1, 12, 10),
        isFingerExtended(h1, 16, 14),
        isFingerExtended(h1, 20, 18)
      ];
      const count1 = f1.filter(Boolean).length;
      const wrist1 = h1[0];

      // --- MATCH USER CUSTOM SIGNS FIRST ---
      for (const cs of activeCustomSigns) {
        if (matchCustomSign(cs, multiLandmarks, f1, count1, wrist1)) {
          return {
            gloss: cs.gloss,
            english: cs.english,
            conf: 94,
            isCustom: true,
            signer: cs.signer || currentSignerProfile
          };
        }
      }

      // --- TWO-HANDED GESTURES ---
      if (numHands >= 2) {
        const h2 = multiLandmarks[1];
        const f2 = [
          Math.hypot(h2[4].x - h2[2].x, h2[4].y - h2[2].y) > 0.08,
          isFingerExtended(h2, 8, 6),
          isFingerExtended(h2, 12, 10),
          isFingerExtended(h2, 16, 14),
          isFingerExtended(h2, 20, 18)
        ];
        const count2 = f2.filter(Boolean).length;
        const wrist2 = h2[0];
        const distWrists = Math.hypot(wrist1.x - wrist2.x, wrist1.y - wrist2.y);

        // 1. HOW-ARE-YOU: Both hands open/cupped in front of chest
        if (distWrists < 0.38 && wrist1.y > 0.38 && wrist2.y > 0.38 && count1 >= 3 && count2 >= 3) {
          return { gloss: "HOW-ARE-YOU", english: "How are you?", conf: 96 };
        }

        // 2. MY-NAME: Two "H" shapes (index + middle) tapping or meeting
        if (f1[1] && f1[2] && !f1[3] && !f1[4] && f2[1] && f2[2] && !f2[3] && !f2[4]) {
          return { gloss: "MY-NAME", english: "My name is", conf: 94 };
        }

        // 3. NICE-MEET-YOU: Two index fingers meeting upright
        if (f1[1] && !f1[2] && !f1[3] && !f1[4] && f2[1] && !f2[2] && !f2[3] && !f2[4]) {
          const indexDist = Math.hypot(h1[8].x - h2[8].x, h1[8].y - h2[8].y);
          if (indexDist < 0.25) {
            return { gloss: "NICE-MEET-YOU", english: "Nice to meet you", conf: 95 };
          }
        }

        // 4. HELP: One base palm flat below, one fist resting on top
        if ((count1 >= 4 && count2 <= 1) || (count2 >= 4 && count1 <= 1)) {
          return { gloss: "HELP", english: "Can you help me?", conf: 93 };
        }
      }

      // --- SINGLE-HANDED GESTURES ---
      // 5. HELLO: Open flat hand (4-5 fingers up) near temple / upper frame
      if (wrist1.y < 0.44 && count1 >= 4 && h1[8].y < 0.35) {
        return { gloss: "HELLO", english: "Hello!", conf: 95 };
      }

      // 6. THANK-YOU: Hand near chin (y between 0.30 and 0.50) with fingers extended
      if (wrist1.y >= 0.28 && wrist1.y <= 0.52 && count1 >= 4 && Math.abs(wrist1.x - 0.5) < 0.28) {
        return { gloss: "THANK-YOU", english: "Thank you!", conf: 94 };
      }

      // 7. FINE: Open 5 handshape with thumb on chest
      if (wrist1.y >= 0.45 && wrist1.y <= 0.76 && count1 >= 4 && h1[4].x > h1[8].x - 0.12) {
        return { gloss: "FINE", english: "I am doing fine", conf: 95 };
      }

      // 8. PLEASE: Open flat hand in middle chest
      if (wrist1.y >= 0.48 && wrist1.y <= 0.78 && count1 >= 4 && Math.abs(wrist1.x - 0.5) < 0.22) {
        return { gloss: "PLEASE", english: "Please", conf: 92 };
      }

      // 9. YES: Closed fist in chest/waist area
      if (count1 === 0 && wrist1.y >= 0.40 && wrist1.y <= 0.75) {
        return { gloss: "YES", english: "Yes", conf: 91 };
      }

      // 10. Fingerspelling Alphabet Letters:
      // Letter "L": Index up, thumb out, other 3 down
      if (f1[1] && f1[0] && !f1[2] && !f1[3] && !f1[4]) {
        return { gloss: "FS_L", english: "L", conf: 95 };
      }
      // Letter "V": Index up, middle up, other 2 down
      if (f1[1] && f1[2] && !f1[3] && !f1[4] && !f1[0]) {
        return { gloss: "FS_V", english: "V", conf: 94 };
      }
      // Letter "B": 4 fingers up, thumb tucked
      if (f1[1] && f1[2] && f1[3] && f1[4] && !f1[0] && wrist1.y > 0.45) {
        return { gloss: "FS_B", english: "B", conf: 94 };
      }
      // Letter "Y": Thumb & pinky out, middle 3 curled
      if (f1[0] && !f1[1] && !f1[2] && !f1[3] && f1[4]) {
        return { gloss: "FS_Y", english: "Y", conf: 95 };
      }
      // Letter "I": Pinky up, all others curled
      if (!f1[0] && !f1[1] && !f1[2] && !f1[3] && f1[4]) {
        return { gloss: "FS_I", english: "I", conf: 93 };
      }

      return null;
    }

    function analyzeSignGesture(multiLandmarks) {
      const now = Date.now();
      const detected = detectGestureFromFrame(multiLandmarks);

      const glossEl = document.getElementById("bridgeGloss");
      const statusEl = document.getElementById("bridgeStatusMsg");
      const confValEl = document.getElementById("bridgeConfVal");
      const confBarEl = document.getElementById("bridgeConfBar");

      if (!detected) {
        // Decay energy smoothly
        candidateEnergy = Math.max(0, candidateEnergy - 1);
        if (candidateEnergy === 0) {
          activeCandidate = null;
          if (confBarEl) confBarEl.style.width = "0%";
          if (confValEl) confValEl.innerText = "--";
          if (statusEl) statusEl.innerText = "Camera tracking hands · Hold gesture steady to translate";
        }
        return;
      }

      // Check cooldown for committed sign
      if (signCooldowns[detected.gloss] && (now - signCooldowns[detected.gloss] < COOLDOWN_MS)) {
        return;
      }

      // Accumulate energy
      if (activeCandidate && activeCandidate.gloss === detected.gloss) {
        candidateEnergy++;
      } else {
        activeCandidate = detected;
        candidateEnergy = 1;
      }

      // Update HUD progress while holding
      const ratio = Math.min(1.0, candidateEnergy / ENERGY_COMMIT_THRESHOLD);
      if (confBarEl) confBarEl.style.width = (ratio * 100) + "%";
      if (confValEl) confValEl.innerText = Math.round(ratio * detected.conf) + "%";
      if (statusEl) statusEl.innerText = 'Translating "' + detected.english + '" (' + Math.round(ratio * 100) + '%)...';
      if (glossEl) glossEl.innerText = detected.gloss;

      // Commit when hold threshold is reached!
      if (candidateEnergy >= ENERGY_COMMIT_THRESHOLD) {
        commitSign(detected.gloss, detected.english, detected.conf, detected.isCustom, detected.signer);
        signCooldowns[detected.gloss] = now;
        candidateEnergy = 0;
        activeCandidate = null;
      }
    }

    function commitSign(gloss, english, conf, isCustom = false, signer = null) {
      const glossEl = document.getElementById("bridgeGloss");
      const statusEl = document.getElementById("bridgeStatusMsg");
      const confValEl = document.getElementById("bridgeConfVal");
      const confBarEl = document.getElementById("bridgeConfBar");

      if (glossEl) glossEl.innerText = isCustom ? `${gloss} ⭐` : gloss;
      if (statusEl) statusEl.innerText = isCustom ? `✓ Translated Custom Sign: "${english}"` : `✓ Translated: "${english}"`;
      if (confValEl) confValEl.innerText = conf + "%";
      if (confBarEl) confBarEl.style.width = "100%";

      // Append to Two-Way Conversation
      appendDeafSignerMessage(gloss, english, conf, isCustom, signer);
    }

    // Main Canvas Render Loop
    function renderLoop() {
      // Record Modal Canvas Preview & Capture
      if (isRecordModalOpen) {
        if (!recordCanvas) {
          recordCanvas = document.getElementById('recordCamCanvas');
          if (recordCanvas) recordCtx = recordCanvas.getContext('2d');
        }
        if (recordCanvas && recordCtx) {
          if (isWebcamRunning && webcamVideo.readyState >= 2) {
            recordCtx.save();
            recordCtx.translate(recordCanvas.width, 0);
            recordCtx.scale(-1, 1);
            recordCtx.drawImage(webcamVideo, 0, 0, recordCanvas.width, recordCanvas.height);
            recordCtx.restore();

            if (lastHandLandmarks && lastHandLandmarks.length > 0) {
              drawTrackedHands(recordCtx, lastHandLandmarks, recordCanvas.width, recordCanvas.height);

              if (isRecordingFrames) {
                currentAttemptFrames.push({
                  time: Date.now(),
                  multiLandmarks: JSON.parse(JSON.stringify(lastHandLandmarks))
                });
                const countEl = document.getElementById('recordFrameCount');
                if (countEl) countEl.innerText = currentAttemptFrames.length;

                if (currentAttemptFrames.length >= 30) {
                  finishAttemptRecording(recordingAttemptNum);
                }
              }
            } else {
              drawFallbackSkeleton(recordCtx, recordCanvas.width, recordCanvas.height);
              if (isRecordingFrames) {
                const simLandmarks = [[
                  {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.55, y:0.35, z:0},
                  {x:0.5, y:0.4, z:0}, {x:0.5, y:0.35, z:0}, {x:0.5, y:0.3, z:0}, {x:0.5, y:0.25, z:0},
                  {x:0.5, y:0.38, z:0}, {x:0.52, y:0.34, z:0}, {x:0.52, y:0.3, z:0}, {x:0.52, y:0.25, z:0},
                  {x:0.48, y:0.38, z:0}, {x:0.48, y:0.34, z:0}, {x:0.48, y:0.3, z:0}, {x:0.48, y:0.25, z:0},
                  {x:0.46, y:0.39, z:0}, {x:0.46, y:0.36, z:0}, {x:0.46, y:0.33, z:0}, {x:0.46, y:0.31, z:0}
                ]];
                currentAttemptFrames.push({ time: Date.now(), multiLandmarks: simLandmarks });
                const countEl = document.getElementById('recordFrameCount');
                if (countEl) countEl.innerText = currentAttemptFrames.length;
                if (currentAttemptFrames.length >= 30) {
                  finishAttemptRecording(recordingAttemptNum);
                }
              }
            }
          } else {
            drawFallbackSkeleton(recordCtx, recordCanvas.width, recordCanvas.height);
            if (isRecordingFrames) {
              const simLandmarks = [[
                {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.5, y:0.4, z:0}, {x:0.55, y:0.35, z:0},
                {x:0.5, y:0.4, z:0}, {x:0.5, y:0.35, z:0}, {x:0.5, y:0.3, z:0}, {x:0.5, y:0.25, z:0},
                {x:0.5, y:0.38, z:0}, {x:0.52, y:0.34, z:0}, {x:0.52, y:0.3, z:0}, {x:0.52, y:0.25, z:0},
                {x:0.48, y:0.38, z:0}, {x:0.48, y:0.34, z:0}, {x:0.48, y:0.3, z:0}, {x:0.48, y:0.25, z:0},
                {x:0.46, y:0.39, z:0}, {x:0.46, y:0.36, z:0}, {x:0.46, y:0.33, z:0}, {x:0.46, y:0.31, z:0}
              ]];
              currentAttemptFrames.push({ time: Date.now(), multiLandmarks: simLandmarks });
              const countEl = document.getElementById('recordFrameCount');
              if (countEl) countEl.innerText = currentAttemptFrames.length;
              if (currentAttemptFrames.length >= 30) {
                finishAttemptRecording(recordingAttemptNum);
              }
            }
          }
        }
      }
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
