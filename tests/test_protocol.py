from datetime import datetime

from hiband_w12_osc.protocol import (
    build_time_packet,
    is_time_sync_ok,
    mac_from_manufacturer,
    parse_bpm,
)


def test_time_packet_matches_observed_monday():
    when = datetime(2026, 9, 28, 18, 45, 54)
    packet = build_time_packet(when)
    assert packet[:14] == bytes.fromhex("a100000007ea091c122d36010124")
    assert len(packet) == 20
    assert packet[14:] == bytes(6)


def test_time_packet_friday_in_october_is_binary_not_bcd():
    when = datetime(2026, 10, 2, 18, 39, 11)
    packet = build_time_packet(when)
    assert packet[4:12] == bytes.fromhex("07ea0a0212270b05")


def test_mac_comes_from_company_f8f8():
    mac = bytes.fromhex("9a48be5b69fe")
    assert mac_from_manufacturer({0xF8F8: mac + b"\x00"}) == mac
    assert mac_from_manufacturer({0x004C: mac}) is None
    assert mac_from_manufacturer({0xF8F8: b"\x01\x02"}) is None


def test_time_sync_requires_status_and_advertised_mac():
    mac = bytes.fromhex("9a48be5b69fe")
    ok = bytes.fromhex("a10000060c140438010000019a48be5b69fe0001")
    before_time = bytes.fromhex("a10000000c14043801000001000000000000000000")
    assert is_time_sync_ok(ok, mac)
    assert not is_time_sync_ok(before_time, mac)
    assert not is_time_sync_ok(ok, bytes(6))


def test_bpm_is_second_byte_when_at_least_one():
    assert parse_bpm(bytes.fromhex("d04c00")) == 76
    assert parse_bpm(bytes.fromhex("d05500")) == 85
    assert parse_bpm(bytes.fromhex("d06300")) == 99
    assert parse_bpm(bytes.fromhex("d00000")) is None
    assert parse_bpm(bytes.fromhex("906f4a640001")) is None
