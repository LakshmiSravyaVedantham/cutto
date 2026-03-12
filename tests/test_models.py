from backend.models import Scene, ScenePlan


def test_scene_generates_id():
    scene = Scene(scene_number=1, narration="test", visual_prompt="test")
    assert scene.scene_id != ""


def test_scene_plan_generates_video_id():
    plan = ScenePlan(
        title="Test",
        total_scenes=1,
        mood="calm",
        scenes=[Scene(scene_number=1, narration="test", visual_prompt="test")],
    )
    assert plan.video_id != ""


def test_scene_plan_from_json():
    data = {
        "title": "Black Holes",
        "total_scenes": 2,
        "mood": "dramatic",
        "scenes": [
            {
                "scene_number": 1,
                "narration": "Stars collapse",
                "visual_prompt": "star collapsing",
                "target_duration": 5,
            },
            {
                "scene_number": 2,
                "narration": "Light bends",
                "visual_prompt": "light bending",
                "visual_type": "image",
            },
        ],
    }
    plan = ScenePlan(**data)
    assert len(plan.scenes) == 2
    assert plan.scenes[0].visual_type == "image"


def test_scene_default_type():
    scene = Scene(scene_number=1, narration="test", visual_prompt="test")
    assert scene.visual_type == "image"
    assert scene.target_duration == 5
