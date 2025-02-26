import pytest
import asyncio

from soniccontrol.communication.package_protocol import PackageProtocol
from soniccontrol.consts import ENCODING
from soniccontrol.communication.package_fetcher import PackageFetcher


@pytest.mark.asyncio
async def test_get_answer_of_package_ensures_that_order_does_not_matter():
    reader = asyncio.StreamReader()
    protocol = PackageProtocol()
    pkg_fetcher = PackageFetcher(reader, protocol)

    msg = "Hello Package Fetcher"
    msg_id = 15
    msg_str = protocol.parse_request(msg, msg_id)

    try:
        pkg_fetcher.run()

        reader.feed_data(protocol.parse_request("asdfd", 10).encode(ENCODING))
        reader.feed_data(msg_str.encode(ENCODING))
        reader.feed_data(protocol.parse_request("hsghfare", 23).encode(ENCODING))

        answer = await pkg_fetcher.get_answer_of_package(15)
        await pkg_fetcher.stop()
    except Exception as e:
        pytest.fail(f"Unexpected exception raised: {e}")

    assert (answer == msg)

