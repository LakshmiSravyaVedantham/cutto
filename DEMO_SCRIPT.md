# CutTo Demo Script (< 4 minutes)

## The Angle
Sravya runs a kids' YouTube channel. She needs educational videos regularly but can't afford animators, voiceover artists, or video editors. CutTo lets her go from lesson idea to finished animated video in one conversation.

---

## 0:00-0:20 — Problem Statement
"I run a kids' educational YouTube channel. Every video needs animations, voiceover, and editing — which means expensive software and hours of work. Most teachers and content creators with great lesson ideas never make their video because the barrier is too high."

*Show: split screen of complex video editing software vs CutTo's simple chat interface*

## 0:20-0:40 — Solution
"CutTo is an AI Video Director. I describe a lesson — how the heart works, why volcanoes erupt, a story about the solar system — and CutTo writes the script, generates animated visuals with Veo, adds voiceover with lipsync, and delivers a finished video I can upload directly."

*Show: CutTo landing page with kids' education focus, click "Start Creating"*

## 0:40-2:30 — Live Demo

1. **Voice input** (0:40-1:00): Click the mic button, speak: "Create an animated explainer for 8-year-olds about how volcanoes erupt. Show the layers of the earth, magma rising, and a big eruption. Make it exciting but educational."
   - Show the voice waveform overlay
   - Show the AI responding with creative excitement: "I'm seeing this as a cinematic journey INTO the earth..."

2. **Interleaved preview images** (1:00-1:20): As Gemini generates the scene plan, preview images appear inline in the conversation
   - Point out: "These preview images generate right in the conversation — I can see what the AI is thinking before committing"
   - This is the Creative Storyteller mandatory requirement

3. **Scene plan editor** (1:20-1:50):
   - Show the scene plan with speaker badges (Narrator, Character 1)
   - Edit a scene's narration to make it more kid-friendly
   - Reorder scenes with arrow buttons
   - Delete a scene — show the **undo toast** ("Scene deleted — Undo") then undo it
   - Show estimated duration
   - Type in revision box: "make the eruption scene more dramatic and exciting for kids"
   - Show the AI revising the plan

4. **Generate** (1:50-2:10): Click "Looks great — Make my video!"
   - Show real-time progress: each scene animating in parallel batches
   - Point out thumbnails appearing as scenes complete
   - If a scene fails, show graceful error handling (pipeline continues)

5. **Final video** (2:10-2:30): Video plays automatically
   - Point out: narration voice matched to educational tone, background music, scene transitions
   - "This is ready to upload to my YouTube channel right now"
   - Click Download

## 2:30-3:00 — Architecture (brief)
*Flash the architecture diagram*

"Under the hood: Gemini 2.5 Flash drives the creative conversation with interleaved text and image output. A multi-agent ADK architecture routes between a Creative Director and Storyboard Artist agent. Veo 2.0 generates animated clips, Cloud TTS creates the voiceover, Wav2Lip adds lipsync on character close-ups, and FFmpeg assembles everything with mood-matched music."

## 3:00-3:20 — Quick-Start Templates
"CutTo also comes with quick-start templates for common kids' topics."

*Click through 1-2 quick starts:*
- "How the heart pumps blood" (medical explainer for kids)
- "Solar system adventure" (animated story)

"Six video categories work out of the box: animated stories, science explainers, documentaries, tutorials, marketing videos, and motivational pieces."

## 3:20-3:40 — Key Features Callout
- "Voice input — press V anywhere or click the mic to speak naturally"
- "Reference image upload — match a visual style from a mood board or textbook"
- "Interactive scene editor — reorder, edit, delete with undo, ask AI for revisions"
- "Graceful error handling — retry on video playback failure, connection recovery with reconnect banner"
- "113 automated tests covering the full pipeline"

## 3:40-3:55 — Wrap
"Every existing tool makes you the editor. CutTo makes you the director. Describe any lesson, any story — and your video is ready to teach."

*Show: landing page tagline "AI Video Director for Kids' Education"*

---

## Tips for Recording
- Use OBS or QuickTime at 1080p+
- Pick the volcano explainer — visually dramatic, clearly educational
- Pre-test the full flow before recording (generate at least once)
- One continuous take shows confidence
- Upload to YouTube (unlisted is fine) and add link to Devpost
- Record voice clearly — demo audio quality matters for judges
