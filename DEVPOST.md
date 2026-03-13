# CutTo — Devpost Submission

## Project Name
CutTo

## Tagline
Describe any video. We'll direct it.

## Category
Creative Storyteller

## About

CutTo is an AI video director that turns a conversation into a finished video. Tell the AI what you want — an animated story, medical explainer, product demo, tutorial, documentary — and it writes the script, generates animated visuals, adds multi-character voiceover with lipsync, and delivers a finished MP4.

### How it works

1. **Conversation** — Describe your video idea. The AI asks 2-3 follow-up questions about story, mood, and visual style.
2. **Scene Plan** — Gemini generates a scene-by-scene plan with inline preview images. Each scene has narration, a visual prompt, and speaker assignment.
3. **Edit** — Review in an interactive editor. Change narration, visuals, speakers. Add or remove scenes. Ask the AI for revisions.
4. **Generate** — Approve the plan. Veo 2.0 generates animated clips, TTS produces voiceover, Wav2Lip applies lipsync, FFmpeg assembles with background music.
5. **Watch & Download** — The finished MP4 plays in-browser.

### What makes it special

- **Interleaved text + image output** — Gemini generates preview images inline during the conversation, not as a separate step
- **3 distinct voice tracks** — narrator, character 1, character 2 with different voices
- **Wav2Lip lipsync** — automatically applied to character dialogue close-ups
- **Visual consistency** — shared Veo seed + style anchor across all scenes
- **Parallel scene processing** — 3 scenes at a time for faster generation
- **5 mood-matched background music tracks** — dramatic, upbeat, calm, inspiring, playful
- **Voice input** — speak your video idea via Web Speech API
- **Any video type** — stories, explainers, tutorials, marketing, documentaries, motivational

## Google Technologies Used

| Technology | How It's Used |
|---|---|
| **Gemini 2.0 Flash** | Text conversation and creative direction |
| **Gemini 2.5 Flash** | Interleaved text + image generation for scene previews |
| **Veo 2.0** | Animated video clip generation from text prompts |
| **Imagen 4.0** | Static image fallback when Veo is unavailable |
| **Google GenAI SDK** | All Gemini/Veo/Imagen API calls |
| **Google ADK** | Agent wrapper with function tools for structured scene planning |
| **Google Cloud TTS** | WaveNet voices for multi-character voiceover |
| **Google Cloud Run** | Production deployment (2 vCPU, 2GB RAM, Docker) |

## Tech Stack

- **Backend**: Python 3.11, FastAPI, WebSocket
- **Frontend**: React 18, Vite 5
- **Video Processing**: FFmpeg (Ken Burns, concat, music mixing, audio sync)
- **Lipsync**: Wav2Lip
- **Voice Input**: Web Speech API
- **Deployment**: Docker (multi-stage), Google Cloud Run

## Links

- **GitHub**: https://github.com/LakshmiSravyaVedantham/cutto
- **Demo Video**: [TODO — record <4 min demo]
- **Live URL**: [TODO — Cloud Run URL after deploy]

## Hackathon Requirements Checklist

- [x] Uses Gemini model (Gemini 2.0 Flash + 2.5 Flash)
- [x] Uses Google GenAI SDK + ADK
- [x] Uses Google Cloud service (Veo, Imagen, Cloud TTS, Cloud Run)
- [x] Interleaved output (Creative Storyteller mandatory) — text + images inline
- [x] Live agent interaction — real-time WebSocket with voice input
- [x] Automated cloud deployment (bonus) — deploy.sh for Cloud Run
- [x] Open source — MIT license on GitHub

## Team

Lakshmi Sravya Vedantham
