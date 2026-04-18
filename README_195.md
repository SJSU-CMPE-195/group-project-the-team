# 🤟 Silent Voice Bridge: The Edge AI ASL Interpreter

> **Phase 1: Proof of Concept (PoC) Milestone** > A portable, real-time bidirectional communication system that translates American Sign Language (ASL) into English text locally on edge hardware.

---

## 👥 The Team

| Name | GitHub | Email |
| :--- | :--- | :--- |
| **Reuben George** | [@reubengeorge](https://github.com/reubengeorge) | reuben.george@sjsu.edu |
| **Pwint Thu Thu San** | [@PwintThuThuSan](https://github.com/PwintThuThuSan) | pwintthuthu.san@sjsu.edu |
| **Aramish Farooq** | [@aramishf](https://github.com/aramishf) | aramish.farooq@sjsu.edu |
| **Nathaniel Ortega** | [@nathanielortega](https://github.com/nathanielortega) | nathaniel.ortega@sjsu.edu |

**Advisor:** Dr. Kaikai Liu  
**Course:** CMPE 195A - Senior Design Project I | **San Jose State University**

---

## 📌 Problem Statement
Communication barriers between the hearing world and 466 million people with disabling hearing loss limit social and economic opportunities. Existing solutions often require constant internet connectivity and compromise privacy via cloud processing. **Silent Voice Bridge** provides a secure, low-latency, and entirely offline environment for bidirectional communication.

## 💡 The Solution
Our system utilizes a **hardware/software co-design** that extracts lightweight skeletal landmarks to ensure high-speed performance on edge devices. By processing data locally on an **NVIDIA Jetson**, we guarantee user privacy while maintaining the 30+ FPS required for natural conversation.

---

## 🚀 Key Features
* **Real-Time Alphabet Recognition:** High-accuracy classification of the static ASL alphabet (A-Z).
* **Efficient Feature Engineering:** Uses **MediaPipe** to "distill" 15GB of raw imagery into a 50MB coordinate-based CSV.
* **Low-Latency Performance:** Achieves **30+ FPS** with **<300ms latency**.
* **Temporal Smoothing:** Custom "Majority Vote" logic eliminates prediction flickering for a stable UI.
* **Lighting Robustness:** Integrated **CLAHE** (Contrast Limited Adaptive Histogram Equalization) for varying environments.

---

## 🛠 Tech Stack

| Category | Technology |
| :--- | :--- |
| **Hardware** | NVIDIA Jetson Orin Nano (Target), MacBook Air M4 (Dev) |
| **Vision Engine** | OpenCV (CLAHE Normalization) |
| **Landmark Logic** | MediaPipe (21 Skeletal Hand Landmarks) |
| **Inference Model** | Scikit-learn (Random Forest Classifier) |
| **Language** | Python 3.12 |

---

## 📂 Project Structure
```text
.
├── data/               # Processed CSV landmark datasets
├── models/             # Trained .pkl models & label encoders
├── src/
│   ├── create_dataset.py   # Image-to-Landmark distillation
│   ├── train_model.py      # Random Forest training pipeline
│   └── live_inference.py   # THE POC: Real-time webcam interpreter
├── docs/               # Screenshots, GIFs, and architecture diagrams
└── README.md


Prerequisites
Python 3.12 (Important: Stability target for JetPack)

Standard Webcam

Virtual Environment (Recommended)

Installation
# Clone the repository
git clone [https://github.com/SJSU-CMPE-195/group-project-the-team.git](https://github.com/SJSU-CMPE-195/group-project-the-team.git)
cd group-project-the-team

# Set up virtual environment
python3 -m venv bridge_env
source bridge_env/bin/activate

# Install dependencies
pip install opencv-python mediapipe==0.10.14 scikit-learn pandas numpy tqdm

Running the PoC
To launch the real-time inference engine:

Bash
python src/live_inference.py
⏭️ What's Next (CMPE 195B)
Dynamic Sign Recognition: Implementing LSTM (Long Short-Term Memory) networks for 30-frame motion analysis.

Vocabulary Expansion: Transitioning to the WLASL dataset for 2,000+ word-level signs.

Hardware Optimization: Utilizing NVIDIA TensorRT for GPU-accelerated inference.

Bidirectional Flow: Integrating Speech-to-Text APIs for a complete conversation loop.
