# I Built an AI Video Director with Gemini, Veo, and Google Cloud

*#GeminiLiveAgentChallenge #gemini #ai #python #opensource*

---

Making a professional video today means juggling video editing software, stock footage, voiceover talent, background music, and hours of tedious editing. Most people with great ideas never make their video because the barrier is too high.

I built **CutTo** to change that. You describe any video idea in a conversation, and CutTo writes the script, generates animated visuals, adds multi-character voiceover with lipsync, and delivers a finished MP4.

## How it works

1. **Talk to the director** — CutTo's AI has a strong creative persona. It reacts to your ideas with genuine enthusiasm: *"I love this — I'm seeing something really cinematic here..."*

2. **See preview images inline** — As you plan, Gemini generates preview images directly in the conversation using interleaved text + image output. No waiting for a separate step.

3. **Edit the scene plan** — An interactive editor lets you modify narration, reorder scenes, change speakers, and ask the AI for revisions in natural language.

4. **Watch it generate** — Real-time progress tracking shows each scene being animated. If a scene fails, the pipeline gracefully continues with the rest.

5. **Download your video** — Multi-character voices, lipsync on close-ups, mood-matched background music. All assembled automatically.

## The tech stack

| Component | Technology |
|---|---|
| Conversation + Planning | Gemini 2.0 Flash + 2.5 Flash (interleaved text + image) |
| Video Generation | Veo 2.0 (animated clips) |
| Image Fallback | Imagen 4.0 + Gemini native image |
| Voice Synthesis | Google Cloud TTS (WaveNet) + edge-tts |
| Lipsync | Wav2Lip |
| Assembly | FFmpeg (Ken Burns, concat, music mixing) |
| Agent Framework | Google ADK (3 specialized agents) |
| Backend | Python 3.11, FastAPI, WebSocket |
| Frontend | React 18, Vite 5, Web Speech API |
| Deployment | Docker (multi-stage), Google Cloud Run |

## Architecture

```
User speaks idea
    |
    v
Gemini generates scene plan with inline preview images
    |
    v
Interactive scene editor (edit, reorder, revise)
    |
    v
Pipeline: Veo -> TTS -> Wav2Lip -> FFmpeg -> Final MP4
(3 scenes in parallel, circuit breaker on failures)
```

## What I learned

**Gemini's interleaved output is magic for creative tools.** Showing preview images *during* the conversation — not after — makes planning feel immediate and collaborative. The user sees what the AI is thinking before committing to anything.

**Visual consistency needs engineering, not just prompting.** I use a "visual style anchor" (a detailed description of art style, color palette, character appearances) that gets prepended to every scene's visual prompt. Combined with Veo's seed parameter (all scenes share the same seed derived from video_id), this keeps characters and style consistent across scenes.

**The ADK multi-agent pattern maps naturally to creative workflows.** I have three agents: a Creative Director who shapes the vision, a Storyboard Artist who generates structured scene plans, and an Orchestrator who routes between them. Each has specialized tools and instructions.

**Audio-video sync is the hardest part.** I implemented two modes: video-driven (default — audio speeds up or pads to match video length) and audio-driven (video stretches to match audio). Getting FFmpeg's atempo chaining right for ratios > 2x was the trickiest bug.

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

Open http://localhost:8000, click "Start Creating", and describe your video.

---

[GitHub Repo](https://github.com/LakshmiSravyaVedantham/cutto) | MIT License

Built for the Google Gemini Live Agent Challenge (Creative Storyteller category).
