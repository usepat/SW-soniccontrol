
from soniccontrol.flashing.tools.bootloader_protocol import Protocol_RP2040
from serial_asyncio import open_serial_connection
import logging


async def main(port: str = "COM23", baudrate: int = 115200):
    reader, writer = await open_serial_connection(url=port, baudrate=baudrate)
    protocol = Protocol_RP2040(logging.getLogger(), writer, reader, 0.1)
    retries = 0
    while retries < 3:
        synced = await protocol.sync_cmd()
        if synced:
            print("Sync successful")
            break
        else:
            print("Sync failed")
            retries += 1





if __name__ == "__main__":
    main()