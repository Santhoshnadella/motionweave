# Motion Weave - Educational Guide & User Manual

## Welcome to Character Replacement
Motion Weave is a "Neural Human Animation" engine. Unlike traditional CGI which uses 3D rigs, Motion Weave uses **Diffusion** to "dream" a character into a new motion.

---

## 📚 Core Concepts (The "Why")

### 1. Diffusion Models
Think of Video Diffusion as a "Restoration Machine".
- We teach an AI to fix static/noisy images.
- To generate a video, we give it pure static (noise) and say "Fix this into a video of a person dancing."
- It hallucniates the person dancing out of the noise.

### 2. ControlNet ( The Skeleton)
If we just asked for "a person dancing," the AI would generate a random person.
**ControlNet** is the leash.
- We show the AI a "Skeleton Video" (stick figures) alongside the noise.
- We force the AI: "You can dream whatever you want, BUT it must align with these stick figures."
- This is how we transfer motion from *Video A* to *Character B*.

### 3. Latent Space
We don't process 1080p pixels directly (it would require 500GB VRAM).
- We compress the video into a "Latent Space" (a mathematical soup, 8x smaller).
- The AI does all the work in this soup.
- At the end, a "VAE Decoder" turns the soup back into pixels.

---

## 🎓 Learning Resources (Zero to Hero)

### Beginner
1. **[Video] How AI Image Generators Work** (Computerphile) - *Must Watch*
2. **[Video] Neural Networks Simply Explained** (3Blue1Brown)

### Intermediate
1. **[Article] ControlNet Explained** (HuggingFace Blog)
2. **[Paper] Stable Video Diffusion** (Stability AI)

### Advanced (Engineer Level)
1. **[Code] MimicMotion Repository** (Tencent) - The core of our engine.
2. **[Concept] Rotary Positional Embeddings** - How transformers understand "time".

---

## 🛠️ System Architecture

### The "Stack"
- **AI Brain**: PyTorch + SVD-XT (Stable Video Diffusion) + MimicMotion.
- **API**: FastAPI (Python). Asynchronous job queue.
- **UI**: Next.js (React).

### Production Deployment
We use **Docker** to package this complex mess into a single box.
- Run `deploy.sh` (Linux) or `deploy.bat` (Windows).
- This spins up 3 services:
    1. `api`: The GPU worker.
    2. `web`: The User Interface.
    3. `redis`: (Optional) The message broker.

---

## ⚡ Troubleshooting

> **"My output faces look blurry!"**
> This is a known limitation of SVD. The "Ghost in the machine" cares more about motion than faces.
> *Fix*: We will implement a "Face Enhancer" pass (Phase 3) using GFPGAN.

> **"It says CUDA Out of Memory!"**
> 1080p Video requires ~24GB VRAM.
> *Fix*: Lower resolution to `576x1024` or rent a bigger GPU (A100).

