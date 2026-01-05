# Motion Weave 🕸️

**Automated Neural Human Animation Engine**

![Motion Weave Banner](https://via.placeholder.com/1200x400.png?text=Motion+Weave+Architecture)
*(Replace with actual banner if available)*

## 🚀 Overview
Motion Weave is a plug-and-play **Character Replacement Engine**. It allows you to take a static image of a character and animate it using the motion from a reference video. Think of it as a "Digital Puppeteer": the reference video provides the strings, and the AI diffusion model pulls them to make your static character dance, walk, or act.

This project packages state-of-the-art research (MimicMotion, SVD, DWPose) into a production-ready **Dockerized container**, making high-end animation accessible via a single command.

---

## 💡 Inspiration & Novelty

### Standing on the Shoulders of Giants
This project is deeply inspired by:
- **MimicMotion (Tencent)**: For the core confidence-aware pose guidance.
- **Animate Anyone (Alibaba)**: For the foundational idea of ReferenceNet.
- **Stable Video Diffusion (Stability AI)**: The backbone of our generative "dreaming".

### The USP (Unique Selling Point)
While the research repos are complex "spaghetti code" meant for papers, **Motion Weave is Engineering**.
1.  **Microservice Architecture**: Decoupled AI Brain (Python/Video) from the Control Studio (Next.js/React).
2.  **Phase 3 Optimizations**: We implemented custom logic for **Latent Stitching** (to create long-form videos >5s) and **Face Enhancement** (integrating GFPGAN to fix the "blurry face" problem common in diffusion).
3.  **Wan 2.1 Ready**: The engine is architected to support multi-model backends, including the upcoming Wan 2.1.
4.  **Plug-and-Play**: A single `deploy.sh` script sets up the entire stack (Drivers, CUDA, API, UI).

---

## ⚙️ How It Works (The Technical Deep Dive)

### The Analogy: "The Ghost Painter"
Imagine a painter (The AI) who is looking at a blurred canvas (Noise).
1.  **The Reference**: You show them a photo of "Alice". They memorize her face (**ReferenceNet**).
2.  **The Skeleton**: You show them a stick-figure video of a dance (**ControlNet**).
3.  **The Process**: The painter starts clearing the fog. As they paint, they are forced to put "Alice's" colors only where the "Stick Figure" lines are.
4.  **The Result**: Alice is now dancing exactly like the stick figure.

### System Architecture
```mermaid
graph TD
    User[User Input] -->|Ref Image + Driver Video| API[FastAPI Backend]
    API -->|Async Job| Queue[Job Manager]
    Queue -->|Process| Engine[AI Engine (GPU)]
    
    subgraph "AI Engine Pipeline"
        direction TB
        Video[Driver Video] -->|OpenCV| DWPose[DWPose Estimator]
        DWPose -->|Skeleton Tensor| SVD[MimicMotion / SVD]
        Ref[Char Image] -->|CLIP Encode| SVD
        
        SVD -->|Latents| VAE[VAE Decoder]
        VAE -->|Raw Frames| Stitch[Smart Stitcher]
        Stitch -->|Refine| GFPGAN[Face Enhancer]
    end
    
    GFPGAN -->|MP4| Storage[Output Folder]
```

### Technical Stack
*   **AI Core**: PyTorch 2.1, Diffusers (HuggingFace), MimicMotion checkponts.
*   **Pose Estimation**: DWPose (ONNX Runtime).
*   **Post-Processing**: GFPGAN (Face Restoration), FFmpeg (Video Encoding).
*   **Infrastructure**: Docker, Nvidia Container Runtime, FastAPI, Next.js.

---

## 🎯 For Whom?
*   **Indie Animators**: Create full character animations without 3D rigging.
*   **Game Devs**: Generate rapid prototyping cutscenes.
*   **Meme Creators**: Put any character into trending viral videos.

---

## ⚠️ Disclaimer & Methodology

**"Plug, Play, & Pray"**
This project is designed to be **Production Ready Scaffolding**.
- ✅ **Wiring**: The logic for Pose Extraction -> Diffusion -> Stitching is fully implemented.
- ✅ **Docker**: The containerization is complete.
- 🚧 **Testing**: I have not "stress tested" this on a cluster of H100s. It operates in what we call **"Engineering Verification"** stage. It is ready for you to deploy and debug, but expect quirks with VRAM usage on longer videos.

**Current Stage:** `Beta 1.0`
- **Ready**: Short clips (2-5s), basic docker deployment, UI uploads.
- **Self-Assessment**: The system includes a `health_check.py` that will tell you if your GPU is good enough.

---

## 📊 Status & Roadmap

| Feature | Status | Notes |
| :--- | :--- | :--- |
| **AI Backbone** | 🟢 Ready | MimicMotion wired up. |
| **Pose Extraction** | 🟢 Ready | DWPose via OpenCV loop. |
| **Docker Stack** | 🟢 Ready | `deploy.sh` works. |
| **Face Enhancer** | 🟡 Beta | GFPGAN implemented but needs weight tuning. |
| **Long Video** | 🟡 Beta | Stitching logic exists (`smooth_stitch`), needs tuning for drift. |
| **Audio Sync** | 🔴 Pending | Not yet implemented (planned for V2). |

---

## 🛠️ How to Run

1.  **Clone**:
    ```bash
    git clone https://github.com/Santhoshnadella/motionweave.git
    cd motionweave
    ```
2.  **Deploy (Linux/Cloud)**:
    ```bash
    chmod +x deploy.sh
    ./deploy.sh
    ```
3.  **Deploy (Windows)**:
    Double click `deploy.bat`.

4.  **Open Studio**:
    Go to `http://localhost:3000`.

---

**Built with 🤖 and ❤️.**
