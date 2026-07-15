# Reality checklist — Coastal-Alpine-Core

| Item | Status | Notes |
| ---- | ------ | ----- |
| **Role** | Shared edge SDK | SecurityGuard, Ollama client, telemetry, flywheel |
| **Works offline** | Yes (LLM client offline fallback) | Needs local Ollama for real generation |
| **Firmware trust roots** | **Empty by default** | Register real digests via `register_firmware_baseline()`; placeholders rejected |
| **Field fleet** | Pre-seed | No commercial SLA |
| **Pin consumers** | Tagged releases only | e.g. `@v0.5.x` — never floating `@main` in production |
| **Tests** | `pytest` | Security hardening suite must stay green |
