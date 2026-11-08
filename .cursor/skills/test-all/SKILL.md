---
name: test-all
description: Run backend pytest and frontend node:test plus typecheck via scripts/verify.py. Use when verifying regressions.
disable-model-invocation: true
---

# Test all

From repo root (PowerShell: `; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }`):

```bash
python scripts/verify.py --all
```

Backend only: `python scripts/verify.py --backend`
Frontend only: `python scripts/verify.py --frontend`

Report with `🧪` / `  ✅` / `  ❌` / `✅ Result: PASS`.
