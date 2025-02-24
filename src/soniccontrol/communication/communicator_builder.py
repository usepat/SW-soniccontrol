import logging
from typing import Union

from soniccontrol.communication.connection import Connection
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.message_protocol import SonicMessageProtocol
from soniccontrol.communication.serial_communicator import (
    SerialCommunicator,
)

class CommunicatorBuilder:
    @staticmethod
    async def build(
        connection: Connection, logger: logging.Logger
    ) -> Communicator:
        """
        Builds a connection using the provided `reader` and `writer` objects.

        Args:
            reader (asyncio.StreamReader): The reader object for the connection.
            writer (asyncio.StreamWriter): The writer object for the connection.
            **kwargs: Additional keyword arguments to be passed to the `SerialCommunicator` constructor.

        Returns:
            tuple[Communicator, Commands]: A tuple containing the `Communicator` object and the `Commands` object
            representing the successful connection.

        Raises:
            ConnectionError: If the connection fails due to incompatibility or the device is not responding.

        """

        com_logger = logging.getLogger(logger.name + "." + CommunicatorBuilder.__name__)

        com_logger.info("Trying to connect with new sonic protocol")
        serial = SerialCommunicator(logger=logger) #type: ignore

        try:
            await serial.open_communication(connection)
            await serial.send_and_wait_for_response("?test") # just send some garbage and look, if it returns a valid response
        except Exception as e:
            com_logger.error(str(e))
            if serial.connection_opened.is_set():
                await serial.close_communication()
        else:
            com_logger.info("Connected with sonic protocol")
            return serial
            
        com_logger.warning("Connection could not be established with sonic protocol")
        raise ConnectionError("Failed to connect due to incompatibility")