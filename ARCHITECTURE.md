# Architecture — coastal-alpine-core

## Overview

`coastal-alpine-core` is the shared foundation library for the Coastal Alpine Tech ecosystem. It provides reusable components for:

- Secure local LLM inference (Ollama wrapper with resilience)
- Prompt security and input guarding
- Hardware telemetry for edge devices (Raspberry Pi 5 + Hailo NPU)
- Unified portal framework used by AquaGuard, SoilGuard, and Blue-Moon

## Design Principles

- **Single source of truth**: All shared logic lives here. Portals should not duplicate core functionality.
- **Versioned releases**: Portals must pin to tagged releases (`@v0.3.0`), never `@main`.
- **Backward compatibility**: Changes to `portal_core` should maintain support for legacy keyword arguments where possible.
- **Security first**: Input validation and prompt guarding are mandatory for any AI-related code.

## Package Structure
- `src/coastal_alpine_core/portal_core/` — Shared portal logic (config, capture, MQTT, hardware control, pruning, AI agent, compliance)
- `src/coastal_alpine_core/` — Core security, telemetry, and Ollama client

## Versioning & Releases
- Semantic versioning via `pyproject.toml`
- Automated releases triggered on push to `main`
- Portals must pin to tagged versions (e.g. `@v0.3.0`), never `@main`

## Dependency Policy
All downstream portals should depend on tagged releases of this package only.
