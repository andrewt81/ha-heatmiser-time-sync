"""Async client for the legacy Heatmiser Wi-Fi V3 protocol.

Derived from Alexander Thoukydides' GPL-3.0-or-later heatmiser-wifi project.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import struct


class HeatmiserError(Exception):
    """Base Heatmiser communication error."""


class HeatmiserAuthError(HeatmiserError):
    """Raised when the thermostat rejects the PIN."""


class HeatmiserProtocolError(HeatmiserError):
    """Raised for an invalid thermostat response."""


@dataclass(frozen=True)
class SyncResult:
    """Clock values returned by one synchronisation."""

    before: datetime
    requested: datetime
    after: datetime
    model: str


def crc16(data: bytes) -> int:
    """Calculate the Heatmiser CRC-16/CCITT value."""
    lookup = (
        0x0000, 0x1021, 0x2042, 0x3063,
        0x4084, 0x50A5, 0x60C6, 0x70E7,
        0x8108, 0x9129, 0xA14A, 0xB16B,
        0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
    )
    value = 0xFFFF
    for octet in data:
        value = ((value << 4) & 0xFFFF) ^ lookup[(value >> 12) ^ (octet >> 4)]
        value = ((value << 4) & 0xFFFF) ^ lookup[(value >> 12) ^ (octet & 0x0F)]
    return value


def _command(opcode: int, pin: int, data: bytes = b"") -> bytes:
    body = bytes((opcode,)) + struct.pack("<HH", 7 + len(data), pin) + data
    return body + struct.pack("<H", crc16(body))


def _decode_response(packet: bytes) -> tuple[int, bytes]:
    if len(packet) < 5:
        raise HeatmiserProtocolError("Response is too short")
    length = struct.unpack_from("<H", packet, 1)[0]
    if length != len(packet):
        raise HeatmiserProtocolError("Response length mismatch")
    expected_crc = struct.unpack_from("<H", packet, len(packet) - 2)[0]
    if crc16(packet[:-2]) != expected_crc:
        raise HeatmiserProtocolError("Response CRC mismatch")
    return packet[0], packet[3:-2]


def _decode_datetime(dcb: bytes) -> tuple[datetime, str]:
    if len(dcb) < 48:
        raise HeatmiserProtocolError("Thermostat data block is too short")
    models = {0: "DT", 1: "DT-E", 2: "PRT", 3: "PRT-E", 4: "PRTHW", 5: "TM1"}
    model = models.get(dcb[4], f"unknown-{dcb[4]}")
    base = 44 if model in ("PRTHW", "TM1") else 41
    year, month, day, _weekday, hour, minute, second = dcb[base : base + 7]
    try:
        return datetime(2000 + year, month, day, hour, minute, second), model
    except ValueError as err:
        raise HeatmiserProtocolError("Invalid clock value in thermostat response") from err


def _datetime_payload(value: datetime) -> bytes:
    # Heatmiser uses Monday=1 ... Sunday=7.
    return bytes((value.year - 2000, value.month, value.day, value.isoweekday(),
                  value.hour, value.minute, value.second))


class HeatmiserClient:
    """Minimal client that reads and updates only the thermostat clock."""

    def __init__(self, host: str, port: int, pin: str, timeout: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.pin = int(pin)
        self.timeout = timeout

    async def _exchange(self, request: bytes) -> tuple[int, bytes]:
        writer: asyncio.StreamWriter | None = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), self.timeout
            )
            writer.write(request)
            await asyncio.wait_for(writer.drain(), self.timeout)
            header = await asyncio.wait_for(reader.readexactly(3), self.timeout)
            length = struct.unpack_from("<H", header, 1)[0]
            if length < 5 or length > 65535:
                raise HeatmiserProtocolError("Invalid response length")
            remainder = await asyncio.wait_for(reader.readexactly(length - 3), self.timeout)
            return _decode_response(header + remainder)
        except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError) as err:
            raise HeatmiserError(f"Unable to communicate with {self.host}:{self.port}") from err
        finally:
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass

    async def read_clock(self) -> tuple[datetime, str]:
        """Read the current clock and model."""
        opcode, data = await self._exchange(
            _command(0x93, self.pin, struct.pack("<HH", 0, 0xFFFF))
        )
        if opcode != 0x94 or len(data) < 4:
            raise HeatmiserProtocolError("Unexpected inquiry response")
        start, length = struct.unpack_from("<HH", data)
        if start != 0:
            raise HeatmiserProtocolError("Unexpected data block start address")
        if length == 0:
            raise HeatmiserAuthError("The thermostat rejected the PIN")
        dcb = data[4:]
        if len(dcb) != length:
            raise HeatmiserProtocolError("Thermostat data block length mismatch")
        return _decode_datetime(dcb)

    async def write_clock(self, value: datetime) -> tuple[datetime, str]:
        """Write the clock and return the clock echoed by the thermostat."""
        item = struct.pack("<HB", 43, 7) + _datetime_payload(value)
        opcode, data = await self._exchange(_command(0xA3, self.pin, bytes((1,)) + item))
        if opcode != 0x94 or len(data) < 4:
            raise HeatmiserProtocolError("Unexpected write response")
        start, length = struct.unpack_from("<HH", data)
        if start != 0:
            raise HeatmiserProtocolError("Unexpected write response start address")
        if length == 0:
            raise HeatmiserAuthError("The thermostat rejected the PIN")
        dcb = data[4:]
        if len(dcb) != length:
            raise HeatmiserProtocolError("Write response data block length mismatch")
        return _decode_datetime(dcb)

    async def sync_clock(self, now: datetime) -> SyncResult:
        """Read, update, and verify the thermostat clock."""
        before, model = await self.read_clock()
        requested = now.replace(tzinfo=None, microsecond=0)
        after, returned_model = await self.write_clock(requested)
        return SyncResult(before, requested, after, returned_model or model)
