"""Unit tests for protocol primitives."""

from datetime import datetime
import struct

from custom_components.heatmiser_time_sync.protocol import (
    _command,
    _datetime_payload,
    crc16,
)


def test_crc_known_ccitt_vector() -> None:
    assert crc16(b"123456789") == 0x29B1


def test_inquiry_command_layout() -> None:
    command = _command(0x93, 1234, struct.pack("<HH", 0, 0xFFFF))
    assert command[0] == 0x93
    assert struct.unpack_from("<H", command, 1)[0] == len(command)
    assert struct.unpack_from("<H", command, 3)[0] == 1234
    assert struct.unpack_from("<H", command, len(command) - 2)[0] == crc16(command[:-2])


def test_datetime_payload_uses_iso_weekday() -> None:
    assert _datetime_payload(datetime(2026, 9, 14, 18, 30, 45)) == bytes(
        (26, 9, 14, 1, 18, 30, 45)
    )
