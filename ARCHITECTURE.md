# coastal-alpine-core — Architecture

## Purpose
This package is the single shared foundation for Coastal Alpine Tech’s edge AI and portal systems. It contains reusable logic for security, telemetry, local LLM access, and the common portal framework used across AquaGuard, SoilGuard, and Blue-Moon.

## Key Rules
- All shared code must live in this repository.
- Portals must depend on **tagged releases only** (e.g. `v0.3.0`). Never pin to `main`.
- Changes to `portal_core/` affect multiple production systems — coordinate before modifying core interfaces.
- Version bumps and releases are managed through the automated GitHub Actions workflow.

## Current Structure
- `src/coastal_alpine_core/portal_core/` — Shared portal logic (config, capture, MQTT, hardware control, pruning, AI agent, compliance)
- `src/coastal_alpine_core/` — Core security, telemetry, and Ollama client

## Versioning & Releases
- Semantic versioning via `pyproject.toml`
- Automated releases triggered on pushed tags (e.g., `v0.4.0`)
- Portals must pin to tagged versions (e.g. `@v0.4.0`), never `@main`

## Dependency Policy
All downstream portals should depend on tagged releases of this package only.

## Release Process
1. Make changes and update version in `pyproject.toml`
2. Push changes to `main`
3. Tag the release and push the tag:
   ```bash
   git tag v0.4.0
   git push origin v0.4.0
   ```
4. GitHub Actions automatically builds and creates a release based on the pushed tag
5. Dependabot will open PRs in the portals to update the pin
5. Portal CI will verify against the new core version

## Local Development

```bash
# Recommended
uv sync
uv run pytest
ruff check .
ruff format .
```
