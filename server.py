import asyncio
import websockets

async def send_audio_chunks(websocket):
    try:
        with open("audio.wav", "rb") as audio_file:
            while chunk := audio_file.read(960):
                print("sending")
                await websocket.send(chunk)
        await websocket.close()
    except Exception as e:
        print(f"Error sending audio: {e}")

async def handle_connection(websocket):
    print("Client connected")
    asyncio.create_task(send_audio_chunks(websocket))

    async for message in websocket:
        if isinstance(message, str):
            print(f"Received text: {message}")
            if message == "PING":
                await websocket.send("PONG")
        elif isinstance(message, bytes):
            print(f"Received binary data of length: {len(message)}")

async def main():
    server = await websockets.serve(handle_connection, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
