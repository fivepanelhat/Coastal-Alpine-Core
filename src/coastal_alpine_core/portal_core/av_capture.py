import asyncio
import logging

logger = logging.getLogger(__name__)

# Optional hardware backends — dev machines and CI usually lack them.
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pyaudio
except ImportError:
    pyaudio = None


class AVCapture:
    """Unified Audio/Video Capture Module for Coastal Alpine Portals.

    Wraps OpenCV (camera) and PyAudio (microphone). Both are optional:
    when a backend is missing the corresponding stream simply reports
    unavailable instead of crashing the portal.
    """

    def __init__(
        self,
        camera_index: int = 0,
        video_fps: int = 30,
        audio_sample_rate: int = 16000,
        audio_chunk_size: int = 4096,
    ):
        self.camera_index = camera_index
        self.video_fps = video_fps
        self.audio_sample_rate = audio_sample_rate
        self.audio_chunk_size = audio_chunk_size
        self.video_capture = None
        self.audio_stream = None
        self._pyaudio_instance = None

    async def start_video_stream(self) -> bool:
        """Open the camera. False when OpenCV is missing or the device won't open."""
        if cv2 is None:
            logger.warning("OpenCV (cv2) not installed — video capture unavailable.")
            return False
        try:
            capture = cv2.VideoCapture(self.camera_index)
            if not capture.isOpened():
                logger.error(f"Camera index {self.camera_index} could not be opened.")
                return False
            capture.set(cv2.CAP_PROP_FPS, self.video_fps)
            self.video_capture = capture
            logger.info(f"Video stream started (camera {self.camera_index} @ {self.video_fps}fps)")
            return True
        except Exception as e:
            logger.error(f"Failed to start video stream: {e}")
            return False

    async def start_audio_stream(self) -> bool:
        """Open the microphone. False when PyAudio is missing or the device fails."""
        if pyaudio is None:
            logger.warning("PyAudio not installed — audio capture unavailable.")
            return False
        try:
            self._pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self._pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.audio_sample_rate,
                input=True,
                frames_per_buffer=self.audio_chunk_size,
            )
            logger.info(f"Audio stream started ({self.audio_sample_rate}Hz)")
            return True
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            return False

    async def capture_frame(self) -> bytes | None:
        """Grab one frame and return it JPEG-encoded, or None on failure."""
        if self.video_capture is None or not self.video_capture.isOpened():
            return None
        try:
            ok, frame = await asyncio.to_thread(self.video_capture.read)
            if not ok:
                logger.warning("Camera read returned no frame.")
                return None
            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                logger.warning("JPEG encoding of captured frame failed.")
                return None
            return encoded.tobytes()
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None

    async def capture_audio_chunk(self) -> bytes | None:
        """Read one chunk from the microphone, or None when unavailable."""
        if self.audio_stream is None:
            return None
        try:
            return await asyncio.to_thread(
                self.audio_stream.read, self.audio_chunk_size, exception_on_overflow=False
            )
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            return None

    async def stop(self):
        """Release camera and microphone resources."""
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        if self.audio_stream is not None:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        if self._pyaudio_instance is not None:
            self._pyaudio_instance.terminate()
            self._pyaudio_instance = None
        logger.info("AV capture stopped and resources released.")

    async def health_check(self) -> bool:
        """Healthy when not yet started, or when at least one stream is live.

        A portal booting without camera/mic hardware is degraded, not dead —
        only report unhealthy when streams were started and ALL have gone down.
        """
        if self.video_capture is None and self.audio_stream is None:
            return True
        video_ok = self.video_capture is not None and self.video_capture.isOpened()
        audio_ok = self.audio_stream is not None and self.audio_stream.is_active()
        return video_ok or audio_ok
