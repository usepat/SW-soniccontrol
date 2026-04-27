import asyncio
from typing import Any, List
import uuid
import aiohttp
import attrs
import cattrs

from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


class RemoteClientError(RuntimeError):
    pass


class RemoteClient:
    def __init__(self, url: str):
        self._url = url
        self._session: aiohttp.ClientSession | None = None

    def start_session(self):
        assert self._session is None, "session already open or not closed"
        self._session = aiohttp.ClientSession()
            

    async def close_client(self):
        if self._session:
            await self._session.close()

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_client()


    async def wait_for_future(self, future_id: uuid.UUID) -> Any:
        async def _poll_task():
            assert self._session
            while True:
                async with self._session.get(self._url + "/poll_future/" + str(future_id)) as response:
                    await self._check_response_ok(response)
                    data = await response.json()

                if data["done"]:
                    if data["exception"] is not None:
                        raise RemoteClientError(data["exception"])
                    else:
                        return data["result"]
        
        task =  asyncio.get_running_loop().create_task(_poll_task())
        await task

        exc = task.exception()
        if exc:
            raise exc
    
        return task.result()

    async def _check_response_ok(self, response: aiohttp.ClientResponse):
        if response.status != 200:
            if response.content_type == "application/json":
                error_message = (await response.json())["error"]
            else:
                error_message = await response.content.read()
            raise RemoteClientError(str(error_message))

    async def get_devices(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = False,
    ) -> List[FwDeviceInfo]:
        assert self._session
        
        # aiohttp requires that the params are strings
        params = {
            "include_ttys": str(include_ttys),
            "include_disks": str(include_disks),
            "include_unverified_ttys": str(include_unverified_ttys),
        }
        
        async with self._session.get(self._url + "/devices", params=params) as response:
            await self._check_response_ok(response)
            data = await response.json()

        dev_infos = cattrs.Converter().structure(data, List[FwDeviceInfo])
        dev_infos = [ attrs.evolve(dev_info, remote_server_url=self._url) for dev_info in dev_infos ]
        return dev_infos

    async def is_port_free(self, port: str) -> bool:
        assert self._session

        # TODO: maybe we need to refactor this, because we changed device detection
        async with self._session.get(self._url + "/is_port_free/" + port) as response:
            await self._check_response_ok(response)
            return (await response.json())["is_connected"]

    async def connect(self, port: str, **kwargs):
        assert self._session

        cmd_args: List[str] = kwargs.get("cmd_args", [])
        baudrate: int = kwargs.get("baudrate", 9600)
        params = { 
            "cmd_args": " ".join(cmd_args), 
            "baudrate": baudrate
        }
        async with self._session.post(self._url + "/connect/" + port, params=params) as response:
            await self._check_response_ok(response)

    async def write(self, port: str, data: bytes):
        assert self._session

        async with self._session.post(
            self._url + "/write/" + port,
            data=data,
            headers={"Content-Type": "application/octet-stream"}
        ) as response:
            await self._check_response_ok(response)

    async def read(self, port: str) -> bytes:
        assert self._session

        async with self._session.get(self._url + "/read/" + port) as response:
            await self._check_response_ok(response)
            return await response.read()

    async def disconnect(self, port: str):
        assert self._session

        async with self._session.post(self._url + "/disconnect/" + port) as response:
            await self._check_response_ok(response)


    async def wait_for_device_redetection(self, dev_info: FwDeviceInfo) -> FwDeviceInfo:
        assert self._session
        
        data = cattrs.Converter().unstructure(dev_info)
        async with self._session.post(self._url + "/wait_for_device_redetection", json=data) as response:
            await self._check_response_ok(response)
            future_id: str = (await response.json())["future_id"]
        
        future_result = await self.wait_for_future(uuid.UUID(future_id))

        new_dev_info = cattrs.structure(future_result, FwDeviceInfo)
        return new_dev_info
        