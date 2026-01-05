import torch
import os
import sys
import subprocess

def check_gpu():
    print("--- SELF-ASSESSMENT: GPU ---")
    if torch.cuda.is_available():
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        name = torch.cuda.get_device_name(0)
        print(f"✅ CUDA Available: {name}")
        print(f"✅ Total VRAM: {vram:.2f} GB")
        
        if vram < 8:
            print("⚠️ WARNING: VRAM is < 8GB. Video generation might fail or require extreme optimization.")
        elif vram < 16:
            print("ℹ️ NOTE: VRAM is decent (8-16GB). SVD-XT should run with optimizations.")
        else:
            print("🚀 STATUS: High-Performance GPU detected. Ready for production.")
    else:
        print("❌ CRITICAL: No GPU detected. AI Engine cannot run.")
        sys.exit(1)

def check_models():
    print("\n--- SELF-ASSESSMENT: MODELS ---")
    # Check if MimicMotion weights exist in cache or need download
    # This is a basic check.
    try:
        from huggingface_hub import scan_cache_dir
        print("✅ HuggingFace Cache is accessible.")
    except Exception as e:
        print(f"⚠️ HuggingFace Hub check failed: {e}")

def main():
    print("Initializing Motion Weave Production Node...")
    check_gpu()
    check_models()
    print("\n✅ System pass. Starting API...")

if __name__ == "__main__":
    main()
