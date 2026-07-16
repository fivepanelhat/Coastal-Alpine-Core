"""
portal_core/config.py - Unified Configuration Module for Coastal Alpine Portals.

Validates and loads environmental settings, sensor thresholds, hardware control maps, and consent metrics for AquaGuard, SoilGuard, and BlueMoon portals.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Local Ollama LLM execution parameters."""

    host: str = Field(default="http://localhost:11434")
    model: str = Field(default="gemma4:e4b")

    @field_validator("host", mode="before")
    @classmethod
    def validate_host(cls, v):
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("Ollama host must start with http:// or https://")
        return v


class MQTTConfig(BaseModel):
    """MQTT broker connection parameters."""

    broker: str = Field(default="localhost")
    port: int = Field(default=1883, ge=1, le=65535)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    topic_prefix: str = Field(default="portal/sensors")


class StorageConfig(BaseModel):
    """Storage directories and media file pruner thresholds."""

    media_dir: Path = Field(default=Path("./telemetry_data/media"))
    sensor_logs_dir: Path = Field(default=Path("./telemetry_data/sensor_logs"))
    compliance_dir: Path = Field(default=Path("./telemetry_data/compliance"))
    retention_hours: int = Field(default=48, ge=1)
    critical_disk_usage_pct: float = Field(default=85.0, ge=50.0, le=99.0)

    @field_validator("media_dir", "sensor_logs_dir", "compliance_dir", mode="before")
    @classmethod
    def create_and_validate_paths(cls, v):
        path = Path(v) if isinstance(v, str) else v
        path.mkdir(parents=True, exist_ok=True)
        return path


class CameraConfig(BaseModel):
    """Physical CSI/USB camera configurations."""

    device_index: int = Field(default=0, ge=0)
    fps: int = Field(default=30, ge=5, le=120)


class AudioConfig(BaseModel):
    """Audio sampling settings for acoustic leak monitoring."""

    sample_rate: int = Field(default=16000)
    chunk_size: int = Field(default=4096, ge=256, le=65536)

    @field_validator("sample_rate", mode="before")
    @classmethod
    def validate_rate(cls, v):
        valid = [8000, 16000, 44100, 48000]
        if v not in valid:
            raise ValueError(f"Sample rate must be one of {valid}")
        return v


class LoggingConfig(BaseModel):
    """Daemon logging profiles."""

    level: str = Field(default="INFO")
    file: Path | None = Field(default=None)

    @field_validator("level", mode="before")
    @classmethod
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


# =====================================================================
# AquaGuard Portal Configurations
# =====================================================================


class AquaGuardHardwareConfig(BaseModel):
    aerator_gpio_pin: int | None = Field(default=None)
    pump_gpio_pin: int | None = Field(default=None)
    valve_gpio_pin: int | None = Field(default=None)
    alert_gpio_pin: int | None = Field(default=None)
    enable_hardware_control: bool = Field(default=False)


class AquaGuardConsentConfig(BaseModel):
    regional_council: str = Field(default="Horizons Regional Council")
    consent_id: str = Field(default="CONSENT-2026-AUTH-0981")


class AquaGuardThresholdConfig(BaseModel):
    ph_min: float = Field(default=6.5, ge=0.0, le=14.0)
    ph_max: float = Field(default=8.5, ge=0.0, le=14.0)
    do_min: float = Field(default=5.0, ge=0.0)
    temp_max: float = Field(default=24.0, ge=0.0)
    turbidity_max: float = Field(default=50.0, ge=0.0)
    nitrate_max: float = Field(default=10.0, ge=0.0)


class AquaGuardConfig(BaseModel):
    ollama: OllamaConfig
    mqtt: MQTTConfig
    storage: StorageConfig
    camera: CameraConfig
    audio: AudioConfig
    hardware: AquaGuardHardwareConfig
    consent: AquaGuardConsentConfig
    thresholds: AquaGuardThresholdConfig
    logging: LoggingConfig


def load_aquaguard_config() -> AquaGuardConfig:
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded configuration from environment file: {env_file.resolve()}")
    else:
        logger.warning("No .env configuration file discovered; utilizing runtime defaults.")

    try:
        config = AquaGuardConfig(
            ollama=OllamaConfig(
                host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
            ),
            mqtt=MQTTConfig(
                broker=os.getenv("MQTT_BROKER", "localhost"),
                port=int(os.getenv("MQTT_PORT", "1883")),
                username=os.getenv("MQTT_USERNAME"),
                password=os.getenv("MQTT_PASSWORD"),
                topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "aquaguard/sensors"),
            ),
            storage=StorageConfig(
                media_dir=os.getenv("MEDIA_DIR", "./telemetry_data/media"),
                sensor_logs_dir=os.getenv("SENSOR_LOGS_DIR", "./telemetry_data/sensor_logs"),
                compliance_dir=os.getenv("COMPLIANCE_DIR", "./telemetry_data/compliance"),
                retention_hours=int(os.getenv("MEDIA_RETENTION_HOURS", "48")),
                critical_disk_usage_pct=float(os.getenv("CRITICAL_DISK_USAGE_PCT", "85.0")),
            ),
            camera=CameraConfig(
                device_index=int(os.getenv("CAMERA_DEVICE_INDEX", "0")),
                fps=int(os.getenv("CAMERA_FPS", "30")),
            ),
            audio=AudioConfig(
                sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
                chunk_size=int(os.getenv("AUDIO_CHUNK_SIZE", "4096")),
            ),
            hardware=AquaGuardHardwareConfig(
                aerator_gpio_pin=int(p) if (p := os.getenv("HARDWARE_AERATOR_GPIO_PIN")) else None,
                pump_gpio_pin=int(p) if (p := os.getenv("HARDWARE_PUMP_GPIO_PIN")) else None,
                valve_gpio_pin=int(p) if (p := os.getenv("HARDWARE_VALVE_GPIO_PIN")) else None,
                alert_gpio_pin=int(p) if (p := os.getenv("HARDWARE_ALERT_GPIO_PIN")) else None,
                enable_hardware_control=os.getenv("HARDWARE_ENABLE_CONTROL", "false").lower()
                == "true",
            ),
            consent=AquaGuardConsentConfig(
                regional_council=os.getenv("REGIONAL_COUNCIL", "Horizons Regional Council"),
                consent_id=os.getenv("CONSENT_ID", "CONSENT-2026-AUTH-0981"),
            ),
            thresholds=AquaGuardThresholdConfig(
                ph_min=float(os.getenv("THRESHOLD_PH_MIN", "6.5")),
                ph_max=float(os.getenv("THRESHOLD_PH_MAX", "8.5")),
                do_min=float(os.getenv("THRESHOLD_DO_MIN", "5.0")),
                temp_max=float(os.getenv("THRESHOLD_TEMP_MAX", "24.0")),
                turbidity_max=float(os.getenv("THRESHOLD_TURBIDITY_MAX", "50.0")),
                nitrate_max=float(os.getenv("THRESHOLD_NITRATE_MAX", "10.0")),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                file=Path(f) if (f := os.getenv("LOG_FILE")) else None,
            ),
        )
        return config
    except Exception as e:
        logger.error(f"Failed loading / validating configuration parameters: {e}")
        raise


# =====================================================================
# SoilGuard Portal Configurations
# =====================================================================


class SoilGuardHardwareConfig(BaseModel):
    irrigation_gpio_pin: int | None = Field(default=None)
    nutrient_gpio_pin: int | None = Field(default=None)
    fan_gpio_pin: int | None = Field(default=None)
    alert_gpio_pin: int | None = Field(default=None)
    enable_hardware_control: bool = Field(default=False)


class SoilGuardConsentConfig(BaseModel):
    regional_council: str = Field(default="Waikato Regional Council")
    consent_id: str = Field(default="CONSENT-2026-SOIL-1992")


class SoilGuardThresholdConfig(BaseModel):
    moisture_min: float = Field(default=15.0, ge=0.0)
    moisture_max: float = Field(default=50.0, ge=0.0)
    temp_max: float = Field(default=35.0, ge=0.0)
    ec_max: float = Field(default=2.5, ge=0.0)
    nitrogen_max: float = Field(default=50.0, ge=0.0)
    phosphorus_max: float = Field(default=80.0, ge=0.0)
    potassium_max: float = Field(default=300.0, ge=0.0)
    ph_min: float = Field(default=5.5, ge=0.0, le=14.0)
    ph_max: float = Field(default=7.5, ge=0.0, le=14.0)


class SoilGuardConfig(BaseModel):
    ollama: OllamaConfig
    mqtt: MQTTConfig
    storage: StorageConfig
    camera: CameraConfig
    audio: AudioConfig
    hardware: SoilGuardHardwareConfig
    consent: SoilGuardConsentConfig
    thresholds: SoilGuardThresholdConfig
    logging: LoggingConfig


def load_soilguard_config() -> SoilGuardConfig:
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded configuration from environment file: {env_file.resolve()}")
    else:
        logger.warning("No .env configuration file discovered; utilizing runtime defaults.")

    try:
        config = SoilGuardConfig(
            ollama=OllamaConfig(
                host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
            ),
            mqtt=MQTTConfig(
                broker=os.getenv("MQTT_BROKER", "localhost"),
                port=int(os.getenv("MQTT_PORT", "1883")),
                username=os.getenv("MQTT_USERNAME"),
                password=os.getenv("MQTT_PASSWORD"),
                topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "soilguard/sensors"),
            ),
            storage=StorageConfig(
                media_dir=os.getenv("MEDIA_DIR", "./telemetry_data/media"),
                sensor_logs_dir=os.getenv("SENSOR_LOGS_DIR", "./telemetry_data/sensor_logs"),
                compliance_dir=os.getenv("COMPLIANCE_DIR", "./telemetry_data/compliance"),
                retention_hours=int(os.getenv("MEDIA_RETENTION_HOURS", "48")),
                critical_disk_usage_pct=float(os.getenv("CRITICAL_DISK_USAGE_PCT", "85.0")),
            ),
            camera=CameraConfig(
                device_index=int(os.getenv("CAMERA_DEVICE_INDEX", "0")),
                fps=int(os.getenv("CAMERA_FPS", "30")),
            ),
            audio=AudioConfig(
                sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
                chunk_size=int(os.getenv("AUDIO_CHUNK_SIZE", "4096")),
            ),
            hardware=SoilGuardHardwareConfig(
                irrigation_gpio_pin=int(p)
                if (p := os.getenv("HARDWARE_IRRIGATION_GPIO_PIN"))
                else None,
                nutrient_gpio_pin=int(p)
                if (p := os.getenv("HARDWARE_NUTRIENT_GPIO_PIN"))
                else None,
                fan_gpio_pin=int(p) if (p := os.getenv("HARDWARE_FAN_GPIO_PIN")) else None,
                alert_gpio_pin=int(p) if (p := os.getenv("HARDWARE_ALERT_GPIO_PIN")) else None,
                enable_hardware_control=os.getenv("HARDWARE_ENABLE_CONTROL", "false").lower()
                == "true",
            ),
            consent=SoilGuardConsentConfig(
                regional_council=os.getenv("REGIONAL_COUNCIL", "Waikato Regional Council"),
                consent_id=os.getenv("CONSENT_ID", "CONSENT-2026-SOIL-1992"),
            ),
            thresholds=SoilGuardThresholdConfig(
                moisture_min=float(os.getenv("THRESHOLD_MOISTURE_MIN", "15.0")),
                moisture_max=float(os.getenv("THRESHOLD_MOISTURE_MAX", "50.0")),
                temp_max=float(os.getenv("THRESHOLD_TEMP_MAX", "35.0")),
                ec_max=float(os.getenv("THRESHOLD_EC_MAX", "2.5")),
                nitrogen_max=float(os.getenv("THRESHOLD_NITROGEN_MAX", "50.0")),
                phosphorus_max=float(os.getenv("THRESHOLD_PHOSPHORUS_MAX", "80.0")),
                potassium_max=float(os.getenv("THRESHOLD_POTASSIUM_MAX", "300.0")),
                ph_min=float(os.getenv("THRESHOLD_PH_MIN", "5.5")),
                ph_max=float(os.getenv("THRESHOLD_PH_MAX", "7.5")),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                file=Path(f) if (f := os.getenv("LOG_FILE")) else None,
            ),
        )
        return config
    except Exception as e:
        logger.error(f"Failed loading / validating configuration parameters: {e}")
        raise


# =====================================================================
# Blue Moon Portal Configurations
# =====================================================================


class BlueMoonHardwareConfig(BaseModel):
    pump_gpio_pin: int | None = Field(default=None)
    pump_pwm_frequency: int = Field(default=1000, ge=100, le=10000)
    lighting_gpio_pin: int | None = Field(default=None)
    lighting_pwm_frequency: int = Field(default=1000, ge=100, le=10000)
    alert_gpio_pin: int | None = Field(default=None)
    enable_hardware_control: bool = Field(default=False)


class PortalConfig(BaseModel):
    ollama: OllamaConfig
    mqtt: MQTTConfig
    storage: StorageConfig
    camera: CameraConfig
    audio: AudioConfig
    hardware: BlueMoonHardwareConfig
    logging: LoggingConfig
    model_config = ConfigDict(arbitrary_types_allowed=True)


def load_config() -> PortalConfig:
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded configuration from environment file: {env_file.resolve()}")
    else:
        logger.warning("No .env configuration file discovered; utilizing runtime defaults.")

    try:
        config = PortalConfig(
            ollama=OllamaConfig(
                host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
            ),
            mqtt=MQTTConfig(
                broker=os.getenv("MQTT_BROKER", "localhost"),
                port=int(os.getenv("MQTT_PORT", "1883")),
                username=os.getenv("MQTT_USERNAME"),
                password=os.getenv("MQTT_PASSWORD"),
                topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "horowhenua/sensors"),
            ),
            storage=StorageConfig(
                media_dir=os.getenv("MEDIA_DIR", "./telemetry_data/media"),
                sensor_logs_dir=os.getenv("SENSOR_LOGS_DIR", "./telemetry_data/sensor_logs"),
                retention_hours=int(os.getenv("MEDIA_RETENTION_HOURS", "48")),
                critical_disk_usage_pct=float(os.getenv("CRITICAL_DISK_USAGE_PCT", "85.0")),
            ),
            camera=CameraConfig(
                device_index=int(os.getenv("CAMERA_DEVICE_INDEX", "0")),
                fps=int(os.getenv("CAMERA_FPS", "30")),
            ),
            audio=AudioConfig(
                sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
                chunk_size=int(os.getenv("AUDIO_CHUNK_SIZE", "4096")),
            ),
            hardware=BlueMoonHardwareConfig(
                pump_gpio_pin=int(p) if (p := os.getenv("HARDWARE_PUMP_GPIO_PIN")) else None,
                pump_pwm_frequency=int(os.getenv("HARDWARE_PUMP_PWM_FREQUENCY", "1000")),
                lighting_gpio_pin=int(p)
                if (p := os.getenv("HARDWARE_LIGHTING_GPIO_PIN"))
                else None,
                lighting_pwm_frequency=int(os.getenv("HARDWARE_LIGHTING_PWM_FREQUENCY", "1000")),
                alert_gpio_pin=int(p) if (p := os.getenv("HARDWARE_ALERT_GPIO_PIN")) else None,
                enable_hardware_control=os.getenv(
                    "HARDWARE_ENABLE_HARDWARE_CONTROL", "false"
                ).lower()
                == "true",
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                file=Path(f) if (f := os.getenv("LOG_FILE")) else None,
            ),
        )
        return config
    except Exception as e:
        logger.error(f"Failed loading / validating configuration parameters: {e}")
        raise
