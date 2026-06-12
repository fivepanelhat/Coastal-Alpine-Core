import re
import logging

logger = logging.getLogger("CoastalAlpineCore.Security")


def input_guard_check(prompt: str) -> bool:
    """
    Scans incoming prompts for potential prompt injections, local file access attempts,
    or common SQL injection patterns.
    Returns:
        True if the prompt is safe.
        False if the prompt is blocked.
    """
    # Block common injection commands
    injection_patterns = [
        r"(?i)\bignore previous instructions\b",
        r"(?i)\bsystem prompt\b",
        r"(?i)\bdelete from\b",
        r"(?i)\bdrop table\b",
        r"(?i)union select",
        r"etc/passwd",
        r"C:\\Windows\\system32",
        r"(?i)\bformat c:\b",
    ]

    for pattern in injection_patterns:
        if re.search(pattern, prompt):
            logger.warning(
                f"Security Alert: Malicious prompt pattern detected: '{pattern}'"
            )
            return False

    return True


def tenant_isolated_query(query_tenant_id: str, active_tenant_id: str) -> bool:
    """
    Enforces strict tenant scoping checks at the service layer to prevent tenant cross-contamination.
    Returns:
        True if the tenant ID matches the session tenant ID.
        False if there is a tenant mismatch.
    """
    if query_tenant_id != active_tenant_id:
        logger.error(
            f"SECURITY VIOLATION: Tenant context mismatch! "
            f"Query tenant_id ({query_tenant_id}) does not match Session tenant_id ({active_tenant_id})."
        )
        return False
    return True
