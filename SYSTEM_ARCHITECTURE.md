# Motion Weave: System Architecture & Implementation Plan

## 1. System Overview
**Motion Weave** is an end-to-end generative AI system allowing users to animate static character images using reference videos, audio, and detailed control settings (lighting, camera, etc.).

**Core Philosophy:** Modular pipeline approach, separating identity (Image) from motion (Video/Pose) and style (Lighting/Camera).

## 2. Technical Stack

### A. Frontend (UI)
- **Framework:** Next.js (React)
- **Styling:** TailwindCSS + Framer Motion (for premium animations)
- **State Management:** Zustand / React Query
- **Features:**
  - Drag & Drop Uploads (Image, Video, Audio)
  - Real-time parameter controls (Lighting, Camera, Duration)
  - Job Status Monitoring via WebSockets/Polling

### B. Backend (API & Orchestration)
- **Framework:** FastAPI (Python)
- **Task Queue:** Redis + Celery (to handle long-running GPU tasks)
- **Storage:** Local / S3-compatible for handling large video files
- **Endpoints:**
  - `/api/v1/jobs/create`: Initiate generation
  - `/api/v1/jobs/{id}`: Poll status
  - `/api/v1/assets/upload`: Handle raw inputs

### C. AI Pipeline (The "Engine")
Implemented as a modular Python package `ai_engine`.

#### **Module 1: Pre-processing**
- **Pose Extraction:** OpenPose / DWpose (extract skeletal motion from Ref Video)
- **Depth Estimation:** MiDaS / ZoeDepth (extract scene geometry)
- **Audio Processing:** Wav2Vec2 (if audio driven)

#### **Module 2: Latent Diffusion Generators**
- **Backbone:** Stable Video Diffusion (SVD) or AnimateAnyone implementation.
- **Conditioning:**
  - *ReferenceNet:* Encodes Character Image for Identity preservation.
  - *Pose Guider:* Injects motion signals into the noisy latents.
  - *Lighting/Camera:* LoRA adapters or ControlNet standard inputs.

#### **Module 3: Temporal Management (The 1-minute logic)**
- **Chunking strategy:** Generate 48 frames -> Overlap 16 frames -> Generate next 32 frames -> Blending.
- **VRAM Optimization:** CPU offloading for unused models.

#### **Module 4: Post-processing**
- **Upscaling:** Real-ESRGAN or similar for 512px -> 1080p/4k.
- **Frame Interpolation:** RIFE (to smooth 12fps -> 24/30fps).
- **FFmpeg:** Audio muxing and final encoding.

## 3. Implementation Phases

### Phase 1: Foundation (Current Step)
- Scaffold Project Structure
- Build Premium UI (Next.js)
- Build API Skeleton (FastAPI)
- Define Pipeline Interface

### Phase 2: Core Components
- Integrate OpenPose wrapper
- Setup SVD Inference Loop (Mocked initially for UI testing)
- Implement File Handling

### Phase 3: Integration
- Connect Logic to UI
- Implement "Chunking" Logic
- Add Lighting/Audio Controls
