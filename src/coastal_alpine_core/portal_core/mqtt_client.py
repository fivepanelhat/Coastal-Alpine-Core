import asyncio
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class MQTTClient:
    """Unified MQTT Client Module for Coastal Alpine Portals."""

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: str = "portal-client",
        topic_prefix: str = "portal/sensors",
        **kwargs
    ):
        self.broker = kwargs.get("broker_host", broker)
        self.port = kwargs.get("broker_port", port)
        self.username = username
        self.password = password
        self.client_id = client_id
        self.topic_prefix = topic_prefix
        self.connected = False
        self._subscriptions = {}

    def _on_message(self, client, userdata, msg):
        pass

    async def health_check(self) -> bool:
        return self.connected

    @classmethod
    def from_config(cls, config: Any, client_id: str = "portal-client"):
        mqtt_cfg = config.mqtt
        return cls(
            broker=mqtt_cfg.broker,
            port=mqtt_cfg.port,
            username=mqtt_cfg.username,
            password=mqtt_cfg.password,
            client_id=client_id,
            topic_prefix=mqtt_cfg.topic_prefix,
        )

    async def connect(self) -> bool:
        """Connect to the MQTT broker."""
        logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port} (ID: {self.client_id})")
        # Simulated connection delay
        await asyncio.sleep(0.5)
        self.connected = True
        logger.info("MQTT connection established")
        return True

    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        logger.info("Disconnecting from MQTT broker")
        self.connected = False

    async def publish(self, topic: str, payload: str, qos: int = 1) -> bool:
        """Publish a message to a specific topic under the prefix."""
        full_topic = f"{self.topic_prefix}/{topic}"
        if not self._connected:
            logger.warning(f"Cannot publish to {full_topic}: MQTT not connected")
            return False
        
        logger.debug(f"Published to {full_topic}: {payload[:50]}...")
        # Simulated publish
        await asyncio.sleep(0.05)
        return True

    async def subscribe(self, topic: str, callback: Callable[[str, str], None]) -> bool:
        """Subscribe to a specific topic and register a callback."""
        full_topic = f"{self.topic_prefix}/{topic}"
        if not self._connected:
            logger.warning(f"Cannot subscribe to {full_topic}: MQTT not connected")
            return False
            
        self._subscriptions[full_topic] = callback
        logger.info(f"Subscribed to {full_topic}")
        # Simulated subscribe
        await asyncio.sleep(0.05)
        return True
