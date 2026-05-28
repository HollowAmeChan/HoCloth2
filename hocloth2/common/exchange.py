from copy import deepcopy
from typing import Any, Literal, TypedDict


SCHEMA_NAME = "hocloth.exchange"
SCHEMA_VERSION = 1
COORDINATE_SPACE = "blender_world"
LENGTH_UNIT = "meter"
QUATERNION_ORDER = "wxyz"

PayloadType = Literal[
    "authoring_snapshot",
    "frame_inputs",
    "build_output",
    "step_output",
]


class ExchangeEnvelope(TypedDict):
    schema: str
    schema_version: int
    backend: str
    payload_type: str
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
        return deepcopy(snapshot_or_dict)
    return make_envelope(backend, "authoring_snapshot", deepcopy(dict(snapshot_or_dict or {})))
