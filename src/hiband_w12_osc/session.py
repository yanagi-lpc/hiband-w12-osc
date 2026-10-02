"""W12 を探して接続し、時刻合わせが通るまで待つ。"""

import asyncio
from datetime import datetime

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from hiband_w12_osc.protocol import build_time_packet, is_time_sync_ok, mac_from_manufacturer

NOTIFY_UUID = "f0080002-0451-4000-b000-000000000000"
WRITE_UUID = "f0080003-0451-4000-b000-000000000000"


async def find_watch(name: str, timeout: float = 10.0) -> tuple[BLEDevice, bytes] | None:
    """名前が一致し、広告に MAC がある個体を返す。"""
    found: dict[str, object] = {}

    def on_detect(device: BLEDevice, advertisement) -> None:
        if found:
            return
        advertised = advertisement.local_name or device.name
        if advertised != name:
            return
        mac = mac_from_manufacturer(advertisement.manufacturer_data)
        if mac is None:
            return
        found["device"] = device
        found["mac"] = mac

    scanner = BleakScanner(detection_callback=on_detect)
    await scanner.start()
    try:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while "device" not in found and loop.time() < deadline:
            await asyncio.sleep(0.2)
    finally:
        await scanner.stop()
    if "device" not in found:
        return None
    return found["device"], found["mac"]  # type: ignore[return-value]


class Watch:
    def __init__(self, device: BLEDevice) -> None:
        self.client = BleakClient(device, disconnected_callback=self._on_disconnect)
        self.notes: asyncio.Queue[bytes] = asyncio.Queue()
        self.disconnected = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None

    def _on_notify(self, _characteristic, data: bytearray) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self.notes.put_nowait, bytes(data))

    def _on_disconnect(self, _client: BleakClient) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self.disconnected.set)

    async def connect(self) -> None:
        self._loop = asyncio.get_running_loop()
        await self.client.connect()
        await self.client.start_notify(NOTIFY_UUID, self._on_notify)

    async def sync_time(self, mac: bytes, timeout: float = 5.0) -> bool:
        await self.client.write_gatt_char(
            WRITE_UUID,
            build_time_packet(datetime.now()),
            response=False,
        )
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                return False
            try:
                payload = await asyncio.wait_for(self.notes.get(), remaining)
            except TimeoutError:
                return False
            if is_time_sync_ok(payload, mac):
                return True

    async def disconnect(self) -> None:
        if self.client.is_connected:
            await self.client.disconnect()
