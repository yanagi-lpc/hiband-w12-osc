"""W12 の BPM を VRChat の OSC へ送る。"""

import argparse
import asyncio

from pythonosc.udp_client import SimpleUDPClient

from hiband_w12_osc.protocol import parse_bpm
from hiband_w12_osc.session import Watch, find_watch


def main() -> None:
    parser = argparse.ArgumentParser(prog="hiband-w12-osc")
    parser.add_argument("--name", default="W12")
    parser.add_argument("--osc-host", default="127.0.0.1")
    parser.add_argument("--osc-port", type=int, default=9000)
    parser.add_argument("--address", default="/avatar/parameters/HR")
    args = parser.parse_args()
    try:
        asyncio.run(run(args.name, args.osc_host, args.osc_port, args.address))
    except KeyboardInterrupt:
        pass


async def run(name: str, osc_host: str, osc_port: int, address: str) -> None:
    osc = SimpleUDPClient(osc_host, osc_port)
    while True:
        print(f"scanning {name}", flush=True)
        found = await find_watch(name)
        if found is None:
            print(
                "not found. disconnect the phone app if it is holding the connection",
                flush=True,
            )
            await asyncio.sleep(2)
            continue
        device, mac = found
        watch = Watch(device)
        try:
            await watch.connect()
            print("connected", flush=True)
            if not await watch.sync_time(mac):
                print("time sync failed", flush=True)
            else:
                print("time sync ok", flush=True)
                await watch.start_hr()
                await _forward_bpm(watch, osc, address)
        except asyncio.CancelledError:
            await watch.stop_hr()
            await watch.disconnect()
            raise
        finally:
            if not watch.disconnected.is_set():
                await watch.stop_hr()
            await watch.disconnect()
        print("disconnected", flush=True)
        await asyncio.sleep(2)


async def _forward_bpm(watch: Watch, osc: SimpleUDPClient, address: str) -> None:
    last: int | None = None
    while not watch.disconnected.is_set():
        payload = await _next_note(watch)
        if payload is None:
            return
        bpm = parse_bpm(payload)
        if bpm is None or bpm == last:
            continue
        last = bpm
        print(f"bpm {bpm}", flush=True)
        osc.send_message(address, bpm)


async def _next_note(watch: Watch) -> bytes | None:
    incoming = asyncio.create_task(watch.notes.get())
    dropped = asyncio.create_task(watch.disconnected.wait())
    done, pending = await asyncio.wait(
        {incoming, dropped},
        timeout=30,
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
    if incoming in done:
        return incoming.result()
    if watch.disconnected.is_set():
        return None
    return b""
