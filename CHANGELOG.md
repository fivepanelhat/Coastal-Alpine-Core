# Changelog


## Hybrid platform update (July 2026)

- Dual-platform installers: `install.sh` (Linux/macOS) and `install.ps1` (Windows)
- Mermaid system maps updated for hybridisation (Core · Weaver · Aether · stack) and Windows + Linux hosts
- Architecture overview images refreshed for hybrid stack + dual OS targets
- Developer setup / installation docs cover Windows and Linux prerequisites and packages

All notable changes to the shared `coastal_alpine_core` package will be documented in this file.

## [0.5.5] - 2026-07-13

### Security (Python)
- `SecurityGuard`: NFKC + zero-width-character normalization before pattern matching — defeats obfuscated injections like `ig<ZWSP>nore previous instructions` and fullwidth-glyph variants; oversized prompts (>32k chars) rejected fail-closed.
- `tenant_isolated_query`: empty or non-string tenant IDs now rejected — two absent tenant contexts previously "matched" (fail-open).
- `device_posture_check`: constant-time firmware hash comparison (`hmac.compare_digest`); non-finite telemetry rejected (a single NaN previously poisoned the window and silently disabled Z-score anomaly detection); device history bounded at 1024 ids with FIFO eviction (memory DoS); malformed/non-dict payloads fail closed.
- `SovereignOllamaClient`: host restricted to http(s) URLs; 100k-char prompt cap before network; malformed JSON in a 200 response counts as a retry instead of crashing the caller.
- `log_performance`: measurements closed when the wrapped function raises.

### Security (JS, npm 1.3.0)
- `attestation_validator.js`: strict hex validation on nonce/quote/signature/PCR inputs — closes a replay-check bypass where an empty or non-hex nonce produced an empty buffer that any quote "contains"; constant-time PCR digest comparison (`crypto.timingSafeEqual`); 16-byte nonce entropy floor; expected baseline no longer echoed to logs; golden digest overridable via `CAT_GOLDEN_PCR_DIGEST`.
- `secure_store.js`: rejects `DB_CIPHER_KEY` values containing quotes/backslashes/control characters (PRAGMA string-literal injection); KDF work factor raised 64,000 → 256,000 (SQLCipher 4 default); DB path overridable via `SOVEREIGN_DB_PATH`; no filesystem side effects at `require()` time.
- `behavioral_analytics.js`: prototype-pollution-safe `Map` history (a `"__proto__"` nodeId previously returned `Object.prototype` as mutable stats); bounded history (1024 nodes, FIFO eviction); strict nodeId/commandType validation, fail-closed.
- `validation.js`: nodeId constrained to `[A-Za-z0-9._-]{1,64}` (log-injection / oversized-identifier defense).

### Added
- `tests/test_security_hardening.py` — pytest regression suite pinning every fail-closed path.
- `tests/attestation_hardening.test.js` — `node --test` suite for the attestation validator (`npm test`).

## [0.5.4] - 2026-07-11

### Security
- Expanded `SecurityGuard` default patterns: jailbreak/exfiltration, SSRF metadata endpoints, credential harvesting, pipe-to-shell, PowerShell `-enc`, and broader SQL destruction lures.
- Documented Dependabot / Code Scanning response process in `SECURITY.md`.

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
