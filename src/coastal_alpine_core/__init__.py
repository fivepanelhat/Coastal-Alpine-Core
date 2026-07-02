"""
coastal-alpine-core: Shared utilities for Taranaki-based Coastal Alpine Tech Edge systems.
"""

from .ollama_client import SovereignOllamaClient
from .security import device_posture_check, input_guard_check, tenant_isolated_query
from .telemetry import DataFlywheel, TelemetryTracker, Trajectory, log_performance

__all__ = [
    "TelemetryTracker",
    "log_performance",
    "SovereignOllamaClient",
    "input_guard_check",
    "device_posture_check",
    "tenant_isolated_query",
    "DataFlywheel",
    "Trajectory",
]
