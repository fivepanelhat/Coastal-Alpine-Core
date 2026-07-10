"""Prompt injection guards, tenant isolation, and device posture checks."""

from __future__ import annotations

import logging
import math
import re
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger("CoastalAlpineCore.Security")


@dataclass
class SecurityResult:
    """Rich result for security checks to support audit logging and flywheel training."""

    is_safe: bool
    reason: str = ""
    matched_pattern: str | None = None
    severity: str = "low"  # low, medium, high


class SecurityGuard:
    """
    Configurable security guard for prompt injection, file access, and tenant isolation.
    Returns structured SecurityResult for better observability and future ML training.
    """

    DEFAULT_PATTERNS: list[str] = [
        # Prompt injection / jailbreak
        r"(?i)\bignore previous instructions\b",
        r"(?i)\bignore (all|any) (previous|prior|above) (instructions|rules|prompts)\b",
        r"(?i)\bdisregard (your|the) (system|developer) (prompt|message|instructions)\b",
        r"(?i)\byou are now\b.*\b(unrestricted|jailbroken|DAN)\b",
        r"(?i)\bsystem prompt\b",
        r"(?i)\bdeveloper message\b",
        r"(?i)\bexfiltrat(e|ion)\b",
        # SQL / data destruction
        r"(?i)\bdelete from\b",
        r"(?i)\bdrop table\b",
        r"(?i)\btruncate table\b",
        r"(?i)union(\s+all)?\s+select",
        r"(?i)\binto outfile\b",
        # Path / OS command injection
        r"etc/passwd",
        r"C:\\Windows\\system32",
        r"(?i)\bformat c:\b",
        r"(?i)\brm\s+-rf\b",
        r"(?i)\bcurl\s+[^\n]*\|\s*(ba)?sh\b",
        r"(?i)\bwget\s+[^\n]*\|\s*(ba)?sh\b",
        r"(?i)\bpowershell\s+(-enc|-encodedcommand)\b",
        # SSRF / remote code lure
        r"(?i)\bfile:///",
        r"(?i)\bmetadata\.google\.internal\b",
        r"(?i)\b169\.254\.169\.254\b",
        # Credential harvesting
        r"(?i)\bBEGIN (RSA |OPENSSH |EC )?PRIVATE KEY\b",
        r"(?i)\baws_secret_access_key\b",
    ]

    def __init__(self, custom_patterns: list[str] | None = None):
        patterns = custom_patterns or self.DEFAULT_PATTERNS
        # Compile once — check_prompt is on the hot path for every LLM call
        self._compiled: list[re.Pattern[str]] = [
            re.compile(p) if isinstance(p, str) else p for p in patterns
        ]
        self.patterns = patterns  # keep original for introspection

    def check_prompt(self, prompt: str) -> SecurityResult:
        """
        Scans prompt for injection and dangerous patterns.
        Returns structured result instead of simple bool.
        """
        text = prompt if isinstance(prompt, str) else str(prompt)
        for compiled in self._compiled:
            if compiled.search(text):
                logger.warning(
                    "Security Alert: Malicious pattern detected: %s", compiled.pattern
                )
                return SecurityResult(
                    is_safe=False,
                    reason="Matched dangerous pattern",
                    matched_pattern=compiled.pattern,
                    severity="high",
                )
        return SecurityResult(is_safe=True, reason="Prompt passed basic checks")


# Module-level guard reused by input_guard_check (avoids recompile every call)
_DEFAULT_GUARD = SecurityGuard()


def input_guard_check(prompt: str) -> bool:
    """
    Backward-compatible simple boolean check (uses SecurityGuard internally).
    """
    return _DEFAULT_GUARD.check_prompt(prompt).is_safe


def tenant_isolated_query(query_tenant_id: str, active_tenant_id: str) -> bool:
    """
    Enforces strict tenant scoping to prevent cross-contamination.
    Logs violation for audit and potential flywheel data.
    """
    if query_tenant_id != active_tenant_id:
        logger.error(
            "SECURITY VIOLATION: Tenant context mismatch! Query=%s vs Session=%s",
            query_tenant_id,
            active_tenant_id,
        )
        return False
    return True


# Registered cryptographic baselines for authorized edge hardware profiles
VALID_FIRMWARE_HASHES = {
    "ESP32_MANAKAI_SOIL": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # pragma: allowlist secret
    "PI5_STING_VISION": "7f83b1657ff1fc53b92c48da1bf5553d684d054611ba4f1f4d9240d8bf1b3a1a",  # pragma: allowlist secret
}

# In-memory rolling telemetry cache (sliding window per device)
HISTORY_WINDOW: dict[str, deque[float]] = {}
HISTORY_MAXLEN = 50


def device_posture_check(device_id, payload):
    """
    Continuous device posture verification and Z-score telemetry anomaly detection.
    """
    try:
        posture = payload.get("posture", {})
        telemetry = payload.get("telemetry", {})

        expected_hash = VALID_FIRMWARE_HASHES.get(payload.get("device_type"))
        if not expected_hash or posture.get("firmware_hash") != expected_hash:
            logger.warning(
                "[SECOPS ANOMALY] Posture validation failed for %s — rogue firmware?",
                device_id,
            )
            return False, "INVALID_POSTURE_HASH"

        if "sec_daemon" not in posture.get("running_processes", []):
            logger.warning(
                "[SECOPS ANOMALY] Device %s degraded security posture (sec_daemon missing).",
                device_id,
            )
            return False, "MUTATED_PROCESS_STATE"

        current_val = float(telemetry.get("value", 0))
        if device_id not in HISTORY_WINDOW:
            HISTORY_WINDOW[device_id] = deque(maxlen=HISTORY_MAXLEN)

        history = HISTORY_WINDOW[device_id]

        if len(history) > 10:
            mean = sum(history) / len(history)
            variance = sum((x - mean) ** 2 for x in history) / len(history)
            std_dev = math.sqrt(variance)

            if std_dev > 0.5:
                z_score = abs(current_val - mean) / std_dev
                if z_score > 3.5:
                    logger.warning(
                        "[ALERT] Statistical anomaly on %s. Value: %s (Z-Score: %.2f)",
                        device_id,
                        current_val,
                        z_score,
                    )
                    return False, "TELEMETRY_OUTLIER"

        history.append(current_val)
        return True, "VERIFIED"

    except Exception as e:
        logger.error("Device posture check failed for %s: %s", device_id, e)
        return False, "PROCESSING_FAULT"
