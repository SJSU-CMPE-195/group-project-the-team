# Project Title: Silent Voice Bridge: The Edge AI ASL Interpreter

> Project Description - The Silent Voice Bridge is a portable, real-time bidirectional communication system designed to translate American Sign Language (ASL) gestures into English text and spoken English into text. By utilizing an NVIDIA Jetson edge computing device, the system processes all data locally to ensure absolute user privacy and low-latency performance without requiring internet connectivity.

## Team

| Name | GitHub | Email |
|------|--------|-------|
| Reuben George | [@username](https://github.com/username) | reuben.george@sjsu.edu |
| Pwint Thu Thu San | [@username](https://github.com/PwintThuThuSan) | pwintthuthu.san@sjsu.edu |
| Aramish Farooq | [@username](https://github.com/username) | aramish.farooq@sjsu.edu |
| Nathaniel Ortega | [@username](https://github.com/username) | nathaniel.ortega@sjsu.edu |

**Advisor:** [Kaikai Liu]

---

## Problem Statement

[2-3 sentences describing the problem you're solving and why it matters]
Communication barriers between the hearing world and the 466 million people with disabling hearing loss often limit social, medical, and economic opportunities. DHH individuals currently depend on scarce human interpreters or cloud-based apps that compromise privacy and require constant internet connectivity. Solving this problem through real-time, offline translation is essential for fostering independence and inclusive communication.

## Solution

[2-3 sentences describing your solution approach]
The Silent Voice Bridge is a portable, edge-AI system that uses a webcam and an NVIDIA Jetson device to translate American Sign Language (ASL) into English text locally. Our approach utilizes a hardware/software co-design that extracts lightweight skeletal landmarks to ensure high-speed performance without uploading sensitive video data to external servers. This creates a secure, low-latency environment for bidirectional communication between DHH and hearing users.

### Key Features

- Real-Time Alphabet Recognition: Successfully classifies the static ASL alphabet using a Random Forest Classifier trained on the Kaggle ASL dataset.
- Efficient Landmark Extraction: Uses MediaPipe to "distill" raw image data into 21 hand landmarks, reducing 15 GB of raw imagery into a 50 MB coordinate-based CSV.
- Low-Latency Edge Inference: Achieves 30+ FPS with under 300ms of latency, meeting the performance targets required for natural, real-time use.
- Temporal Smoothing Buffer: Employs "Majority Vote" logic across consecutive frames to eliminate prediction flickering and provide a stable user interface.
- Privacy-Preserving Offline Logic: Performs all gesture classification locally on the device, ensuring no video data is sent to the cloud.
---

## Proof of Concept Scope
The initial Proof of Concept (PoC) serves as the Classification Foundation for the project.

## What it demonstrates:
- Real-time recognition of the static ASL alphabet (A-Z).
- Efficient landmark extraction that reduces 15 GB of raw imagery into a 50 MB coordinate-based dataset.
- A stable vision pipeline achieving 30+ FPS with under 300ms of latency.
- Temporal smoothing logic that eliminates "flickering" between similar signs.

## What is NOT included yet:
- Recognition of dynamic, word-level signs or complex phrases.
- Two-handed sign tracking.
- The bidirectional speech-to-text component.

## Demo

[Link to demo video or GIF]

**Live Demo:** [URL if deployed]

---

## Screenshots

| Feature | Screenshot |
|---------|------------|
| [Feature 1] | ![Screenshot](docs/screenshots/feature1.png) |
| [Feature 2] | ![Screenshot](docs/screenshots/feature2.png) |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Frontend | |
| Backend | |
| Database | |
| Deployment | |

---

## Getting Started

### Prerequisites

To maintain stability and mirror the target JetPack environment, the following versions are required:
- Python
- MediaPipe
- OpenCV
- Scikit-learn

### Installation

```bash
# Clone the repository
git clone https://github.com/SJSU-CMPE-195/group-project-the-team.git
cd [repo]

# Install dependencies
pip install opencv-python mediapipe==0.10.14 scikit-learn pandas numpy

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run database migrations (if applicable)
[migration command]
```

### Technical Stack
- Hardware: NVIDIA Jetson Nano/Orin (Target).
- Vision Engine: OpenCV (using CLAHE for lighting normalization).
- Feature Extraction: MediaPipe (extracting 21 skeletal landmarks per hand).
- Machine Learning: Scikit-learn (Random Forest Classifier).
- Frontend Interface: React (for the final dynamic web interface).

### What's Next (195B)
- Dynamic Sign Recognition: Implementing LSTM (Long Short-Term Memory) neural networks to analyze motion over 30-frame windows.
- Vocabulary Expansion: Moving from alphabet recognition to a full vocabulary of 2,000+ signs using the WLASL dataset.
- Hardware Optimization: Applying NVIDIA TensorRT to accelerate inference speeds on the Jetson edge device.
- Bidirectional Communication: Integrating a speech-to-text API for hearing-to-DHH user communication.

### Running Locally

```bash
# Development mode
[dev command]

# The app will be available at http://localhost:XXXX
```

### Running Tests

```bash
[test command]
```

---

## API Reference

<details>
<summary>Click to expand API endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/resource` | Get all resources |
| GET | `/api/resource/:id` | Get resource by ID |
| POST | `/api/resource` | Create new resource |
| PUT | `/api/resource/:id` | Update resource |
| DELETE | `/api/resource/:id` | Delete resource |

</details>

---

## Project Structure

```
.
├── [folder]/           # Description
├── src/                # Source code files
├── tests/              # Test files
├── docs/               # Documentation files
└── README.md
```

---

## Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### Commit Messages

Use clear, descriptive commit messages:
- `Add user authentication endpoint`
- `Fix database connection timeout issue`
- `Update README with setup instructions`

---

## Acknowledgments

- [Resource/Library/Person]
- [Resource/Library/Person]

---

## License

This project is licensed under the <FILL IN> License - see the [LICENSE](LICENSE) file for details.

---

*CMPE 195A/B - Senior Design Project | San Jose State University | Spring 2026*
