from pydantic import BaseModel
from typing import Literal
import uuid


class Scene(BaseModel):
    scene_id: str = ""
    scene_number: int
    narration: str
    visual_prompt: str
    visual_type: Literal["image", "video"] = "image"
    target_duration: int = 5

    def model_post_init(self, __context):
        if not self.scene_id:
            self.scene_id = str(uuid.uuid4())


class ScenePlan(BaseModel):
    video_id: str = ""
    title: str
    total_scenes: int
    mood: str
    visual_style_anchor: str = ""
    scenes: list[Scene]

    def model_post_init(self, __context):
        if not self.video_id:
            self.video_id = str(uuid.uuid4())


class PipelineProgress(BaseModel):
    video_id: str
    scene: int
    step: Literal["visual", "voiceover", "clip", "assembly", "complete"]
    status: Literal["in_progress", "done", "error"]
    message: str = ""
