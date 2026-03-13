import base64
import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.agent import ConversationSession, extract_scene_plan
from backend.config import DEMO_SECRET
from backend.models import PipelineProgress
from backend.pipeline import run_pipeline
from backend.services import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.config import (
        GEMINI_IMAGE_MODEL,
        GEMINI_MODEL,
        GOOGLE_API_KEY,
        IMAGEN_MODEL,
        VEO_MODEL,
    )

    logger.info("=" * 50)
    logger.info("CutTo v0.1.0 — AI Video Director")
    logger.info("=" * 50)
    logger.info(f"  Gemini text model:  {GEMINI_MODEL}")
    logger.info(f"  Gemini image model: {GEMINI_IMAGE_MODEL}")
    logger.info(f"  Imagen model:       {IMAGEN_MODEL}")
    logger.info(f"  Veo model:          {VEO_MODEL}")
    logger.info(f"  API key configured: {'yes' if GOOGLE_API_KEY else 'NO'}")
    logger.info(
        f"  Cloud Storage:      {'enabled' if storage.is_available() else 'disabled'}"
    )
    logger.info(f"  Demo gate:          {'enabled' if DEMO_SECRET else 'disabled'}")
    logger.info("=" * 50)
    yield


app = FastAPI(
    title="CutTo",
    version="0.1.0",
    description="AI Video Director — describe any video idea, get a finished video",
    lifespan=lifespan,
)

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
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

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
        return FileResponse(
            path, media_type="video/mp4", filename=f"cutto-{video_id[:8]}.mp4"
        )
    video_bytes = storage.download_video(video_id)
    if video_bytes:
        return Response(
            content=video_bytes,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="cutto-{video_id[:8]}.mp4"'
            },
        )
    return JSONResponse({"error": "Video not found"}, status_code=404)


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


@app.get("/api/categories")
async def list_categories():
    """Return supported video categories with examples."""
    from backend.adk_agent import list_video_categories

    return list_video_categories()


@app.get("/api/config")
async def get_config():
    """Return public configuration (no secrets)."""
    from backend.config import GEMINI_IMAGE_MODEL, GEMINI_MODEL, IMAGEN_MODEL, VEO_MODEL

    return {
        "models": {
            "conversation": GEMINI_MODEL,
            "image_generation": GEMINI_IMAGE_MODEL,
            "video_generation": VEO_MODEL,
            "image_fallback": IMAGEN_MODEL,
        },
        "features": {
            "voice_input": True,
            "image_upload": True,
            "lipsync": True,
            "multi_character_voices": True,
            "scene_reordering": True,
            "background_music": True,
            "crossfade_transitions": True,
            "ai_prompt_enhancement": True,
            "scene_thumbnails": True,
            "quick_start_templates": True,
        },
        "limits": {
            "max_scenes": 20,
            "max_duration_per_scene": 120,
            "videos_per_hour": 3,
        },
    }


@app.post("/api/plan")
async def create_plan(body: dict):
    """REST endpoint for ADK agent plan_video tool — judges can test directly.

    POST /api/plan {"description": "Explain how the human heart works"}
    """
    description = body.get("description", "")
    if not description:
        return JSONResponse({"error": "Missing 'description' field"}, status_code=400)
    from backend.adk_agent import plan_video

    result = plan_video(description)
    return result


@app.get("/api/agent")
async def agent_info():
    """Describe the ADK multi-agent architecture — judges can inspect the agent graph."""
    from backend.adk_agent import director_agent, root_agent, storyboard_agent

    def agent_summary(agent):
        return {
            "name": agent.name,
            "model": agent.model,
            "description": agent.description,
            "tools": [t.__name__ for t in agent.tools],
        }

    return {
        "architecture": "multi-agent",
        "framework": "Google ADK",
        "root_agent": {
            **agent_summary(root_agent),
            "sub_agents": [
                agent_summary(director_agent),
                agent_summary(storyboard_agent),
            ],
        },
        "tool_count": len(root_agent.tools),
        "description": (
            "CutTo uses a 3-agent ADK architecture: the root orchestrator routes "
            "between a Creative Director (vision & conversation) and a Storyboard "
            "Artist (structured scene planning). Each agent has specialized tools."
        ),
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

    # Send static welcome — no Gemini call, no auto-chat
    await ws.send_json(
        {
            "type": "transcript",
            "role": "agent",
            "text": "Hi! I'm CutTo, your AI video director. Tell me what video you'd like to create — an animated story, medical explainer, tutorial, product demo, documentary, or anything else.",
        }
    )

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "text":
                user_msg = data["text"]
                # User message shown optimistically on frontend — no echo needed

                # Decode optional reference image from base64
                ref_image_bytes = None
                if data.get("image"):
                    try:
                        from backend.agent import MAX_IMAGE_SIZE

                        raw = data["image"]
                        # Strip optional data-URI prefix
                        if "," in raw:
                            raw = raw.split(",", 1)[1]
                        ref_image_bytes = base64.b64decode(raw)
                        if len(ref_image_bytes) > MAX_IMAGE_SIZE:
                            await ws.send_json(
                                {
                                    "type": "error",
                                    "message": "Image too large. Maximum size is 5 MB.",
                                }
                            )
                            ref_image_bytes = None
                    except Exception:
                        logger.warning("Failed to decode uploaded image, ignoring")
                        ref_image_bytes = None

                text, image_bytes, plan, pipeline_started = await session.send_message(
                    user_msg, image_bytes=ref_image_bytes
                )

                await ws.send_json(
                    {"type": "transcript", "role": "agent", "text": text}
                )

                if image_bytes:
                    img_b64 = base64.b64encode(image_bytes).decode()
                    await ws.send_json({"type": "scene_preview", "image_data": img_b64})

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
                    await ws.send_json(
                        {"type": "scene_plan", "plan": current_plan.model_dump()}
                    )
                except Exception as e:
                    logger.error(f"Plan update error: {e}")
                    await ws.send_json(
                        {"type": "error", "message": f"Failed to update plan: {e}"}
                    )

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


async def run_video_pipeline(ws: WebSocket, plan):
    async def progress_callback(progress: PipelineProgress):
        try:
            msg = {
                "type": "pipeline_progress",
                "video_id": progress.video_id,
                "scene": progress.scene,
                "step": progress.step,
                "status": progress.status,
            }
            if progress.thumbnail:
                msg["thumbnail"] = progress.thumbnail
            await ws.send_json(msg)
        except Exception:
            logger.warning("WebSocket closed during progress update")

    try:
        video_path = await run_pipeline(plan, progress_callback=progress_callback)
        video_paths[plan.video_id] = video_path
        video_url = f"/videos/{plan.video_id}/final.mp4"

        # Upload to GCS for durability when available.
        if storage.is_available():
            uploaded = storage.upload_video(video_path, plan.video_id)
            if not uploaded:
                logger.warning(
                    "GCS upload failed for %s; falling back to local file serving",
                    plan.video_id,
                )
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
            friendly = (
                "Video generation timed out. Try a simpler scene or fewer scenes."
            )
        elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
            friendly = "API rate limit reached. Please wait a moment and try again."
        elif "too many scene failures" in str(e).lower():
            friendly = (
                "Multiple scenes failed to generate. Try simpler visual descriptions."
            )
        await ws.send_json(
            {
                "type": "pipeline_progress",
                "video_id": "",
                "scene": 0,
                "step": "error",
                "status": "error",
            }
        )
        await ws.send_json({"type": "error", "message": friendly})
