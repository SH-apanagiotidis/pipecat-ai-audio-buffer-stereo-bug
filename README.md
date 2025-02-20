# Minimal example to reproduce an issue with pipecat-ai's [AudioBufferProcessor](https://github.com/pipecat-ai/pipecat/blob/v0.0.57/src/pipecat/processors/audio/audio_buffer_processor.py)

When using `num_channels=2` to interleave user and bot audio into the same file, and no user audio was received, 
then the `on_audio_data` callback is never called and `AudioBufferProcessor.merge_audio_buffers` returns an empty 
buffer.


## `on_audio_data` callback never called

The callback is called from

- [stop_recording](https://github.com/pipecat-ai/pipecat/blob/v0.0.57/src/pipecat/processors/audio/audio_buffer_processor.py#L98)
  - Either called manually or when processing `CancelFrame` or `EndFrame`
- [process_frame](https://github.com/pipecat-ai/pipecat/blob/v0.0.57/src/pipecat/processors/audio/audio_buffer_processor.py#L115)
  - Only calls the callback when there is user audio

As such, if there is no user audio, then the callback is never called during processing.

When called manually then the other issue prevents accessing bot audio.


## `AudioBufferProcessor.merge_audio_buffers` returns an empty buffer

With [num_channels=1](https://github.com/pipecat-ai/pipecat/blob/v0.0.57/src/pipecat/processors/audio/audio_buffer_processor.py#L84)
this works as expected, i.e., bot audio is returned and there is no user audio. 

For [num_channels=2](https://github.com/pipecat-ai/pipecat/blob/v0.0.57/src/pipecat/processors/audio/audio_buffer_processor.py#L86)
this "breaks" since [interleave_stereo_audio](https://github.com/pipecat-ai/pipecat/blob/v0.0.57/src/pipecat/audio/utils.py#L56)
trims both bot and user audio to the length of the smaller buffer.
Consequently, an empty buffer is returned when there is no user audio, regardless if there is bot audio.

In addition, if user audio would be shorter than bot audio, then we would truncate the bot audio, which is also 
undesirable.

# Reproduction steps

- Save an audio file as `./audio.wav`
  - For example use one from here: https://samplelib.com/sample-wav.html
- Run [server.py](./server.py)
  - This will launch a WebSocket server that will send `./audio.wav` to the first connected client and closes the 
    connection when done
- Set `num_channels=1` in [client.py](https://github.com/SH-apanagiotidis/pipecat-ai-audio-buffer-stereo-bug/blob/main/client.py#L39)
- Run [client.py](./client.py)
  - This will launch a pipecat-ai pipeline that connects to the server and tries to save all received audio
- Restart the server
- Set `num_channels=2` in [client.py](https://github.com/SH-apanagiotidis/pipecat-ai-audio-buffer-stereo-bug/blob/main/client.py#L39)
- Run [client.py](./client.py) again


## Output for `num_channels=1`

```shell
2025-02-20 12:56:15.599 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking PipelineSource#0 -> WebsocketClientInputTransport#0
2025-02-20 12:56:15.599 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking WebsocketClientInputTransport#0 -> WebsocketClientOutputTransport#0
2025-02-20 12:56:15.599 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking WebsocketClientOutputTransport#0 -> AudioBufferProcessor#0
2025-02-20 12:56:15.599 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking AudioBufferProcessor#0 -> PipelineSink#0
2025-02-20 12:56:15.599 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking PipelineTaskSource#0 -> Pipeline#0
2025-02-20 12:56:15.599 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking Pipeline#0 -> PipelineTaskSink#0
2025-02-20 12:56:15.599 | DEBUG    | pipecat.pipeline.runner:run:39 - Runner PipelineRunner#0 started running PipelineTask#0
Connected
Disconnected
user_audio_buffer=0 bytes
bot_audio_buffer=563200 bytes
Merged audio saved to conversation_recording20250220_125633.wav
2025-02-20 12:56:33.192 | DEBUG    | pipecat.pipeline.runner:run:50 - Runner PipelineRunner#0 finished running PipelineTask#0

Process finished with exit code 0
```

## Output for `num_channels=2`

```shell
2025-02-20 12:57:08.914 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking PipelineSource#0 -> WebsocketClientInputTransport#0
2025-02-20 12:57:08.914 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking WebsocketClientInputTransport#0 -> WebsocketClientOutputTransport#0
2025-02-20 12:57:08.914 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking WebsocketClientOutputTransport#0 -> AudioBufferProcessor#0
2025-02-20 12:57:08.914 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking AudioBufferProcessor#0 -> PipelineSink#0
2025-02-20 12:57:08.914 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking PipelineTaskSource#0 -> Pipeline#0
2025-02-20 12:57:08.914 | DEBUG    | pipecat.processors.frame_processor:link:177 - Linking Pipeline#0 -> PipelineTaskSink#0
2025-02-20 12:57:08.915 | DEBUG    | pipecat.pipeline.runner:run:39 - Runner PipelineRunner#0 started running PipelineTask#0
Connected
Disconnected
user_audio_buffer=0 bytes
bot_audio_buffer=563200 bytes
No audio data to save
2025-02-20 12:57:26.515 | DEBUG    | pipecat.pipeline.runner:run:50 - Runner PipelineRunner#0 finished running PipelineTask#0

Process finished with exit code 0
```
