"""時刻合わせと心拍通知のバイト列。"""

from datetime import datetime

PACKET_LEN = 20
COMPANY_ID = 0xF8F8

HR_START = bytes((0xD0, 0x01))
HR_STOP = bytes((0xD0, 0x00))


def build_time_packet(when: datetime) -> bytes:
    """ローカル時刻を a1 パケットにする。余りは 00。"""
    packet = bytearray(PACKET_LEN)
    packet[0] = 0xA1
    packet[4:6] = when.year.to_bytes(2, "big")
    packet[6] = when.month
    packet[7] = when.day
    packet[8] = when.hour
    packet[9] = when.minute
    packet[10] = when.second
    packet[11] = when.isoweekday()
    packet[12] = 0x01
    packet[13] = 0x24
    return bytes(packet)


def mac_from_manufacturer(manufacturer_data: dict[int, bytes]) -> bytes | None:
    """広告の company 0xF8F8 の後ろ 6 バイトを MAC にする。"""
    payload = manufacturer_data.get(COMPANY_ID)
    if payload is None or len(payload) < 6:
        return None
    return bytes(payload[:6])


def is_time_sync_ok(payload: bytes, mac: bytes) -> bool:
    """a1 応答の 4 バイト目が 06 で、13〜18 バイト目が広告の MAC と一致するか。"""
    if len(payload) < 18 or len(mac) != 6:
        return False
    return payload[0] == 0xA1 and payload[3] == 0x06 and payload[12:18] == mac


def parse_bpm(payload: bytes) -> int | None:
    """d0 の 2 バイト目が 1 以上のときだけ BPM にする。"""
    if len(payload) < 2 or payload[0] != 0xD0:
        return None
    bpm = payload[1]
    if bpm < 1:
        return None
    return bpm
