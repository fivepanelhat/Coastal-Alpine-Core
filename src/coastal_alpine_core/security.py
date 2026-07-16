"""Prompt injection guards, tenant isolation, and device posture checks."""

from __future__ import annotations

import hmac
import logging
import math
import re
import unicodedata
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger("CoastalAlpineCore.Security")

# Prompts beyond this size are rejected outright: oversized inputs are a
# memory/latency DoS vector on 16GB-class edge nodes before they are a
# legitimate query.
MAX_PROMPT_CHARS = 32_000

# Zero-width and BOM characters used to split trigger words past regex
# filters (e.g. "ig<ZWSP>nore previous instructions").
_ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")


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
        if len(text) > MAX_PROMPT_CHARS:
            logger.warning(
                "Security Alert: oversized prompt rejected (%d chars > %d limit)",
                len(text),
                MAX_PROMPT_CHARS,
            )
            return SecurityResult(
                is_safe=False,
                reason=f"Prompt exceeds {MAX_PROMPT_CHARS} character limit",
                severity="medium",
            )
        # Strip obfuscation layers before matching: NFKC folds fullwidth /
        # compatibility glyphs, and zero-width characters are deleted so
        # "ig<ZWSP>nore" cannot slip past word-boundary patterns.
        text = _ZERO_WIDTH_RE.sub("", unicodedata.normalize("NFKC", text))
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

    Fail-closed: missing, empty, or non-string tenant identifiers are treated
    as violations — two absent tenant contexts must never "match".
    """
    if not isinstance(query_tenant_id, str) or not isinstance(active_tenant_id, str):
        logger.error("SECURITY VIOLATION: non-string tenant identifier rejected")
        return False
    if not query_tenant_id or not active_tenant_id:
        logger.error("SECURITY VIOLATION: empty tenant identifier rejected")
        return False
    if query_tenant_id != active_tenant_id:
        logger.error(
            "SECURITY VIOLATION: Tenant context mismatch! Query=%s vs Session=%s",
            query_tenant_id,
            active_tenant_id,
        )
        return False
    return True


# Well-known insecure digests that must never be accepted as production baselines.
# (SHA-256 of empty string; SHA-256 of "Hello World" — common scaffolding placeholders.)
_PLACEHOLDER_FIRMWARE_DIGESTS = frozenset(
    {
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "7f83b1657ff1fc53b92c48da1bf5553d684d054611ba4f1f4d9240d8bf1b3a1a",
    }
)

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# Registered cryptographic baselines for authorized edge hardware profiles.
# Empty by default: production fleets must register real digests via
# register_firmware_baseline() or CAT_FIRMWARE_HASHES_JSON. Fail-closed.
VALID_FIRMWARE_HASHES: dict[str, str] = {}


def _is_placeholder_digest(digest: str) -> bool:
    return digest.lower() in _PLACEHOLDER_FIRMWARE_DIGESTS


def _is_valid_sha256_hex(digest: str) -> bool:
    return bool(isinstance(digest, str) and _SHA256_HEX_RE.fullmatch(digest.lower()))


def register_firmware_baseline(device_type: str, firmware_hash: str) -> None:
    """Register an authorized firmware digest for a device profile.

    Rejects non-SHA-256 hex strings and known placeholder digests so scaffolding
    hashes can never become a production trust root.
    """
    if not isinstance(device_type, str) or not device_type.strip():
        raise ValueError("device_type must be a non-empty string")
    if not _is_valid_sha256_hex(firmware_hash):
        raise ValueError("firmware_hash must be a 64-char lowercase hex SHA-256 digest")
    normalized = firmware_hash.lower()
    if _is_placeholder_digest(normalized):
        raise ValueError(
            "firmware_hash is a known placeholder digest and cannot be registered "
            "(empty-string or Hello-World SHA-256)"
        )
    VALID_FIRMWARE_HASHES[device_type] = normalized


def clear_firmware_baselines() -> None:
    """Clear all registered firmware baselines (tests / reconfiguration)."""
    VALID_FIRMWARE_HASHES.clear()

# In-memory rolling telemetry cache (sliding window per device)
HISTORY_WINDOW: dict[str, deque[float]] = {}
HISTORY_MAXLEN = 50

# Cap on distinct device histories: an attacker cycling spoofed device_ids
# must not be able to grow this dict without bound (memory DoS). Oldest
# entries are evicted FIFO once the cap is hit.
MAX_TRACKED_DEVICES = 1024


def device_posture_check(device_id, payload):
    """
    Continuous device posture verification and Z-score telemetry anomaly detection.
    """
    try:
        if not isinstance(payload, dict):
            logger.warning("[SECOPS ANOMALY] Non-dict payload from %s rejected.", device_id)
            return False, "MALFORMED_PAYLOAD"

        posture = payload.get("posture", {})
        telemetry = payload.get("telemetry", {})
        if not isinstance(posture, dict) or not isinstance(telemetry, dict):
            logger.warning("[SECOPS ANOMALY] Malformed sub-structures from %s.", device_id)
            return False, "MALFORMED_PAYLOAD"

        # Constant-time comparison: the firmware digest check must not leak
        # match-prefix length via timing. Placeholder digests fail closed even
        # if somehow present in VALID_FIRMWARE_HASHES.
        expected_hash = VALID_FIRMWARE_HASHES.get(payload.get("device_type"))
        presented_hash = posture.get("firmware_hash")
        if (
            not expected_hash
            or not isinstance(presented_hash, str)
            or not _is_valid_sha256_hex(expected_hash)
            or _is_placeholder_digest(expected_hash)
            or not hmac.compare_digest(presented_hash.lower(), expected_hash.lower())
        ):
            reason = "INVALID_POSTURE_HASH"
            if expected_hash and _is_placeholder_digest(expected_hash):
                reason = "PLACEHOLDER_FIRMWARE_BASELINE"
            logger.warning(
                "[SECOPS ANOMALY] Posture validation failed for %s — rogue firmware? (%s)",
                device_id,
                reason,
            )
            return False, reason

        if "sec_daemon" not in posture.get("running_processes", []):
            logger.warning(
                "[SECOPS ANOMALY] Device %s degraded security posture (sec_daemon missing).",
                device_id,
            )
            return False, "MUTATED_PROCESS_STATE"

        current_val = float(telemetry.get("value", 0))
        # NaN/inf poisoning defense: one NaN in the window turns every later
        # mean/std into NaN, silently disabling the Z-score detector.
        if not math.isfinite(current_val):
            logger.warning(
                "[SECOPS ANOMALY] Non-finite telemetry value from %s rejected.", device_id
            )
            return False, "TELEMETRY_OUTLIER"

        if device_id not in HISTORY_WINDOW:
            if len(HISTORY_WINDOW) >= MAX_TRACKED_DEVICES:
                evicted = next(iter(HISTORY_WINDOW))
                HISTORY_WINDOW.pop(evicted, None)
                logger.warning(
                    "[SECOPS] Device history cap reached; evicted oldest entry %s.",
                    evicted,
                )
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
