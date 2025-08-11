# Voice UX flows

States: Idle → Listening → Thinking → Speaking
- Idle: wake-word armed (“Pappu”); VAD passive
- Listening: capture speech via Web Speech API; stop on silence or tap
- Thinking: show spinner; allow cancel
- Speaking: TTS output; allow barge-in to interrupt

Edge cases
- Microphone permission denied → fallback to manual mic button
- Wake-word false triggers → adjust sensitivity; visual confirmation step
