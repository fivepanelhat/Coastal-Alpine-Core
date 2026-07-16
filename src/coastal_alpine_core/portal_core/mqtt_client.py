import asyncio
import contextlib
import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


class MQTTClient:
    """Unified MQTT Client Module for Coastal Alpine Portals.

    paho-mqtt backed. Incoming JSON messages are queued on an asyncio.Queue
    so portal orchestrators can `await read_message()` without blocking on
    the paho network thread.
    """

    CONNECT_ATTEMPTS = 3

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        client_id: str = "portal-client",
        topic_prefix: str = "portal/sensors",
        max_queue_size: int = 100,
        **kwargs,
    ):
        # Legacy callers used broker=/port= keywords
        self.broker_host = kwargs.get("broker", broker_host)
        self.broker_port = kwargs.get("port", broker_port)
        self.username = username
        self.password = password
        self.client_id = client_id
        self.topic_prefix = topic_prefix
        self.connected = False
        # Bounded queue: when full, drop oldest so slow AI loops never OOM the Pi
        self.max_queue_size = max(1, int(kwargs.get("max_queue_size", max_queue_size)))
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)

        if mqtt is None:
            raise ImportError(
                "paho-mqtt is required for MQTTClient — install coastal-alpine-core[mqtt] "
                "or add paho-mqtt>=2.1.0 to your requirements."
            )

        try:
            # paho 2.x — VERSION1 keeps the rc-style callback signatures
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1, client_id=client_id
            )
        except AttributeError:  # paho 1.x
            self.client = mqtt.Client(client_id=client_id)

        if username:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    @classmethod
    def from_config(cls, config: Any, client_id: str = "portal-client"):
        mqtt_cfg = config.mqtt
        return cls(
            broker_host=mqtt_cfg.broker,
            broker_port=mqtt_cfg.port,
            username=mqtt_cfg.username,
            password=mqtt_cfg.password,
            client_id=client_id,
            topic_prefix=mqtt_cfg.topic_prefix,
        )

    # ---------------- paho callbacks (network thread) ----------------

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            wildcard = f"{self.topic_prefix}/#"
            self.client.subscribe(wildcard)
            logger.info(f"MQTT connected; subscribed to {wildcard}")
        else:
            self.connected = False
            logger.error(f"MQTT connection refused (rc={rc})")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT unexpectedly disconnected (rc={rc})")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Dropping malformed MQTT payload on {msg.topic}: {e}")
            return
        item = {
            "topic": msg.topic,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            self.message_queue.put_nowait(item)
        except asyncio.QueueFull:
            # Drop oldest, keep newest sensor reading (edge backpressure)
            with contextlib.suppress(asyncio.QueueEmpty):
                self.message_queue.get_nowait()
            try:
                self.message_queue.put_nowait(item)
            except asyncio.QueueFull:
                logger.warning("MQTT queue full; dropping message on %s", msg.topic)

    # ---------------- portal-facing API ----------------

    async def connect(self) -> bool:
        """Connect with retry/backoff. False after CONNECT_ATTEMPTS failures."""
        for attempt in range(1, self.CONNECT_ATTEMPTS + 1):
            try:
                self.client.connect(self.broker_host, self.broker_port, keepalive=60)
                self.client.loop_start()
                logger.info(
                    f"MQTT connecting to {self.broker_host}:{self.broker_port} "
                    f"(ID: {self.client_id})"
                )
                return True
            except Exception as e:
                logger.warning(
                    f"MQTT connect attempt {attempt}/{self.CONNECT_ATTEMPTS} failed: {e}"
                )
                if attempt < self.CONNECT_ATTEMPTS:
                    await asyncio.sleep(2**attempt)
        logger.error("MQTT connection failed after all retries.")
        return False

    async def disconnect(self) -> None:
        """Gracefully stop the network loop and disconnect."""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
        logger.info("MQTT disconnected.")

    async def read_message(self) -> dict:
        """Await the next parsed sensor message."""
        return await self.message_queue.get()

    async def publish(self, topic: str, payload: str, qos: int = 1) -> bool:
        """Publish a message to a topic under the configured prefix."""
        full_topic = f"{self.topic_prefix}/{topic}"
        if not self.connected:
            logger.warning(f"Cannot publish to {full_topic}: MQTT not connected")
            return False
        result = self.client.publish(full_topic, payload, qos=qos)
        logger.debug(f"Published to {full_topic}: {payload[:50]}...")
        return getattr(result, "rc", 0) == 0

    async def health_check(self) -> bool:
        return self.connected
