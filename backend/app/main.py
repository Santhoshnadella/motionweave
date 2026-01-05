from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import shutil
import os
import uuid
import json
import sys
from pathlib import Path

# --- MOTION WEAVE INTEGRATION ---
# Add root project dir to path to find ai_engine
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

try:
    from ai_engine.pipeline import MotionWeaveEngine
    print("AI Engine module found.")
except ImportError as e:
    print(f"Error importing AI Engine: {e}")
    MotionWeaveEngine = None

app = FastAPI(title="Motion Weave API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = str(ROOT_DIR / "backend" / "uploads")
OUTPUT_DIR = str(ROOT_DIR / "backend" / "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount Output directory for serving video files
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# Job Store (In-Memory for V1)
jobs = {}

# Global Engine Instance
# We load it lazily or on startup.
engine_instance = None

def get_engine():
    global engine_instance
    if engine_instance is None and MotionWeaveEngine:
        try:
            print("Initializing AI Engine Model Stack...")
            engine_instance = MotionWeaveEngine()  # Loads models to GPU
        except Exception as e:
            print(f"CRITICAL: Engine failed to load: {e}")
    return engine_instance

# Pydantic models
class LightingConfig(BaseModel):
    key: str = "left" 
    intensity: float = 0.8
    env: Optional[str] = "studio"

class GenerationConfig(BaseModel):
    duration: int = 5
    resolution: str = "1080p"
    camera_motion: str = "static"
    lighting: LightingConfig

class MotionPipelineWorker:
    """
    Handles the asynchronous generation task.
    """
    def process_job(self, job_id, config):
        print(f"[Worker] Starting Job {job_id}")
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 5
        jobs[job_id]["stage"] = "Initializing Engine"

        engine = get_engine()
        
        if not engine:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "AI Engine could not be initialized."
            return

        # Paths
        char_path = config["char_path"]
        ref_path = config["ref_path"]
        output_filename = f"{job_id}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        jobs[job_id]["stage"] = "Generating Animation"
        jobs[job_id]["progress"] = 20

        try:
            # CALL THE REAL ENGINE
            # This is a blocking call on the GPU
            success = engine.generate(
                ref_image_path=char_path,
                pose_video_path=ref_path,
                output_path=output_path,
                num_frames=16 + (config.get("duration", 5) * 5) # Rough logic
            )
            
            if success:
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["progress"] = 100
                jobs[job_id]["output_url"] = f"http://localhost:8000/outputs/{output_filename}"
                print(f"[Worker] Job {job_id} Success")
            else:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "Generation pipeline returned False"

        except Exception as e:
            print(f"Worker Error: {e}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)

pipeline_worker = MotionPipelineWorker()

@app.post("/api/v1/jobs/create")
async def create_job(
    background_tasks: BackgroundTasks,
    character_image: UploadFile = File(...),
    reference_video: UploadFile = File(...),
    audio: Optional[UploadFile] = File(None),
    config_json: str = Form(...) 
):
    job_id = str(uuid.uuid4())
    
    # SAVE ASSETS
    char_path = os.path.join(UPLOAD_DIR, f"{job_id}_char.png")
    ref_path = os.path.join(UPLOAD_DIR, f"{job_id}_ref.mp4")
    
    with open(char_path, "wb") as f:
        shutil.copyfileobj(character_image.file, f)
    with open(ref_path, "wb") as f:
        shutil.copyfileobj(reference_video.file, f)
        
    # PARSE CONFIG
    try:
        raw_config = json.loads(config_json)
    except json.JSONDecodeError:
        raw_config = {}

    full_config = {
        "char_path": char_path,
        "ref_path": ref_path,
        **raw_config 
    }

    job_data = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "stage": "Queued",
        "config": full_config
    }
    jobs[job_id] = job_data
    
    # DISPATCH
    background_tasks.add_task(pipeline_worker.process_job, job_id, full_config)
    
    return job_data

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})
