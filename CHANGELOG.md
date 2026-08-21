# Changelog


## Hybrid platform update (July 2026)

- Dual-platform installers: `install.sh` (Linux/macOS) and `install.ps1` (Windows)
- Mermaid system maps updated for hybridisation (Core · Weaver · Aether · stack) and Windows + Linux hosts
- Architecture overview images refreshed for hybrid stack + dual OS targets
- Developer setup / installation docs cover Windows and Linux prerequisites and packages

All notable changes to the shared `coastal_alpine_core` package will be documented in this file.

## [0.5.10] - 2026-08-21

### Added (Sprint E)
- **ConfigOverlay** (`config_overlay.py`): stacked defaults → profile → tenant → session merge; secret-like keys rejected
- **EffectJournal** (`effects.py`): reversible tool/skill effects with LIFO undo + optional JSONL audit
- **Skill dependency graph** (`skill_graph.py`): `depends_on` topological load order; cycle/missing-dep detection
- **CodeModeRunner** (`code_mode.py`): sandboxed PTC / code-mode execution (`tools.<name>(**kwargs)` only; no imports)

## [0.5.9] - 2026-08-21

### Added
- `record_session_trajectory` bridge (SessionEvent outcomes → DataFlywheel Trajectory)

## [0.5.8] - 2026-08-21

### Added
- LLMProvider Protocol, ProviderProfile, get_provider / get_profile registry

## [0.5.7] - 2026-08-21

### Added
- **SessionEvent / SessionEventStore** (`session_events.py`): append-only, tenant-aware event stream for Weaver and Aether agent turns (Sprint A Phase 1). Complements DataFlywheel Trajectory with finer-grained HITL-ready events, list-by-session, and resume-from-event-id. CAT stamp: local-first JSONL, edge-safe rotation, no secrets in payloads.

## [0.5.6] - 2026-07-16

### Security
- Firmware trust roots are **empty by default** and **fail-closed**.
- Removed known placeholder digests (empty-string SHA-256 and "Hello World" SHA-256) from `VALID_FIRMWARE_HASHES`.
- Added `register_firmware_baseline()` / `clear_firmware_baselines()`; registration rejects non-SHA-256 and placeholder digests.
- `device_posture_check` rejects placeholder baselines even if they appear in the map (`PLACEHOLDER_FIRMWARE_BASELINE`).
- Added `REALITY.md` honesty checklist for pre-seed positioning.

## [0.5.5] - 2026-07-13

### Security (Python)
- `SecurityGuard`: NFKC + zero-width-character normalization before pattern matching.
- `tenant_isolated_query`: empty or non-string tenant IDs now rejected.
- Package hardening suite expanded.

## [0.5.4] - 2026-07-11

### Security
- Expanded `SecurityGuard` default patterns.

## [0.5.3] - 2026-07-11

### Changed / optimised (edge SDK)
- Edge Ollama client, SecurityGuard, DataFlywheel, TelemetryTracker improvements.

## [1.0.0] - 2026-06-07

### Added
- Initialized core structure and Python module.
