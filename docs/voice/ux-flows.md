# Voice UX flows

States: Idle → Listening → Thinking → Speaking
- Idle: wake-word armed (“Pappu”); VAD passive
- Listening: capture speech via Web Speech API; stop on silence or tap
- Thinking: show spinner; allow cancel
- Speaking: TTS output; allow barge-in to interrupt

Edge cases
- Microphone permission denied → fallback to manual mic button
- Wake-word false triggers → adjust sensitivity; visual confirmation step

## Ask me (voice) — assessment flow

Scope: Voice-first practice for MCQ and short-answer. All audio stays on-device; only transcribed text is sent to the API.

Flow (per question)
- Speaking: System reads the question (and choices, for MCQ) using TTS.
- Listening: Start STT (Web Speech API), VAD-based stop on silence or user tap.
- Thinking: Send text to validator:
	- MCQ → POST /mcq/validate { questionId, selected: "A|B|C|D" }
	- Short answer → POST /answer/validate { question, userAnswer, subject, chapter }
- Speaking: Read back correctness, brief feedback, and 1–2 page anchors; show captions.

UI controls
- Mic button (toggle), waveform level meter, live captions (interim results), retry.
- Commands: “repeat”, “next”, “skip”, “option A/B/C/D”, “stop”.
- Barge-in: interrupt TTS to answer early.

STT/TTS
- STT: Browser Web Speech API (preferred); language configurable (e.g., en-IN). Fallback to manual text input where unsupported.
- TTS: SpeechSynthesis API; allow rate/pitch adjustment.
- Privacy: No audio uploads by default; only text sent to backend.

Validation and feedback
- MCQ: correctness + short explanation + citation snippet.
- Short answer: rubric score (correct/partial/incorrect), 2–3 feedback bullets, and citations; link to related Teach sections for gaps.

Latency targets (P50)
- STT final result: ≤ 1.5s after end-of-speech.
- API validation: ≤ 500ms typical.
- TTS start: ≤ 300ms.

Error handling
- No speech detected: prompt to retry or type.
- Low-confidence transcript: confirm (“Did you mean …?”) before submit.
- Background noise/VAD false stops: extend auto-timeout, show hint.

Accessibility
- Always-on captions and keyboard shortcuts; visual focus cues; screen-reader labels.

Implementation notes
- JS module voice layer: startListening(), stopListening(), onResult(cb), speak(text).
- Practice UI integrates voice layer; submits to /mcq/validate or /answer/validate.
- Config flags: enableVoice, language, sttTimeoutMs, vadSensitivity.
