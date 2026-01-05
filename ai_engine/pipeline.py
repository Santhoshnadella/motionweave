import os
import sys
import torch
import numpy as np
from PIL import Image

# Add MimicMotion to path
current_dir = os.path.dirname(os.path.abspath(__file__))
mimic_motion_path = os.path.join(current_dir, "mimic_motion")
if mimic_motion_path not in sys.path:
    sys.path.append(mimic_motion_path)

# Try to import MimicMotionPipeline
try:
    from mimicmotion.pipelines.pipeline_mimicmotion import MimicMotionPipeline
except ImportError as e:
    print(f"Warning: MimicMotion library not found or incomplete: {e}")
    MimicMotionPipeline = None

from controlnet_aux import DWposeDetector
from diffusers.utils import export_to_video
try:
    from gfpgan import GFPGANer
except ImportError:
    print("GFPGAN not found. Face enhancement disabled.")
    GFPGANer = None

class MotionWeaveEngine:
    def __init__(self, device="cuda", model_id="Tencent/MimicMotion", use_wan=False):
        self.device = device
        self.use_wan = use_wan
        self.dtype = torch.float16 if device == "cuda" else torch.float32
        print(f"Initializing Motion Weave Engine on {device} [Wan2.1: {use_wan}]...")

        if not torch.cuda.is_available() and device == "cuda":
            print("WARNING: CUDA not found, using CPU. This will be extremely slow.")
            self.device = "cpu"
            self.dtype = torch.float32

        self.pipeline = None
        self.pose_detector = None
        self.face_enhancer = None
        
        self.init_models(model_id)

    def init_models(self, model_id):
        if self.use_wan:
            self._load_wan_pipeline()
        else:
            self._load_pose_detector()
            self._load_mimic_motion(model_id)
            
        self._load_face_enhancer()

    def _load_wan_pipeline(self):
        print("Loading Wan 2.1 Pipeline (Placeholder)...")
        # TODO: Implement actual Wan 2.1 loading logic when weights are available
        pass

    def _load_face_enhancer(self):
        if GFPGANer:
            print("Loading GFPGAN Face Enhancer...")
            try:
                self.face_enhancer = GFPGANer(
                    model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.0.pth',
                    upscale=1,
                    arch='clean',
                    channel_multiplier=2,
                    bg_upsampler=None
                )
            except Exception as e:
                print(f"GFPGAN Load Failed: {e}")

    def _load_pose_detector(self):
        print("Loading DWPose Detector...")
        try:
            self.pose_detector = DWposeDetector.from_pretrained(
                "yzd-v/DWPose", 
                torch_dtype=self.dtype
            ).to(self.device)
            print("DWPose loaded successfully.")
        except Exception as e:
            print(f"Failed to load DWPose: {e}")

    def _load_mimic_motion(self, model_id):
        print(f"Loading MimicMotion Pipeline from {model_id}...")
        if MimicMotionPipeline is None:
            print("MimicMotionPipeline class is missing. Check git clone.")
            return

        try:
            self.pipeline = MimicMotionPipeline.from_pretrained(
                model_id, 
                torch_dtype=self.dtype,
                variant="fp16" if self.device == "cuda" else None
            ).to(self.device)
            
            # Save VRAM
            self.pipeline.enable_vae_slicing()
            print("MimicMotion pipeline loaded successfully.")

        except Exception as e:
            print(f"Failed to load MimicMotion Pipeline: {e}")

    def preprocess_driving_video(self, video_path):
        """
        Reads MP4, extracts frames, runs DWPose on each frame to get skeleton.
        Returns: tensor of shape (f, h, w, c) normalized for MimicMotion.
        """
        print(f"Extracting skeletons from {video_path}...")
        import cv2
        cap = cv2.VideoCapture(video_path)
        pose_frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Convert BGR (OpenCV) to RGB (PIL)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            
            # Run DWPose
            # Note: This is slow. In production, we batch this using a dataloader.
            pose = self.pose_detector(pil_img)
            pose_frames.append(pose)
            
        cap.release()
        
        if not pose_frames:
            raise ValueError("No frames extracted from video")
            
        print(f"Extracted {len(pose_frames)} pose frames.")
        return pose_frames

    def generate(self, ref_image_path, pose_video_path, output_path, seed=42, num_frames=16):
        """
        Main generation entry point.
        """
        if not self.pipeline:
            print("Pipeline not initialized.")
            return False

        print(f"Starting generation for {ref_image_path}...")
        
        # 1. Load Reference Image
        if not os.path.exists(ref_image_path):
            print(f"Reference image not found: {ref_image_path}")
            return False
        
        # Resize ref image to standard aspect ratio (9:16 vertical usually)
        ref_image = Image.open(ref_image_path).convert("RGB")
        ref_image = ref_image.resize((576, 1024)) 
        
        # 2. Extract Pose Signals
        try:
            pose_frames_pil = self.preprocess_driving_video(pose_video_path)
        except Exception as e:
            print(f"Pose extraction failed: {e}")
            return False
        
        # Limit frames for safety if VRAM is low
        # processing_frames = pose_frames_pil[:num_frames] 
        # For now, let's just take the first 16 frames to prove it works
        processing_frames = pose_frames_pil[:16]

        print("Running Inference (MimicMotion)...")
        generator = torch.Generator(device=self.device).manual_seed(seed)
        
        try:
            # The pipeline expects a list of PIL images for the pose
            output = self.pipeline(
                ref_image, 
                image_pose=processing_frames, 
                num_frames=len(processing_frames), 
                tile_size=16, 
                tile_overlap=4,
                height=1024, 
                width=576, 
                fps=25,
                noise_aug_strength=0.0, 
                generator=generator,
                num_inference_steps=25, 
                guidance_scale=2.0, 
                context_schedule="uniform",
                context_frames=12,
                context_stride=1,
                context_overlap=4,
            )
            
            frames = output.frames[0]
            
            # PHASE 3: Face Enhancement
            frames = self.enhance_faces(frames)

            print(f"Saving video to {output_path}")
            export_to_video(frames, output_path, fps=25)
            
            return True
            
        except Exception as e:
            print(f"Inference failed: {e}")
            return False

    # PHASE 3: Optimization Methods
    def enhance_faces(self, frames):
        """
        Uses GFPGAN to restore face details in long shots.
        """
        if not self.face_enhancer:
            return frames
            
        print("Running Face Enhancer (GFPGAN) on frames...")
        enhanced_frames = []
        for pil_frame in frames:
            # Convert PIL RGB -> OpenCV BGR
            img = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)
            
            # Run GFPGAN
            _, _, output = self.face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
            
            # Convert back to PIL RGB
            out_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            enhanced_frames.append(Image.fromarray(out_rgb))
            
        return enhanced_frames

    def smooth_stitch(self, chunk_a, chunk_b, overlap=4):
        """
        Cross-fades overlapping frames to prevent 'scene cut' effect.
        Assuming chunk_a and chunk_b list of PIL Images.
        """
        if not chunk_a: return chunk_b
        
        # Split A
        body_a = chunk_a[:-overlap]
        tail_a = chunk_a[-overlap:]
        
        # Split B
        head_b = chunk_b[:overlap]
        body_b = chunk_b[overlap:]
        
        blended = []
        for i in range(overlap):
            alpha = i / (overlap - 1) # 0.0 to 1.0
            # Blend tail_a[i] with head_b[i]
            img1 = tail_a[i]
            img2 = head_b[i]
            blend_img = Image.blend(img1, img2, alpha)
            blended.append(blend_img)
            
        return body_a + blended + body_b
            
        except Exception as e:
            print(f"Inference failed: {e}")
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", type=str, help="Reference image path")
    parser.add_argument("--vid", type=str, help="Driving video path")
    args = parser.parse_args()
    
    engine = MotionWeaveEngine()
    if args.ref and args.vid:
        engine.generate(args.ref, args.vid, "output.mp4")
