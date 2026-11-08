---
name: phase-runner
description: Execute the next pending step in docs/challenge/implementation-plan.md. Use when continuing Keyloop implementation.
disable-model-invocation: true
---

# Phase runner

1. Read `docs/challenge/implementation-plan.md`.
2. Take the first unchecked `[ ]` step.
3. Inspect target files. Edit 2 to 4 files.
4. Run `python scripts/verify.py --step <id>`.
5. Mark the step `[x]`.
