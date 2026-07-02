import re
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("CoastalAlpineCore.Security")


@dataclass
class SecurityResult:
    """Rich result for security checks to support audit logging and flywheel training."""
    is_safe: bool
    reason: str = ""
    matched_pattern: Optional[str] = None
    severity: str = "low"  # low, medium, high


class SecurityGuard:
    """
    Configurable security guard for prompt injection, file access, and tenant isolation.
    Returns structured SecurityResult for better observability and future ML training (flywheel).
    """

    DEFAULT_PATTERNS: List[str] = [
        r"(?i)\bignore previous instructions\b",
        r"(?i)\bsystem prompt\b",
        r"(?i)\bdelete from\b",
        r"(?i)\bdrop table\b",
        r"(?i)union select",
        r"etc/passwd",
        r"C:\\Windows\\system32",
        r"(?i)\bformat c:\b",
        r"(?i)\brm -rf\b",
    ]

    def __init__(self, custom_patterns: Optional[List[str]] = None):
        self.patterns = custom_patterns or self.DEFAULT_PATTERNS

    def check_prompt(self, prompt: str) -> SecurityResult:
        """
        Scans prompt for injection and dangerous patterns.
        Returns structured result instead of simple bool.
        """
        for pattern in self.patterns:
            if re.search(pattern, prompt):
                logger.warning(f"Security Alert: Malicious pattern detected: {pattern}")
                return SecurityResult(
                    is_safe=False,
                    reason="Matched dangerous pattern",
                    matched_pattern=pattern,
                    severity="high",
                )
        return SecurityResult(is_safe=True, reason="Prompt passed basic checks")


def input_guard_check(prompt: str) -> bool:
    """
    Backward-compatible simple boolean check (uses SecurityGuard internally).
    """
    guard = SecurityGuard()
    result = guard.check_prompt(prompt)
    return result.is_safe


def tenant_isolated_query(query_tenant_id: str, active_tenant_id: str) -> bool:
    """
    Enforces strict tenant scoping to prevent cross-contamination.
    Logs violation for audit and potential flywheel data.
    """
    if query_tenant_id != active_tenant_id:
        logger.error(
            f"SECURITY VIOLATION: Tenant context mismatch! "
            f"Query={query_tenant_id} vs Session={active_tenant_id}"
        )
        return False
    return True
