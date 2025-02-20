import json
import logging

from pipecat.frames.frames import (
    Frame,
    AudioRawFrame,
    StartFrame,
    TransportMessageFrame,
    TransportMessageUrgentFrame, TextFrame, OutputAudioRawFrame,
)
from pipecat.serializers.base_serializer import FrameSerializer, FrameSerializerType

logger = logging.getLogger(__name__)


class CustomFrameSerializer(FrameSerializer):
    def __init__(self):
        self._sample_rate_hz = None
        self._num_channels = 1

    @property
    def type(self) -> FrameSerializerType:
        return FrameSerializerType.TEXT

    async def setup(self, frame: StartFrame):
        self._sample_rate_hz = frame.audio_in_sample_rate

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if isinstance(frame, (TransportMessageFrame, TransportMessageUrgentFrame)):
            return json.dumps(frame.message)
        elif isinstance(frame, AudioRawFrame):
            return frame.audio
        else:
            logger.warning(f"Cannot serialize: {frame}")
            return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, str):
            return TextFrame(json.loads(data))
        elif isinstance(data, bytes):
            return OutputAudioRawFrame(
                audio=data,
                sample_rate=self._sample_rate_hz,
                num_channels=self._num_channels,
            )
        else:
            logger.warning(f"Cannot deserialize: {data}")
            return None
