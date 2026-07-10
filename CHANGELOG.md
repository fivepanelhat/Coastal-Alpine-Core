# Changelog

All notable changes to the shared `coastal_alpine_core` package will be documented in this file.

## [0.5.3] - 2026-07-11

### Changed / optimised (edge SDK)
- `SovereignOllamaClient`: keep-alive session, edge default options, optional LRU response cache, `invoke`/`chat` aliases, configurable timeout.
- `SecurityGuard`: precompiled regex patterns; shared default guard for `input_guard_check`.
- `DataFlywheel`: automatic JSONL rotation; faster recent-read path for large files.
- `TelemetryTracker`: non-blocking `cpu_percent(interval=None)`.
- `MQTTClient`: bounded queue with drop-oldest backpressure.
- `AVCapture`: optional downscale + JPEG quality for Pi bandwidth.
- `AIAgent`: skip visual/audio LLM when capture is None; compact flywheel metadata.
- `HardwareController`: normalise `*_action` keys; `setup`/`cleanup` lifecycle hooks.
- Export `SecurityGuard` / `SecurityResult`; package version **0.5.3**.

## [1.2.0] - 2026-06-08

### Added
- Added Node.js `secure_store.js` using SQLCipher 256-bit AES database encryption at rest.
- Added Node.js `behavioral_analytics.js` for actuator timing and frequency control.
- Added Node.js `power_governor.js` for battery-aware duty cycle offsets.
- Added Python `analytics/input_guard.py` for device posture verification and Z-Score telemetry anomaly checks.
- Added Python `logging/compliance_guard.py` estimating carbon emission mitigation metrics and hash-chained audits.
- Created `dist/index.js` CommonJS entry point.

## [1.1.0] - 2026-06-07

### Added
- Added Node.js `attestation_validator.js` validating TPM 2.0 signatures against "Golden Boot" baseline registers.
- Added Node.js `validation.js` with telemetry clamps.

## [1.0.0] - 2026-06-07

### Added
- Initialized core structure and Python module.
- Added prompt sanitization and tenant scoping checks to `security.py`.
- Added Ollama connection wrapper to `models.py`.
- Added PMIC execution time metrics to `telemetry.py`.
