import asyncio
import aioconsole

class SimulationController:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._stop_event = asyncio.Event()

    async def connect(self):
        """Establish the connection and start a background reader task."""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print(f"Connected to {self.host}:{self.port}")
        
        # Start a background task to read incoming data
        asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        """Continuously read from the socket until stopped or disconnected."""
        while not self._stop_event.is_set():
            if self.reader is None:
                break
            data = await self.reader.read(1024)
            if not data:
                # Socket closed or no more data
                print("Connection closed by the remote side.")
                await self.close()
                break

            # Handle the incoming data
            print(f"Received data: {data}")

    async def write(self, data: bytes):
        """Send data over the socket (non-blocking)."""
        if self.writer is not None:
            self.writer.write(data)
            await self.writer.drain()
            print(f"Sent data: {data!r}")
        else:
            print("Cannot write: no active connection.")

    async def close(self):
        """Close the connection and stop the read loop."""
        self._stop_event.set()
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()
        print("Connection closed.")


async def main():
    client = SimulationController("127.0.0.1", 1024)
    await client.connect()

    try:
        while True:
            # Asynchronously get user input using aioconsole
            command = await aioconsole.ainput("Enter command: ")
            if command.lower() in {"exit", "quit"}:
                print("Exiting...")
                break
            await client.write(command.encode())
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting...")
    finally:
        await client.close()

# Run the demo
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")