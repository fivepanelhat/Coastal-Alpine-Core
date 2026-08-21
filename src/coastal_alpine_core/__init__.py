"""
coastal-alpine-core: Shared utilities for Taranaki-based Coastal Alpine Tech Edge systems.
"""

from .code_mode import CodeModeResult, CodeModeRunner
from .config_overlay import ConfigOverlay
from .effects import EffectJournal, EffectRecord
from .ollama_client import SovereignOllamaClient
from .providers import (
    LLMProvider,
    ProviderProfile,
    get_profile,
    get_provider,
    list_providers,
    provider_from_profile,
    register_provider,
)
from .security import (
    SecurityGuard,
    SecurityResult,
    clear_firmware_baselines,
    device_posture_check,
    input_guard_check,
    register_firmware_baseline,
    tenant_isolated_query,
)
from .session_events import (
    EVENT_TYPES,
    SessionEvent,
    SessionEventStore,
    make_event,
)
from .session_flywheel import record_session_trajectory
from .skill_graph import SkillGraphError, resolve_skill_order, validate_skill_graph
from .telemetry import DataFlywheel, TelemetryTracker, Trajectory, log_performance

__version__ = "0.5.10"

__all__ = [
    "TelemetryTracker",
    "log_performance",
    "SovereignOllamaClient",
    "LLMProvider",
    "ProviderProfile",
    "get_provider",
    "get_profile",
    "provider_from_profile",
    "list_providers",
    "register_provider",
    "ConfigOverlay",
    "EffectJournal",
    "EffectRecord",
    "resolve_skill_order",
    "validate_skill_graph",
    "SkillGraphError",
    "CodeModeRunner",
    "CodeModeResult",
    "SecurityGuard",
    "SecurityResult",
    "input_guard_check",
    "device_posture_check",
    "register_firmware_baseline",
    "clear_firmware_baselines",
    "tenant_isolated_query",
    "DataFlywheel",
    "Trajectory",
    "record_session_trajectory",
    "SessionEvent",
    "SessionEventStore",
    "make_event",
    "EVENT_TYPES",
    "__version__",
]
