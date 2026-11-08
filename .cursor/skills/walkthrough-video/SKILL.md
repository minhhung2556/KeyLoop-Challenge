---
name: walkthrough-video
description: Build the Keyloop 5-10 minute walkthrough with English VieNeu TTS, live website screenshots, and FFmpeg.
disable-model-invocation: true
---

# Walkthrough video

```bash
python scripts/build_walkthrough_video.py
python scripts/verify.py --video
```

Stages: VieNeu-TTS-v3-Turbo (`Adam`) WAV -> screenshot cards + demo sequence -> FFmpeg mux `video/output/keyloop_walkthrough.mp4`.

Accent `#00B5D8`. Local GSAP and fonts only. Python 3.10 + `vieneu` (pyenv 3.10.11).
