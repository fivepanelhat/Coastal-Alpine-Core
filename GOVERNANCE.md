# Governance — CAT Architectural Standards

This repository is governed by the **Coastal Alpine Tech (CAT) Architectural
Standards** maturity model (Gold / Diamond / Platinum). The canonical decision
skill lives in the [Aether](https://github.com/fivepanelhat/Aether) repo at
`skills/cat-architectural-standards/SKILL.md`.

## Tier classification

| Tier | Role | Applies to Coastal-Alpine-Core as |
| :--- | :--- | :--- |
| **Diamond** *(primary)* | Enterprise-grade foundation | The shared edge SDK every portal depends on — `SecurityGuard`, offline Ollama client with retries/backoff, hardware telemetry, mTLS MQTT. Reliability and security are the product. |
| **Platinum** *(secondary)* | Intelligent self-improving system | Structured `SecurityResult` and telemetry feed the data flywheel for continuous local improvement. |
| **Gold** *(secondary)* | Workflow-native design | Portal framework mirrors the sense → guard → infer → actuate field workflow. |

## Operating rules

- **Classify before building.** Declare the primary (and any secondary) tier in
  each PR/ADR. As a foundational SDK, most changes here are **Diamond** and must
  preserve backward compatibility for downstream portals.
- **HITL gates are non-negotiable:** changes to `SecurityGuard` patterns, crypto,
  telemetry, MQTT/device posture, classification, or any tier-compliance release
  claim require human approval.
- **Sovereignty overlay applies to all tiers.** Te Tiriti o Waitangi and Te Mana
  Raraunga principles are architectural requirements — local processing on
  RPi 5 16GB + Hailo-10H, no silent cloud exfiltration.

## References

- Aether: `skills/cat-architectural-standards/SKILL.md` — decision protocol
- `SECURITY.md`, `ARCHITECTURE.md` — Diamond/sovereignty detail
