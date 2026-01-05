# Motion Weave: Technical Manual & Build Guide

## 1. System Overview & High-Level Truth
**Motion Weave** is a modular AI pipeline designed to emulate the capabilities of state-of-the-art systems like **Kling Motion Control** (Kuaishou), **Animate Anyone** (Alibaba), and **OmniHuman** (ByteDance).

### The "Truth" About End-to-End Systems
None of these commercial tools are single "black box" models. They are sophisticated pipelines that orchestrate multiple specialized networks:
1.  **Identity Encoding**: Separating user identity from motion (ReferenceNet/CLIP).
2.  **Motion Extraction**: Converting video pixels into abstract control signals (Pose/Depth/Camera Tokens).
3.  **Latent Diffusion**: The core generation engine (SVD/DiT) that creates pixels.
4.  **Temporal Consistency**: Mechanism to ensure Frame N looks like Frame N-1 (Cross-attention/Motion Modules).

## 2. Architecture Design
We enable a **Modular Architecture** to allow independent upgrades of components (e.g., swapping OpenPose for DensePose).

```mermaid
graph TD
    User[User Inputs] --> API[FastAPI Orchestrator]
    API --> Pre[Preprocessing Module]
    
    subgraph "Preprocessing"
        Pre --> Pose[Pose Extractor (OpenPose/DWpose)]
        Pre --> Depth[Depth Estimator (ZoeDepth)]
        Pre --> Audio[Audio Encoder (Wav2Vec2)]
    end
    
    subgraph "Conditioning & Encoding"
        Pose --> Control[ControlNet Adapters]
        Audio --> MotionTrans[Audio-Motion Transformer]
        Img[Ref Image] --> RefNet[ReferenceNet / IP-Adapter]
        Light[Lighting Prompt] --> SH[Spherical Harmonics Encoder]
    end
    
    subgraph "Generative Core (SVD / DiT)"
        Control & RefNet & SH --> Diffusion[Latent Diffusion Backbone]
        Diffusion --> Temp[Temporal Attention Module]
    end
    
    subgraph "Post-Processing"
        Temp --> VAE[VAE Decoder]
        VAE --> Upscale[ESRGAN / Refiner]
        Upscale --> Stitch[Chunk Stitcher (1-min logic)]
    end
    
    Stitch --> Final[Output Video]
```

## 3. Model Stack Implementation
### **Backbone: Stable Video Diffusion (SVD-XT) or AnimateAnyone**
We use SVD as the generative core due to its open weights and temporal stability.

### **Control Modules Table**
| Feature | Recommended Model | Integration Strategy |
| :--- | :--- | :--- |
| **Identity** | CLIP + ReferenceNet | Encodes the reference image features and injects them via Cross-Attention layers. |
| **Pose** | DWpose (OpenPose fork) | Extracts body keypoints. Fed into a ControlNet adapter trained for SVD. |
| **Audio** | Wav2Vec2 | Extracts phoneme features. Mapped to face latent space via a small MLP projector. |
| **Lighting** | Spherical Harmonics (SH) | Low-frequency lighting representation. Injected as a global style token. |
| **Camera** | Learnable Motion Tokens | Special LoRA adapters trained on camera movement datasets (Pan, Zoom). |

## 4. Handling 1-Minute Videos (The Chunking Strategy)
Generating 1800 frames (60s @ 30fps) in one pass is impossible on consumer hardware. We use **Overlapping Chunk Generation**:

1.  **Chunk 1**: Generate frames 0–48.
2.  **Chunk 2**: Take frames 32–48 as *context* (visual prompt). Generate frames 48–96.
3.  **Blending**: Use a linear fade or latent blend for the overlapping region (32–48) to prevent "popping".
4.  **Drift Correction**: Periodically re-inject the original Reference Image embeddings to reset identity accumulation errors.

## 5. Implementation Steps (Python & PyTorch)

### **Step 1: Environment Setup**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install diffusers transformers accelerate "opencv-python>=4.8" controlnet-aux
pip install insightface onnxruntime-gpu  # For accurate face embedding
```

### **Step 2: The Core Pipeline (`ai_engine/pipeline.py`)**
See the updated code in `ai_engine/pipeline.py` for the implementation of the `MotionWeaveEngine` class.

## 6. Training Path (From Prototype to Pro)

### **Phase 1: The Prototype (Weeks 1-4)**
*   **Goal**: 3-second clips, good identity, choppy motion.
*   **Data**: UBC-Fashion dataset (clean backgrounds).
*   **Method**: Fine-tune SVD with ReferenceNet on the dataset. Freeze the temporal layers; only train the ReferenceNet.

### **Phase 2: Motion Control (Weeks 5-8)**
*   **Goal**: Driven animation from video.
*   **Method**: Train a ControlNet adapter for SVD using calculated Pose maps.
*   **Data**: HumanVid or TikTok datasets (curated).

### **Phase 3: The Long Game (Weeks 9-12)**
*   **Goal**: 60s consistency + Audio.
*   **Method**: Implement the "Context Sliding Window" inference logic. Train audio-reactive face modules (SadTalker style).

## 7. Hardware Reality
*   **Minimum Inference**: NVIDIA RTX 3090 / 4090 (24GB VRAM). Lower VRAM requires extreme quantization (4-bit).
*   **Minimum Training**: 4x - 8x A100 (80GB). Do not attempt to train SVD from scratch on consumer cards. Use LoRA fine-tuning instead.

## 8. Open-Source Resources
*   **AnimateAnyone**: `https://github.com/HumanAIGC/AnimateAnyone` (The implementation gold standard).
*   **MagicAnimate**: `https://github.com/magic-research/magic-animate` (Good for DensePose integration).
*   **UniAnimate**: `https://github.com/ali-vilab/UniAnimate-DiT` (Best reference for the long-video stitching logic).
*   **ComfyUI**: Excellent for prototyping the node graph before coding it in Python.
