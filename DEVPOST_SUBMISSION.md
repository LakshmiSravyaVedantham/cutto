# CutTo — Devpost Submission Draft

## Title
CutTo — AI Video Director

## Tagline
Turn any lesson into an animated video — describe it in conversation, CutTo directs the rest.

## Category
Creative Storyteller

---

## Inspiration
I run a kids' educational YouTube channel. Every video needs animated visuals, voiceover, music, and editing — which means expensive software and 4-8 hours per upload. Most teachers and educational content creators have the same problem: great lesson ideas, no practical way to turn them into engaging videos. I wanted to make video creation as simple as describing a lesson in a conversation.

## What it does
CutTo is an AI Video Director that turns a lesson idea into a finished animated video. You describe what you want to teach (via text or voice), and CutTo:

1. **Shapes the vision** — A creative AI director with a strong persona collaborates on the concept: "I'm seeing this as a journey inside the earth — layers peeling away, magma chambers glowing..."
2. **Plans the video** — Gemini generates a scene-by-scene plan with inline preview images (interleaved text + image output) so you see the visual direction before committing
3. **Lets you edit** — An interactive scene editor lets you modify narration, visuals, speakers, reorder scenes, and ask the AI for revisions in natural language
4. **Generates the video** — Veo 2.0 creates animated clips, Cloud TTS produces multi-character voiceover, Wav2Lip applies lipsync, and FFmpeg assembles everything with mood-matched music
5. **Delivers the result** — Watch, download, and upload the finished MP4 directly to your channel

CutTo supports 6 video categories: animated stories, science/medical explainers, documentaries, tutorials, marketing videos, and motivational pieces. Built specifically for educational content creators who need professional-quality videos without professional-level budgets.

## How we built it
- **Frontend**: React 18 + Vite 5, WebSocket communication, Web Speech API for voice input
- **Backend**: Python 3.11 + FastAPI, WebSocket server, pipeline orchestrator
- **AI Conversation**: Gemini 2.5 Flash (interleaved text + image) via google-genai SDK
- **ADK Integration**: Multi-agent architecture with 3 specialized agents (Creative Director, Storyboard Artist, Orchestrator) using Google ADK with 4 function tools
- **Video Generation**: Veo 2.0 for animated clips, with fallback chain to Imagen 4.0 and Gemini native image generation
- **Voice Synthesis**: Google Cloud TTS (WaveNet voices) with edge-tts fallback, 3 distinct character voices
- **Lipsync**: Wav2Lip for automatic mouth sync on character dialogue scenes
- **Video Processing**: FFmpeg for Ken Burns effect, clip assembly, audio adjustment, and background music mixing
- **Deployment**: Multi-stage Docker build (Node 18 + Python 3.11-slim), Google Cloud Run with deploy script

### Key Technical Decisions
- **Visual consistency**: All scenes share a Veo seed (derived from video_id hash) for consistent character design
- **Parallel processing**: Scenes processed in batches of 3 to balance speed against Veo rate limits
- **Audio/video sync**: Two modes — video-driven (default, audio adjusts to video length) and audio-driven (video adjusts to audio length)
- **Circuit breaker**: Pipeline aborts after 3+ scene failures to fail fast
- **Exponential backoff**: WebSocket reconnection with 1s→30s delay

## Challenges we ran into
- Veo 2.0 rate limits required careful batching and a fallback chain (Veo → Imagen → Gemini native image)
- Maintaining visual consistency across scenes — solved with seed parameters and style anchor text
- Audio/video duration sync — implemented two sync modes with FFmpeg atempo chaining
- Gemini interleaved output requires specific model + modality configuration that differs from text-only calls

## Accomplishments that we're proud of
- End-to-end video generation from a single conversation — no editing tools needed
- The creative director persona makes the AI feel like a real collaborator, not just a tool
- Multi-agent ADK architecture with specialized roles (Director for creative vision, Storyboard for structured planning)
- Voice input breaks the "text box paradigm" — press V or click the mic to speak naturally
- Reference image upload — upload a photo or mood board and the AI matches the visual style
- Polish details judges notice: undo toast on scene deletion, video retry button, connection error recovery, keyboard shortcuts, smooth glassmorphism UI
- Edit Scenes from the done screen — tweak and regenerate without starting over
- 116 automated tests covering the pipeline, services, agent, API, and ADK agents

## What we learned
- Gemini's interleaved text + image output is powerful for creative workflows — showing preview images during conversation makes planning feel immediate
- Veo's seed parameter is critical for visual consistency but isn't widely documented
- ADK's agent framework provides clean separation of concerns for multi-step creative workflows
- The gap between "AI generates content" and "AI directs a production" is mostly about persona and workflow design

## What's next for CutTo
- **Curriculum integration** — teachers paste a learning objective, CutTo generates a full lesson video series
- **Multi-language support** — narration in any language for global classrooms
- **Template library** — pre-built templates for common educational topics (human body, solar system, history)
- **Veo 3.1 integration** — native audio in video clips for even better quality
- **Export to social media formats** — vertical for TikTok/YouTube Shorts, square for Instagram

---

## Built With
gemini, veo, imagen, google-cloud-tts, google-cloud-run, google-adk, fastapi, react, ffmpeg, wav2lip, python, javascript, websockets, docker

## Bonus Points Claimed
- **Blog post** (+0.6): Published on Dev.to — [link to add after publishing]
- **Automated deployment** (+0.2): GitHub Actions workflow for Cloud Run (`.github/workflows/deploy.yml`) — manual trigger, multi-stage Docker build
- **GDG membership** (+0.2): Member of Google Developer Groups — [link to add after joining]

### How to claim GDG membership bonus
1. Go to https://gdg.community.dev/
2. Find and join your local GDG chapter
3. Add your GDG profile link to this submission

## Links
- **GitHub**: https://github.com/LakshmiSravyaVedantham/cutto
- **Demo URL**: https://cutto-vu7xxy6oaa-uc.a.run.app
- **Demo Video**: [YouTube URL — fill after recording]
