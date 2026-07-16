"""
Coastal Alpine Portal Core Module

The engine room for autonomous portals.
Orchestrates multi-modal data ingestion, LLM reasoning, and hardware enforcement.
"""

__version__ = "0.2.1"
__author__ = "Coastal Alpine Tech Limited"

import sys as _sys

from .ai_agent import AIAgent, OptimizationPlan
from .av_capture import AVCapture
from .config import AquaGuardConfig, SoilGuardConfig, load_aquaguard_config, load_soilguard_config
from .config import PortalConfig as BlueMoonConfig
from .config import load_config as load_bluemoon_config
from .hardware_control import ActionState, HardwareController, ValveAction
from .media_pruner import MediaPruner
from .mqtt_client import MQTTClient

# Portals originally shipped their own top-level `portal_core` package and
# their tests still patch e.g. "portal_core.av_capture.cv2". Alias this
# package (and each submodule, so patches hit the SAME module objects).
_sys.modules.setdefault("portal_core", _sys.modules[__name__])
for _sub in ("ai_agent", "av_capture", "config", "hardware_control", "media_pruner", "mqtt_client"):
 _sys.modules.setdefault(f"portal_core.{_sub}", _sys.modules[f"{__name__}.{_sub}"])

__all__ = [
 "AIAgent",
 "OptimizationPlan",
 "MQTTClient",
 "AVCapture",
 "MediaPruner",
 "HardwareController",
 "ActionState",
 "ValveAction",
 "load_aquaguard_config",
 "load_soilguard_config",
 "load_bluemoon_config",
 "AquaGuardConfig",
 "SoilGuardConfig",
 "BlueMoonConfig",
]
