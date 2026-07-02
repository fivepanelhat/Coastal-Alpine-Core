"""
Coastal Alpine Portal Core Module

The engine room for autonomous portals.
Orchestrates multi-modal data ingestion, LLM reasoning, and hardware enforcement.
"""

__version__ = "0.2.0"
__author__ = "Coastal Alpine Tech Limited"

from .ai_agent import AIAgent, OptimizationPlan
from .mqtt_client import MQTTClient
from .av_capture import AVCapture
from .media_pruner import MediaPruner
from .hardware_control import HardwareController, ActionState, ValveAction
from .config import (
    load_aquaguard_config,
    load_soilguard_config,
    load_config as load_bluemoon_config,
    AquaGuardConfig,
    SoilGuardConfig,
    PortalConfig as BlueMoonConfig
)

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
