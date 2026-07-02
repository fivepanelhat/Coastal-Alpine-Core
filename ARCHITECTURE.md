# coastal-alpine-core Architecture

## Overview
`coastal-alpine-core` is the shared foundation for the Coastal Alpine Tech stack. It provides:
- Secure local LLM client (Ollama)
- Prompt security & input guarding
- Hardware telemetry for RPi 5 + Hailo
- Unified `portal_core` framework used by AquaGuard, SoilGuard, and Blue-Moon portals

## Package Structure
- `src/coastal_alpine_core/portal_core/` — Shared portal logic (config, capture, MQTT, hardware control, pruning, AI agent, compliance)
- `src/coastal_alpine_core/` — Core security, telemetry, and Ollama client

## Versioning & Releases
- Semantic versioning via `pyproject.toml`
- Automated releases triggered on push to `main`
- Portals must pin to tagged versions (e.g. `@v0.3.0`), never `@main`

## Dependency Policy
All downstream portals should depend on tagged releases of this package only.
