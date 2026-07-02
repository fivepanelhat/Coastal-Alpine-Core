import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AVCapture:
    """Unified Audio/Video Capture Module for Coastal Alpine Portals."""

    def __init__(self, config: Any = None, **kwargs):
        if config:
            self.config = config
            self.camera_device = getattr(config, "camera", None)
            self.audio_device = getattr(config, "audio", None)
        else:
            self.config = kwargs
            self.camera_device = kwargs
            self.audio_device = kwargs

    async def capture_frame(self) -> bytes:
        """Capture a single JPEG frame from the configured camera."""
        await asyncio.sleep(0.1)
        return b"MOCK_JPEG_FRAME_DATA"

    async def capture_audio_chunk(self) -> bytes:
        """Capture a chunk of audio from the configured microphone."""
        await asyncio.sleep(0.1)
        return b"MOCK_AUDIO_DATA"

    def start_video_stream(self) -> bool:
        return True

    def start_audio_stream(self) -> bool:
        return True

    def stop(self):
        pass

    async def health_check(self) -> bool:
        return True
