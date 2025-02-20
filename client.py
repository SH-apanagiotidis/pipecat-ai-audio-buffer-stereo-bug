import asyncio
import datetime
import io
import wave

import aiofiles
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor
from pipecat.transports.network.websocket_client import WebsocketClientTransport, WebsocketClientParams

from custom_frame_serializer import CustomFrameSerializer


async def save_audio(audio: bytes, sample_rate: int, num_channels: int):
    if len(audio) > 0:
        filename = f"conversation_recording{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        with io.BytesIO() as buffer:
            with wave.open(buffer, "wb") as wf:
                wf.setsampwidth(2)
                wf.setnchannels(num_channels)
                wf.setframerate(sample_rate)
                wf.writeframes(audio)
            async with aiofiles.open(filename, "wb") as file:
                await file.write(buffer.getvalue())
        print(f"Merged audio saved to {filename}")
    else:
        print("No audio data to save")


async def main():
    audio_buffer = AudioBufferProcessor(
        sample_rate=None,
        # If num_channels=2 and there is no user audio, then merge_audio_buffers returns an empty buffer
        # because interleave_stereo_audio cuts both bot and user audio to the length of the smaller buffer, i.e.,
        # 0 bytes :/
        num_channels=1,
        user_continuous_stream=True,
        buffer_size=0,
    )

    transport = WebsocketClientTransport(
        uri="ws://localhost:8765/",
        params=WebsocketClientParams(
            serializer=CustomFrameSerializer(),

            add_wav_header=False,

            audio_in_enabled=True,
            audio_in_channels=1,
            audio_in_stream_on_start=True,

            audio_out_enabled=True,
            audio_out_channels=1,
            audio_out_is_live=True,

            vad_enabled=False,
        ),
    )

    pipeline = Pipeline([
        transport.input(),
        transport.output(),
        audio_buffer,
    ])

    task = PipelineTask(
        pipeline=pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=16000,
        ),
    )

    @audio_buffer.event_handler("on_audio_data")
    async def on_audio_data(buffer, audio, sample_rate, num_channels):
        print(f"Received {len(audio)} bytes of audio (sample_rate={sample_rate} num_channels={num_channels})")
        await save_audio(audio, sample_rate, num_channels)

    @transport.event_handler("on_connected")
    async def on_connected(transport: WebsocketClientTransport, client):
        print("Connected")
        await audio_buffer.start_recording()

    @transport.event_handler("on_disconnected")
    async def on_disconnected(transport: WebsocketClientTransport, client):
        print("Disconnected")
        await task.queue_frame(EndFrame())

    runner = PipelineRunner()

    await runner.run(task)

    print(f"user_audio_buffer={len(audio_buffer._user_audio_buffer)} bytes")
    print(f"bot_audio_buffer={len(audio_buffer._bot_audio_buffer)} bytes")

    await save_audio(audio_buffer.merge_audio_buffers(), audio_buffer.sample_rate, audio_buffer.num_channels)


if __name__ == "__main__":
    asyncio.run(main())
