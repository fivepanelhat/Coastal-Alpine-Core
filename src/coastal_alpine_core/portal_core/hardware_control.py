import contextlib
import logging
from enum import Enum
from typing import Any

try:
 import RPi.GPIO as GPIO
except ImportError:
 GPIO = None

logger = logging.getLogger(__name__)


class ActionState(Enum):
 OFF = "off"
 LOW = "low"
 MEDIUM = "medium"
 HIGH = "high"


class ValveAction(Enum):
 CLOSED = "closed"
 OPEN = "open"


class HardwareController:
 """Unified Hardware Controller for Coastal Alpine Portals (AquaGuard, SoilGuard, BlueMoon)."""

 def __init__(self, config: Any = None, **kwargs):
 if config:
 self.config = config.hardware if hasattr(config, "hardware") else config
 self.enable_control = getattr(self.config, "enable_hardware_control", False)
 else:
 # Reconstruct config from kwargs for backward compatibility
 class DummyConfig:
 def __init__(self, **kw):
 for k, v in kw.items():
 setattr(self, k, v)

 self.config = DummyConfig(**kwargs)
 self.enable_control = not kwargs.get("simulation_mode", False)

 # Unified state tracking
 self.states: dict[str, Any] = {}
 self.pwms: dict[str, Any] = {}

 if self.enable_control and GPIO:
 GPIO.setmode(GPIO.BCM)
 GPIO.setwarnings(False)
 self._init_pins()
 else:
 logger.info(
 "Hardware control is disabled or RPi.GPIO is missing. Operating in SIMULATION mode."
 )

 def _init_pins(self):
 # Extract all possible pins from config
 pins = {
 "aerator": getattr(self.config, "aerator_gpio_pin", None),
 "pump": getattr(self.config, "pump_gpio_pin", None),
 "valve": getattr(self.config, "valve_gpio_pin", None),
 "irrigation": getattr(self.config, "irrigation_gpio_pin", None),
 "nutrient": getattr(self.config, "nutrient_gpio_pin", None),
 "fan": getattr(self.config, "fan_gpio_pin", None),
 "lighting": getattr(self.config, "lighting_gpio_pin", None),
 "alert": getattr(self.config, "alert_gpio_pin", None),
 }

 for name, pin in pins.items():
 if pin is not None:
 GPIO.setup(pin, GPIO.OUT)
 if name in ["aerator", "pump", "irrigation", "nutrient", "fan", "lighting"]:
 freq = getattr(self.config, f"{name}_pwm_frequency", 1000)
 self.pwms[name] = GPIO.PWM(pin, freq)
 self.pwms[name].start(0)

 async def set_pwm_device(self, device_name: str, state: ActionState) -> bool:
 duty_cycles = {
 ActionState.OFF: 0,
 ActionState.LOW: 33,
 ActionState.MEDIUM: 66,
 ActionState.HIGH: 100,
 }
 dc = duty_cycles.get(state, 0)
 self.states[device_name] = {"state": state, "duty_cycle": dc}

 if not self.enable_control or not GPIO:
 logger.info(f"[SIM] {device_name.capitalize()} state -> {state.value} (PWM {dc}%)")
 return True

 try:
 if device_name in self.pwms:
 self.pwms[device_name].ChangeDutyCycle(dc)
 logger.info(f"{device_name.capitalize()} state -> {state.value} (PWM {dc}%)")
 return True
 except Exception as e:
 logger.error(f"Error setting {device_name} output: {e}")
 return False

 async def set_gpio_device(self, device_name: str, state: ValveAction) -> bool:
 val = 1 if state == ValveAction.OPEN else 0
 self.states[device_name] = {"state": state, "value": val}

 if not self.enable_control or not GPIO:
 logger.info(
 f"[SIM] {device_name.capitalize()} state -> {state.value} (pin value {val})"
 )
 return True

 try:
 pin = getattr(self.config, f"{device_name}_gpio_pin", None)
 if pin is not None:
 GPIO.output(pin, GPIO.HIGH if val == 1 else GPIO.LOW)
 logger.info(f"{device_name.capitalize()} state -> {state.value} (pin value {val})")
 return True
 except Exception as e:
 logger.error(f"Error setting {device_name} output: {e}")
 return False

 def get_status(self) -> dict[str, Any]:
 return {"enabled": self.enable_control, "states": self.states}

 async def enforce_plan(self, plan: dict) -> bool:
 """Dynamically map optimization plan actions to hardware pins."""
 if not plan:
 return False

 success = True

 # In a unified model, we parse actions from either the unified `actions` dict
 # or from top-level keys ending in `_action` (backward compatibility)
 actions = plan.get("actions", {})
 if not actions:
 for k, v in plan.items():
 if isinstance(k, str) and k.endswith("_action"):
 actions[k.replace("_action", "")] = v

 for device, action_val in actions.items():
 # Normalise "pump_action" -> "pump" so plans from AIAgent.actions work
 if isinstance(device, str) and device.endswith("_action"):
 device = device[: -len("_action")]
 if isinstance(action_val, str):
 action_val = action_val.lower()
 try:
 if action_val in [s.value for s in ActionState]:
 state = ActionState(action_val)
 ok = await self.set_pwm_device(device, state)
 success = success and ok
 elif action_val in [s.value for s in ValveAction]:
 state = ValveAction(action_val)
 ok = await self.set_gpio_device(device, state)
 success = success and ok
 else:
 logger.warning(f"Unknown action state {action_val} for device {device}")
 success = False
 except ValueError:
 success = False

 return success

 async def setup(self) -> None:
 """No-op hook for portal lifecycle / tests."""
 return None

 async def cleanup(self) -> None:
 """Stop PWM and release GPIO when enabled."""
 if self.enable_control and GPIO:
 try:
 for pwm in self.pwms.values():
 with contextlib.suppress(Exception):
 pwm.stop()
 GPIO.cleanup()
 except Exception as e:
 logger.warning("GPIO cleanup: %s", e)
 self.pwms.clear()

 async def health_check(self) -> bool:
 return True

 async def trigger_alert(self, duration_ms: int):
 logger.info(f"Alert triggered for {duration_ms}ms")
