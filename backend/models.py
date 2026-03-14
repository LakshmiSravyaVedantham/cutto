import uuid
from typing import Literal

from pydantic import BaseModel, Field


class Scene(BaseModel):
    scene_id: str = ""
    scene_number: int = Field(gt=0)
    narration: str = Field(min_length=1)
    speaker: str = "narrator"  # "narrator", "character_1", "character_2", etc.
    visual_prompt: str = Field(min_length=1)
    visual_type: Literal["image", "video"] = "image"
    target_duration: int = Field(default=5, ge=1, le=120)

    def model_post_init(self, __context):
        if not self.scene_id:
            self.scene_id = str(uuid.uuid4())


class ScenePlan(BaseModel):
    video_id: str = ""
    title: str = Field(min_length=1)
    total_scenes: int = Field(gt=0, le=20)
    mood: str
    visual_style_anchor: str = ""
    audio_driven: bool = (
        True  # True = audio drives duration (natural voice), False = video drives
    )
    scenes: list[Scene]

    def model_post_init(self, __context):
        if not self.video_id:
            self.video_id = str(uuid.uuid4())
        # Keep total_scenes in sync with actual scene count
        if self.total_scenes != len(self.scenes):
            self.total_scenes = len(self.scenes)


class PipelineProgress(BaseModel):
    video_id: str
    scene: int
    step: Literal["visual", "voiceover", "clip", "assembly", "complete", "error"]
    status: Literal["in_progress", "done", "error"]
    message: str = ""
    thumbnail: str = ""  # base64-encoded JPEG thumbnail for completed scenes
