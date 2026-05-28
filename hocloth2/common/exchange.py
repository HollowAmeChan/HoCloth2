import struct
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal, TypedDict

import msgpack


SCHEMA_NAME = "hocloth.exchange"
SCHEMA_VERSION = 1
COORDINATE_SPACE = "blender_world"
LENGTH_UNIT = "meter"
QUATERNION_ORDER = "wxyz"
PAYLOAD_ENCODING = "msgpack"
FRAME_LENGTH_FORMAT = "<I"
FRAME_LENGTH_SIZE = struct.calcsize(FRAME_LENGTH_FORMAT)

PayloadType = Literal[
    "hello",
    "host_status",
    "authoring_snapshot",
    "build_request",
    "build_output",
    "frame_inputs",
    "step_request",
    "step_output",
    "error",
]


class ExchangeEnvelope(TypedDict):
    schema: str
    schema_version: int
    backend: str
    payload_type: str
    payload_encoding: str
    coordinate_space: str
    length_unit: str
    quaternion_order: str
    payload: dict[str, Any]


def is_exchange_envelope(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema") == SCHEMA_NAME
        and isinstance(value.get("backend"), str)
        and isinstance(value.get("payload_type"), str)
        and isinstance(value.get("payload"), dict)
    )


def make_envelope(
    backend: str,
    payload_type: PayloadType,
    payload: dict[str, Any] | None = None,
) -> ExchangeEnvelope:
    return {
        "schema": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "backend": backend,
        "payload_type": payload_type,
        "payload_encoding": PAYLOAD_ENCODING,
        "coordinate_space": COORDINATE_SPACE,
        "length_unit": LENGTH_UNIT,
        "quaternion_order": QUATERNION_ORDER,
        "payload": payload or {},
    }


def unwrap_payload(
    value: dict[str, Any] | None,
    expected_backend: str | None = None,
    expected_type: PayloadType | None = None,
) -> dict[str, Any]:
    if value is None:
        return {}
    if not is_exchange_envelope(value):
        return value
    if expected_backend is not None and value.get("backend") != expected_backend:
        raise ValueError(f"Expected backend '{expected_backend}', got '{value.get('backend')}'.")
    if expected_type is not None and value.get("payload_type") != expected_type:
        raise ValueError(f"Expected payload '{expected_type}', got '{value.get('payload_type')}'.")
    return value.get("payload") or {}


def wrap_authoring_snapshot(backend: str, snapshot_or_dict: Any) -> ExchangeEnvelope:
    if is_exchange_envelope(snapshot_or_dict):
        if snapshot_or_dict.get("backend") != backend:
            raise ValueError(f"Expected backend '{backend}', got '{snapshot_or_dict.get('backend')}'.")
        if snapshot_or_dict.get("payload_type") != "authoring_snapshot":
            raise ValueError(
                "Expected payload 'authoring_snapshot', "
                f"got '{snapshot_or_dict.get('payload_type')}'."
            )
        wrapped = deepcopy(snapshot_or_dict)
        wrapped["payload_encoding"] = PAYLOAD_ENCODING
        return wrapped
    return make_envelope(backend, "authoring_snapshot", deepcopy(dict(snapshot_or_dict or {})))


def pack_message(envelope: dict[str, Any]) -> bytes:
    if not is_exchange_envelope(envelope):
        raise ValueError("Cannot pack a non HoCloth exchange envelope.")
    normalized = deepcopy(envelope)
    normalized["payload_encoding"] = PAYLOAD_ENCODING
    return msgpack.packb(normalized, use_bin_type=True, strict_types=False)


def unpack_message(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = msgpack.unpackb(data, raw=False, strict_map_key=False)
    if not is_exchange_envelope(value):
        raise ValueError("Decoded MessagePack data is not a HoCloth exchange envelope.")
    return value


def write_messagepack_file(path: str | Path, envelope: dict[str, Any]) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_bytes(pack_message(envelope))
    return resolved


def read_messagepack_file(path: str | Path) -> dict[str, Any]:
    return unpack_message(Path(path).read_bytes())


def pack_frame(envelope: dict[str, Any]) -> bytes:
    body = pack_message(envelope)
    if len(body) > 0xFFFFFFFF:
        raise ValueError("MessagePack frame is larger than uint32 length prefix allows.")
    return struct.pack(FRAME_LENGTH_FORMAT, len(body)) + body


def unpack_frame(frame: bytes | bytearray | memoryview) -> dict[str, Any]:
    data = memoryview(frame)
    if len(data) < FRAME_LENGTH_SIZE:
        raise ValueError("Frame is shorter than the length prefix.")
    (length,) = struct.unpack(FRAME_LENGTH_FORMAT, data[:FRAME_LENGTH_SIZE])
    body = data[FRAME_LENGTH_SIZE:]
    if len(body) != length:
        raise ValueError(f"Frame body length mismatch: expected {length}, got {len(body)}.")
    return unpack_message(body)


def read_exact(stream, byte_count: int) -> bytes:
    chunks = []
    remaining = byte_count
    while remaining > 0:
        chunk = stream.read(remaining)
        if not chunk:
            raise EOFError(f"Expected {byte_count} bytes, stream ended with {remaining} bytes remaining.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_frame(stream) -> dict[str, Any]:
    header = read_exact(stream, FRAME_LENGTH_SIZE)
    (length,) = struct.unpack(FRAME_LENGTH_FORMAT, header)
    return unpack_message(read_exact(stream, length))


def write_frame(stream, envelope: dict[str, Any]) -> None:
    stream.write(pack_frame(envelope))
    flush = getattr(stream, "flush", None)
    if flush is not None:
        flush()
