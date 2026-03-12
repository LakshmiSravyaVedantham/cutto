import os
import logging
import base64
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.agent import ConversationSession, extract_scene_plan
from backend.pipeline import run_pipeline
from backend.models import PipelineProgress
from backend.config import DEMO_SECRET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CutTo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React build if available
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir) and os.path.exists(
    os.path.join(static_dir, "index.html")
):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount(
            "/assets", StaticFiles(directory=assets_dir), name="assets"
        )

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))


# Serve generated videos
videos_dir = "/tmp"


@app.get("/videos/{video_id}/{filename}")
async def serve_video(video_id: str, filename: str):
    """Serve generated video files from temp directory."""
    # Look for the video in temp directories
    import glob

    pattern = f"/tmp/cutto_*/{filename}"
    matches = glob.glob(pattern)
    if not matches:
        pattern = f"/tmp/cutto_*/scene_*/{filename}"
        matches = glob.glob(pattern)

    # Also check for final.mp4 specifically
    pattern2 = f"/tmp/cutto_*/final.mp4"
    matches2 = glob.glob(pattern2)

    all_matches = matches + matches2
    if all_matches:
        return FileResponse(all_matches[0], media_type="video/mp4")

    return {"error": "Video not found"}


# Rate limiting: 3 videos per IP per hour
video_requests: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str) -> bool:
    now = time.time()
    hour_ago = now - 3600
    video_requests[ip] = [t for t in video_requests[ip] if t > hour_ago]
    if len(video_requests[ip]) >= 3:
        return False
    video_requests[ip].append(now)
    return True


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, key: str = Query(default="")):
    # Auth gate
    if DEMO_SECRET and key != DEMO_SECRET:
        await ws.close(code=4001, reason="Invalid key")
        return

    await ws.accept()
    client_ip = ws.client.host if ws.client else "unknown"
    session = ConversationSession()
    current_plan = None

    # Send initial greeting
    try:
        text, image_bytes, plan, started = await session.send_message(
            "Hello! I want to make a video."
        )
        await ws.send_json(
            {"type": "transcript", "role": "agent", "text": text}
        )
    except Exception as e:
        logger.error(f"Initial greeting failed: {e}")
        await ws.send_json(
            {
                "type": "transcript",
                "role": "agent",
                "text": "Hi! I'm CutTo, your AI video director. What video would you like to create today?",
            }
        )

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "text":
                user_msg = data["text"]
                await ws.send_json(
                    {"type": "transcript", "role": "user", "text": user_msg}
                )

                text, image_bytes, plan, pipeline_started = (
                    await session.send_message(user_msg)
                )

                await ws.send_json(
                    {"type": "transcript", "role": "agent", "text": text}
                )

                if image_bytes:
                    img_b64 = base64.b64encode(image_bytes).decode()
                    await ws.send_json(
                        {"type": "scene_preview", "image_data": img_b64}
                    )

                if plan:
                    current_plan = plan
                    await ws.send_json(
                        {"type": "scene_plan", "plan": plan.model_dump()}
                    )

                # Backup parser
                if not current_plan:
                    backup_plan = extract_scene_plan(text)
                    if backup_plan:
                        current_plan = backup_plan
                        await ws.send_json(
                            {
                                "type": "scene_plan",
                                "plan": current_plan.model_dump(),
                            }
                        )

                if pipeline_started and current_plan:
                    if not check_rate_limit(client_ip):
                        await ws.send_json(
                            {
                                "type": "error",
                                "message": "Rate limit exceeded. Max 3 videos per hour.",
                            }
                        )
                    else:
                        await run_video_pipeline(ws, current_plan)

            elif data["type"] == "approve" and current_plan:
                if not check_rate_limit(client_ip):
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": "Rate limit exceeded. Max 3 videos per hour.",
                        }
                    )
                else:
                    await run_video_pipeline(ws, current_plan)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


async def run_video_pipeline(ws: WebSocket, plan):
    async def progress_callback(progress: PipelineProgress):
        await ws.send_json(
            {
                "type": "pipeline_progress",
                "video_id": progress.video_id,
                "scene": progress.scene,
                "step": progress.step,
                "status": progress.status,
            }
        )

    try:
        video_path = await run_pipeline(
            plan, progress_callback=progress_callback
        )
        # Return a URL the frontend can use
        video_url = f"/videos/{plan.video_id}/final.mp4"
        await ws.send_json(
            {
                "type": "complete",
                "video_id": plan.video_id,
                "video_url": video_url,
                "video_path": video_path,
            }
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        await ws.send_json({"type": "error", "message": str(e)})
