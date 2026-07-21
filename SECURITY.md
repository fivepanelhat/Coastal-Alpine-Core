# Security Policy for Coastal-Alpine-Core

## CRITICAL INFRASTRUCTURE WARNING

This repository contains the shared architectural core, data models, and cryptographic utilities for the Coastal Alpine Tech Sovereign Stack.

**Blast radius:** A vulnerability in this repository propagates to all edge nodes, AI modules, and web portals.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.5.x   | Yes       |
| < 0.5   | Best-effort patches only |

## Vulnerability Disclosure

Do **not** open a public issue for security flaws in Core.

1. Report privately via GitHub Security Advisories on this repository, or to the Chief Architect.
2. Include: impact surface (edge / portal / multi-tenant), reproduction steps, and affected versions.
3. Core triage is **immediate**. Patches follow semantic versioning so edge nodes can pin safely.

## Security Notifications (how we track threats)

| Channel | What we watch | Response |
| ------- | ------------- | -------- |
| **Dependabot alerts** | Known CVEs in Python / Actions deps | Weekly PRs; critical within 48h |
| **Code scanning (CodeQL / Bandit)** | SAST findings on `main` | Fix-forward on `main` or security advisory |
| **Secret scanning (Gitleaks)** | Leaked credentials in history/PRs | Rotate + purge; block merge |
| **Red team workflow** | Prompt injection / adversarial suites | Expand `SecurityGuard` patterns |
| **Org security mail / advisories** | Supply-chain and NVD notices | Pin/floor versions in `requirements` + Core release |

## Active threat patches (2026-07)

| ID | Package / surface | Severity | Mitigation in this repo |
| -- | ----------------- | -------- | ----------------------- |
| GHSA-f4j7-r4q5-qw2c (CVE-2026-45829) | `chromadb` ≤1.5.9 pre-auth RCE | Critical | Not a Core direct dep; stack docs require **localhost-only** bind, no `trust_remote_code`, network policy. Monitor for fixed release. |
| GHSA-f4xh-w4cj-qxq8 | `langsmith` <0.8.18 file read | High | Floor `langsmith>=0.8.18` in consumers (Weaver / stack). |
| GHSA-4xgf-cpjx-pc3j | `pydantic-settings` <2.14.2 symlink escape | Medium | Floor `pydantic-settings>=2.14.2` in consumers. |
| CodeQL `actions/missing-workflow-permissions` | GITHUB_TOKEN scope | Warning | CI workflows set `permissions: contents: read` by default. |
| CodeQL `py/clear-text-storage-sensitive-data` | API keys on disk | Error | Tools must not write secrets; use env vars / operator-managed `.env`. |

## Built-in controls

- **`SecurityGuard` / `input_guard_check`** — precompiled prompt-injection, SSRF lure, SQL, and credential patterns (v0.5.4+).
- **`tenant_isolated_query`** — hard fail on tenant context mismatch.
- **`device_posture_check`** — firmware hash + telemetry Z-score anomalies.
- **SecOps CI** — Bandit SAST, Gitleaks, scheduled red-team.

## Quality gates

- Unit tests in `tests/test_core_sdk.py` (security + SDK contracts).
- Ruff lint on `src` / `tests`.
- Publish only from tagged releases (`v*.*.*`).

## Reporting SLA

| Severity | Acknowledge | Target fix / mitigation |
| -------- | ----------- | ----------------------- |
| Critical | 24h | 48h mitigation + version bump |
| High | 48h | 5 business days |
| Medium / Low | 5 business days | Next minor release |

## Fleet security principles

- **No silent exfiltration** of personal or tenant operational data
- Prefer **local-first** processing; third-party AI only with explicit operator configuration and UI/docs disclosure
- Report vulnerabilities via GitHub Security Advisories or the maintainer contact on the org profile
- High-stakes production changes require human approval (HITL)

## Data sales and third parties

- **We do not sell personal information or customer operational data to third parties.**
- Optional AI or cloud services run only when configured by the operator; processing must be disclosed (in-product and/or docs).
- Prefer local-first paths so third-party transfer is unnecessary by default.

## NZ Privacy Act and Te Mana Raraunga

- Design in accordance with the **Privacy Act 2020**.
- Operate in accordance with **Te Mana Raraunga** principles for Māori data sovereignty interests.
- Align AI features with **NZ AI safety** / responsible AI expectations (HITL, transparency, no silent training on private content).

