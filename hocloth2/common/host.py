import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exchange import read_frame, write_frame


HOST_RELATIVE_DIR = Path("bundled") / "unity_host" / "windows-x64"
HOST_EXE_CANDIDATES = (
    "HoClothUnity.exe",
    "HoCloth2Unity.exe",
    "HoClothUnityHost.exe",
)

_process: subprocess.Popen | None = None


@dataclass(frozen=True)
class HostPaths:
    plugin_root: Path
    host_dir: Path
    executable: Path | None


@dataclass(frozen=True)
class HostStatus:
    bundled: bool
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


def is_running() -> bool:
    global _process
    if _process is None:
        return False
    if _process.poll() is not None:
        _process = None
        return False
    return True


def status() -> HostStatus:
    paths = resolve_host_paths()
    running = is_running()
    bundled = paths.executable is not None
    if running:
        message = "Unity host is running."
    elif bundled:
        message = "Unity host executable is bundled but not running."
    elif paths.host_dir.exists():
        message = "Unity host folder exists, but no executable was found."
    else:
        message = "Unity host is not bundled yet."
    return HostStatus(
        bundled=bundled,
        running=running,
        host_dir=str(paths.host_dir),
        executable=str(paths.executable or ""),
        message=message,
    )


def launch() -> HostStatus:
    global _process
    if is_running():
        return status()

    paths = resolve_host_paths()
    if paths.executable is None:
        return status()

    _process = subprocess.Popen(
        [str(paths.executable)],
        cwd=str(paths.executable.parent),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return status()


def terminate() -> HostStatus:
    global _process
    if _process is not None and _process.poll() is None:
        _process.terminate()
    _process = None
    return status()


def send(envelope: dict[str, Any]) -> None:
    if not is_running() or _process is None or _process.stdin is None:
        raise RuntimeError("Unity host is not running.")
    write_frame(_process.stdin, envelope)


def receive() -> dict[str, Any]:
    if not is_running() or _process is None or _process.stdout is None:
        raise RuntimeError("Unity host is not running.")
    return read_frame(_process.stdout)


def request(envelope: dict[str, Any]) -> dict[str, Any]:
    send(envelope)
    return receive()
