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
from backend.services import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CutTo")

_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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


# Store video paths by video_id
video_paths: dict[str, str] = {}


@app.get("/videos/{video_id}/final.mp4")
async def serve_video(video_id: str):
    """Serve generated video file."""
    path = video_paths.get(video_id)
    if path and os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=f"cutto-{video_id[:8]}.mp4")
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
    return {
        "status": "ok",
        "service": "cutto",
        "version": "0.1.0",
    }


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
            "Hi! I'm ready to create a video. What kind of video can you help me make?"
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
                "text": "Hi! I'm CutTo, your AI video director. I can create any kind of video — animated stories, medical explainers, tutorials, product demos, documentaries, and more. What would you like to make?",
            }
        )

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "text":
                user_msg = data["text"]
                # User message shown optimistically on frontend — no echo needed

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

            elif data["type"] == "update_plan" and data.get("plan"):
                try:
                    from backend.models import ScenePlan
                    updated = ScenePlan(**data["plan"])
                    current_plan = updated
                    session.scene_plan = updated
                    await ws.send_json({
                        "type": "scene_plan",
                        "plan": current_plan.model_dump()
                    })
                except Exception as e:
                    logger.error(f"Plan update error: {e}")
                    await ws.send_json({
                        "type": "error",
                        "message": f"Failed to update plan: {e}"
                    })

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
        # Upload to GCS if available, otherwise serve locally
        if storage.is_available():
            video_url = storage.upload_video(video_path, plan.video_id)
        else:
            video_paths[plan.video_id] = video_path
            video_url = f"/videos/{plan.video_id}/final.mp4"
        await ws.send_json(
            {
                "type": "complete",
                "video_id": plan.video_id,
                "video_url": video_url,
            }
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        friendly = "Video generation failed. Please try again."
        if "timed out" in str(e).lower():
            friendly = "Video generation timed out. Try a simpler scene or fewer scenes."
        elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
            friendly = "API rate limit reached. Please wait a moment and try again."
        elif "too many scene failures" in str(e).lower():
            friendly = "Multiple scenes failed to generate. Try simpler visual descriptions."
        await ws.send_json({"type": "error", "message": friendly})
