from typing import List
import aiohttp


class RemoteClient:
    def __init__(self, url: str):
        self._url = url
        self._session = aiohttp.ClientSession()

    async def close_client(self):
        await self._session.close()

    async def _check_response_ok(self, response: aiohttp.ClientResponse):
        if response.status != 200:
            if response.content_type == "application/json":
                error_message = (await response.json())["error"]
            else:
                error_message = await response.content.read()
            raise Exception(error_message)

    async def scan_available_ports(self) -> List[str]:
        async with self._session.get(self._url + "/scan_available_ports") as response:
            await self._check_response_ok(response)
            return (await response.json())["ports"]

    async def is_port_free(self, port: str) -> bool:
        async with self._session.get(self._url + "/is_port_free/" + port) as response:
            await self._check_response_ok(response)
            return (await response.json())["is_connected"]

    async def connect(self, port: str, **kwargs):
        cmd_args: List[str] = kwargs.get("cmd_args", [])
        baudrate: int = kwargs.get("baudrate", 9600)
        params = { 
            "cmd_args": " ".join(cmd_args), 
            "baudrate": baudrate
        }
        async with self._session.post(self._url + "/connect/" + port, params=params) as response:
            await self._check_response_ok(response)

    async def write(self, port: str, data: bytes):
        async with self._session.post(
            self._url + "/write/" + port,
            data=data,
            headers={"Content-Type": "application/octet-stream"}
        ) as response:
            await self._check_response_ok(response)

    async def read(self, port: str) -> bytes:
        async with self._session.get(self._url + "/read/" + port) as response:
            await self._check_response_ok(response)
            return await response.read()

    async def disconnect(self, port: str):
        async with self._session.post(self._url + "/disconnect/" + port) as response:
            await self._check_response_ok(response)
