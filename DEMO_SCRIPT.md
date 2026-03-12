# CutTo Demo Script (< 4 minutes)

## 0:00-0:20 — Problem Statement
"Making a professional video today requires video editing software, stock footage, voiceover talent, and hours of work. Most people with great ideas never make their video because the barrier is too high."

*Show: split screen of complex video editing software vs CutTo's simple chat*

## 0:20-0:40 — Solution
"CutTo is an AI Video Director. You describe any video idea in conversation — a medical explainer, an animated story, a product demo — and CutTo writes the script, generates animated visuals, adds multi-character voiceover with lipsync, and delivers a finished video."

*Show: CutTo landing page, click "Start Creating"*

## 0:40-2:30 — Live Demo
1. **Voice input** (0:40-1:00): Click the mic button, speak: "Create an animated story about a robot who discovers music for the first time"
   - Show the voice waveform overlay
   - Show the AI responding with creative enthusiasm (strong persona)

2. **Interleaved images** (1:00-1:20): As Gemini generates the scene plan, preview images appear inline in the conversation
   - This is the Creative Storyteller mandatory requirement

3. **Scene plan editor** (1:20-1:50):
   - Show the 8-scene plan with speaker badges (Narrator, Char 1, Char 2)
   - Edit a scene's narration
   - Reorder scenes with arrow buttons
   - Show estimated duration in header
   - Ask AI for a revision: "make scene 3 more emotional"

4. **Generate** (1:50-2:10): Click "Looks great — Make my video!"
   - Show real-time progress: each scene animating, compositing
   - If a scene fails, show the red X error indicator (graceful handling)

5. **Final video** (2:10-2:30): Video plays in browser
   - Point out: multi-character voices, lipsync on close-ups, background music
   - Download button

## 2:30-3:00 — Architecture (brief)
*Flash the architecture diagram from README*

"Under the hood: Gemini drives the creative conversation with interleaved text and images. The ADK multi-agent architecture routes between a Creative Director and Storyboard Artist. Veo 2.0 generates animated clips, Imagen 4.0 provides fallback images, Google Cloud TTS creates multi-character voiceover, and Wav2Lip adds lipsync. Everything runs on Cloud Run."

## 3:00-3:15 — Cloud Deployment Proof
*Show Google Cloud Console with Cloud Run service running*

## 3:15-3:30 — Categories
"CutTo handles 6 video types: stories, explainers, documentaries, tutorials, marketing videos, and motivational pieces. All from a single conversation."

*Quick montage: show 2-3 different video types*

## 3:30-3:45 — Wrap
"CutTo — describe any video. We'll direct it."

---

## Tips for Recording
- Use OBS or QuickTime
- Record at 1080p or higher
- One continuous take if possible — shows confidence
- Pick a visually stunning topic (fantasy, space, nature)
- Pre-test the full flow before recording
- Upload to YouTube (unlisted is fine)
