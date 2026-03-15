# I Built an AI Video Director That Turns Lessons Into Animated Videos

*#GeminiLiveAgentChallenge #gemini #ai #python #opensource*

---

I run a kids' educational YouTube channel. Every video needs animations, voiceover, music, and careful editing — which means expensive software and hours of work per upload. Most teachers and content creators I know have the same problem: great lesson ideas, no way to turn them into videos.

I built **CutTo** to fix this. You describe a lesson in a conversation — "explain how volcanoes erupt for 8-year-olds" — and CutTo writes the script, generates animated visuals, adds voiceover with lipsync, and delivers a finished MP4 you can upload directly.

## How it works

1. **Talk to the director** — CutTo's AI has a creative director persona. It reacts to your ideas with enthusiasm: *"I'm seeing this as a cinematic journey into the earth — layers peeling away, magma rising..."* It shapes your rough idea into a visual plan.

2. **See preview images inline** — As you plan, Gemini generates preview images directly in the conversation using interleaved text + image output. You see what the AI is thinking before committing to anything.

3. **Edit the scene plan** — An interactive editor lets you modify narration, reorder scenes, change speakers, and ask the AI for revisions in natural language: "make the eruption more dramatic."

4. **Watch it generate** — Real-time progress tracking shows each scene being animated in parallel. If a scene fails, the pipeline gracefully continues with the rest.

5. **Download your video** — Multi-character voices, lipsync on close-ups, mood-matched background music. Ready to upload.

CutTo supports 6 video categories: animated stories, science explainers, documentaries, tutorials, marketing videos, and motivational pieces. The project has 119 automated tests covering the pipeline, services, agent, and API.

## The real use case: kids' education

Here's why this matters to me personally. My YouTube channel targets kids ages 6-12. A typical video — "How does the heart pump blood?" — requires:

- Writing a kid-friendly script
- Finding or creating animated visuals
- Recording voiceover (or hiring someone)
- Adding background music
- Editing everything together in Premiere/DaVinci

That's 4-8 hours per video minimum, or $200+ if I outsource it.

With CutTo, I describe the lesson, review the scene plan, and click generate. The entire process takes one conversation. The AI handles the creative direction, visual generation, voice synthesis, and assembly.

## The tech stack

| Component | Technology |
|---|---|
| Conversation + Planning | Gemini 2.5 Flash (interleaved text + image) |
| Video Generation | Veo 3.0 (cinematic clips) with FLOW prompt decomposition |
| Image Fallback | Imagen 4.0 + Gemini native image |
| Voice Synthesis | Google Cloud TTS (Journey/Chirp3 HD) + edge-tts |
| Lipsync | Wav2Lip |
| Assembly | FFmpeg (Ken Burns, concat, music mixing) |
| Agent Framework | Google ADK (3 specialized agents) |
| Backend | Python 3.11, FastAPI, WebSocket |
| Frontend | React 18, Vite 5, Web Speech API |
| Deployment | Docker (multi-stage), Google Cloud Run |

## Architecture

```
User speaks lesson idea
    |
    v
Gemini generates scene plan with inline preview images
    |
    v
Interactive scene editor (edit, reorder, revise with AI)
    |
    v
FLOW Prompt Decomposition (subject/action/camera/lighting/palette/texture)
    |
    v
Pipeline: Veo 3.0 -> TTS -> FFmpeg crossfade -> Final MP4
(staggered parallel batches, circuit breaker on failures)
```

The ADK multi-agent architecture uses three specialized agents:
- **Creative Director** — shapes the vision, asks clarifying questions
- **Storyboard Artist** — generates structured scene plans with visual prompts
- **Orchestrator** — routes between agents based on conversation state

Each agent has its own tools and system instructions. The Creative Director has access to image generation for inline previews; the Storyboard Artist outputs structured JSON that feeds directly into the video pipeline.

## What I learned

**Gemini's interleaved output is the killer feature for creative tools.** Showing preview images *during* the conversation — not after — makes planning feel immediate. The user sees what the AI is imagining and can redirect before any expensive generation happens.

**Visual consistency requires engineering.** I use a "visual style anchor" — a detailed description of art style, color palette, and character appearances — prepended to every scene's visual prompt. Combined with Veo's seed parameter (all scenes share a seed derived from video_id), characters and style stay consistent across scenes.

**Audio-video sync is harder than it looks.** I implemented two modes: audio-driven (default — preserves natural voice speed, video adjusts) and video-driven (audio speeds up or pads to match video length). Getting FFmpeg's atempo chaining right for ratios > 2x was the trickiest bug in the project.

**The persona makes the product.** A generic "video generator" feels like a tool. A creative director with opinions and enthusiasm feels like a collaborator. The difference is entirely in the system prompt and conversation design.

## Try it yourself

```bash
git clone https://github.com/LakshmiSravyaVedantham/cutto.git
cd cutto
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
cp -r frontend/dist static
echo "GOOGLE_API_KEY=your-key" > .env
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000, click a quick-start template like "How the heart pumps blood", and watch the AI direct your video.

---

[GitHub Repo](https://github.com/LakshmiSravyaVedantham/cutto) | MIT License

Built for the Google Gemini Live Agent Challenge (Creative Storyteller category). Every existing tool makes you the editor. CutTo makes you the director.
