import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exchange import make_envelope, read_frame, write_frame


HOST_RELATIVE_DIR = Path("engine")
HOST_EXE_CANDIDATES = (
    "HoClothUnity.exe",
    "HoCloth2Unity.exe",
    "HoClothUnityHost.exe",
)
HOST_TCP_HOST = "127.0.0.1"
HOST_TCP_PORT = 39277

_process: subprocess.Popen | None = None


@dataclass(frozen=True)
class HostPaths:
    plugin_root: Path
    host_dir: Path
    executable: Path | None


@dataclass(frozen=True)
class HostStatus:
    engine_available: bool
    running: bool
    host_dir: str
    executable: str
    message: str


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_host_paths() -> HostPaths:
    root = plugin_root()
    host_dir = root / HOST_RELATIVE_DIR
    executable = None
    if host_dir.exists():
        for name in HOST_EXE_CANDIDATES:
            candidate = host_dir / name
            if candidate.exists():
                executable = candidate
                break
        if executable is None:
            executables = sorted(host_dir.glob("*.exe"))
            executable = executables[0] if executables else None
    return HostPaths(root, host_dir, executable)


def is_process_running() -> bool:
    global _process
    if _process is None:
        return False
    if _process.poll() is not None:
        _process = None
        return False
    return True


def can_connect(timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((HOST_TCP_HOST, HOST_TCP_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def wait_until_ready(timeout_seconds: float = 10.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if can_connect(timeout=0.2):
            return True
        time.sleep(0.1)
    return can_connect(timeout=0.2)


def status() -> HostStatus:
    paths = resolve_host_paths()
    listening = can_connect(timeout=0.05)
    process_running = is_process_running()
    engine_available = paths.executable is not None
    if listening:
        message = f"Unity host is listening on {HOST_TCP_HOST}:{HOST_TCP_PORT}."
    elif process_running:
        message = "Unity host process is running, waiting for TCP listener."
    elif engine_available:
        message = "Unity engine executable exists but is not running."
    elif paths.host_dir.exists():
        message = "Unity host folder exists, but no executable was found."
    else:
        message = "Unity engine is not installed yet."
    return HostStatus(
        engine_available=engine_available,
        running=listening or process_running,
        host_dir=str(paths.host_dir),
        executable=str(paths.executable or ""),
        message=message,
    )


def launch(wait_seconds: float = 10.0) -> HostStatus:
    global _process
    if can_connect(timeout=0.1):
        return status()

    if not is_process_running():
        paths = resolve_host_paths()
        if paths.executable is None:
            return status()

        _process = subprocess.Popen(
            [str(paths.executable)],
            cwd=str(paths.executable.parent),
        )

    wait_until_ready(wait_seconds)
    return status()


def terminate() -> HostStatus:
    global _process
    if _process is not None and _process.poll() is None:
        _process.terminate()
    _process = None
    return status()


def request(envelope: dict[str, Any], timeout: float = 10.0) -> dict[str, Any]:
    with socket.create_connection((HOST_TCP_HOST, HOST_TCP_PORT), timeout=timeout) as client:
        stream = client.makefile("rwb")
        write_frame(stream, envelope)
        return read_frame(stream)


def hello(timeout: float = 3.0) -> dict[str, Any]:
    return request(make_envelope("Host", "hello", {}), timeout=timeout)
