"""
Backend Runner for HuffZip.
Handles locating, auto-compiling, and executing the C Huffman compression backend safely.
"""

from __future__ import annotations

import os
import platform
import shutil
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class BackendResult:
    """Result data structure returned from compression or decompression."""
    success: bool
    mode: str
    input_path: str
    output_path: str
    original_size: int = 0
    output_size: int = 0
    saved_bytes: int = 0
    savings_pct: float = 0.0
    ratio: float = 0.0
    error_message: str = ""
    stdout: str = ""
    stderr: str = ""


HUFF_MAGIC = b"HUFF"
HUFF_VERSION = 1


def format_size(size_bytes: int, detailed: bool = False) -> str:
    """Formats file size into human-readable string (e.g. 1.25 MB)."""
    if size_bytes < 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    val = float(size_bytes)
    while val >= 1024.0 and unit_index < len(units) - 1:
        val /= 1024.0
        unit_index += 1

    formatted = f"{val:.2f} {units[unit_index]}"
    if detailed and unit_index > 0:
        return f"{formatted} ({size_bytes:,} bytes)"
    return formatted


def get_backend_executable_name() -> str:
    """Returns the expected executable name based on OS."""
    return "huff.exe" if platform.system() == "Windows" else "huff"


def find_project_root() -> Path:
    """Returns the root directory of the HuffZip project."""
    # Current file is in <root>/gui/backend_runner.py
    current_dir = Path(__file__).resolve().parent
    if (current_dir.parent / "backend").is_dir():
        return current_dir.parent
    if (current_dir / "backend").is_dir():
        return current_dir
    return Path.cwd()


def find_backend_executable() -> Optional[Path]:
    """
    Locates the compiled C backend executable across standard locations.
    Returns Path if found and executable, else None.
    """
    root = find_project_root()
    exe_name = get_backend_executable_name()

    candidate_paths = [
        root / "backend" / exe_name,
        root / exe_name,
        root / "bin" / exe_name,
        Path.cwd() / "backend" / exe_name,
        Path.cwd() / exe_name,
    ]

    # If packaged via PyInstaller
    if hasattr(sys, "_MEIPASS"):
        meipass_root = Path(sys._MEIPASS)
        candidate_paths.insert(0, meipass_root / "backend" / exe_name)
        candidate_paths.insert(1, meipass_root / exe_name)

    for path in candidate_paths:
        if path.is_file() and os.access(path, os.X_OK):
            return path
        # On Windows, os.access(path, os.X_OK) can be true for any file, but checking is_file is sufficient
        if platform.system() == "Windows" and path.is_file():
            return path

    # Check system PATH
    which_path = shutil.which("huff") or shutil.which("huff.exe")
    if which_path:
        return Path(which_path)

    return None


def compile_backend() -> Tuple[bool, str]:
    """
    Attempts to compile the C backend using gcc.
    Returns (success, message).
    """
    root = find_project_root()
    backend_dir = root / "backend"
    if not backend_dir.is_dir():
        backend_dir = root

    sources = ["main.c", "huffman.c", "heap.c", "fileio.c", "utils.c"]
    missing = [s for s in sources if not (backend_dir / s).is_file()]
    if missing:
        return False, f"Missing C source files in {backend_dir}: {', '.join(missing)}"

    exe_name = get_backend_executable_name()
    target_path = backend_dir / exe_name

    gcc_cmd = shutil.which("gcc")
    if not gcc_cmd:
        return False, "GCC compiler not found on PATH. Please install MinGW or GCC."

    cmd = [
        gcc_cmd,
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-O2",
        "-o",
        str(target_path),
    ] + [str(backend_dir / s) for s in sources]

    try:
        process = subprocess.run(
            cmd,
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if process.returncode == 0 and target_path.is_file():
            return True, f"Successfully built backend at {target_path}"
        else:
            err = process.stderr.strip() or process.stdout.strip()
            return False, f"Compilation failed (code {process.returncode}):\n{err}"
    except Exception as exc:
        return False, f"Error running compiler: {exc}"


def ensure_backend_executable() -> Tuple[Optional[Path], str]:
    """
    Finds the backend executable or attempts to compile it automatically.
    Returns (executable_path, status_message).
    """
    exe = find_backend_executable()
    if exe:
        return exe, f"Found existing executable: {exe.name}"

    # Try auto-compiling
    success, msg = compile_backend()
    if success:
        exe = find_backend_executable()
        if exe:
            return exe, "Compiled backend successfully"
    return None, f"Could not locate or compile backend executable. {msg}"


def validate_huff_header(file_path: str | Path) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validates whether a file is a valid HuffZip compressed archive.
    Checks:
      - File exists and is at least 2061 bytes (4 magic + 1 ver + 8 size + 2048 freq table)
      - Magic bytes == b"HUFF"
      - Version == 1
    Returns:
      (is_valid, original_uncompressed_size, error_reason)
    """
    path = Path(file_path)
    if not path.is_file():
        return False, None, "File does not exist"

    file_size = path.stat().st_size
    min_header_size = 4 + 1 + 8 + (256 * 8)  # 2061 bytes
    if file_size < min_header_size:
        return False, None, f"File too small ({file_size} bytes). Minimum HuffZip archive size is {min_header_size} bytes."

    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != HUFF_MAGIC:
                return False, None, f"Invalid magic header '{magic!r}'. Expected 'HUFF'."

            version = f.read(1)
            if not version or version[0] != HUFF_VERSION:
                return False, None, f"Unsupported version '{version!r}'. Expected version {HUFF_VERSION}."

            size_bytes = f.read(8)
            if len(size_bytes) != 8:
                return False, None, "Could not read original file size."

            orig_size = struct.unpack("<Q", size_bytes)[0]
            return True, orig_size, None
    except Exception as exc:
        return False, None, f"Header read error: {exc}"


def run_compress(
    input_path: str | Path,
    output_path: str | Path,
    backend_exe: Optional[Path] = None,
    verbose: bool = False,
) -> BackendResult:
    """
    Executes Huffman compression on input_path writing to output_path.
    Calculates actual compression statistics and cleans up on failure.
    """
    in_p = Path(input_path).resolve()
    out_p = Path(output_path).resolve()

    if not in_p.is_file():
        return BackendResult(
            success=False,
            mode="compress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message=f"Input file not found: {in_p}",
        )

    if in_p == out_p:
        return BackendResult(
            success=False,
            mode="compress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message="Input and output paths cannot be identical.",
        )

    # Ensure output parent directory exists
    try:
        out_p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return BackendResult(
            success=False,
            mode="compress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message=f"Cannot create destination directory: {exc}",
        )

    # Locate executable
    exe = backend_exe or find_backend_executable()
    if not exe:
        exe, compile_msg = ensure_backend_executable()
        if not exe:
            return BackendResult(
                success=False,
                mode="compress",
                input_path=str(in_p),
                output_path=str(out_p),
                error_message=f"Backend executable unavailable: {compile_msg}",
            )

    original_size = in_p.stat().st_size

    # Command arguments: huff compress [-v] <input> <output>
    cmd = [str(exe), "compress"]
    if verbose:
        cmd.append("-v")
    cmd.extend([str(in_p), str(out_p)])

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        if out_p.is_file():
            out_p.unlink(missing_ok=True)
        return BackendResult(
            success=False,
            mode="compress",
            input_path=str(in_p),
            output_path=str(out_p),
            original_size=original_size,
            error_message="Compression timed out after 300 seconds.",
        )
    except Exception as exc:
        if out_p.is_file():
            out_p.unlink(missing_ok=True)
        return BackendResult(
            success=False,
            mode="compress",
            input_path=str(in_p),
            output_path=str(out_p),
            original_size=original_size,
            error_message=f"Failed to execute backend process: {exc}",
        )

    if process.returncode != 0:
        # Clean up partial output file
        if out_p.is_file():
            out_p.unlink(missing_ok=True)
        err = process.stderr.strip() or process.stdout.strip() or f"Process exited with code {process.returncode}"
        return BackendResult(
            success=False,
            mode="compress",
            input_path=str(in_p),
            output_path=str(out_p),
            original_size=original_size,
            error_message=f"Compression failed: {err}",
            stdout=process.stdout,
            stderr=process.stderr,
        )

    if not out_p.is_file():
        return BackendResult(
            success=False,
            mode="compress",
            input_path=str(in_p),
            output_path=str(out_p),
            original_size=original_size,
            error_message="Backend reported success, but output file was not created.",
            stdout=process.stdout,
            stderr=process.stderr,
        )

    compressed_size = out_p.stat().st_size
    saved_bytes = original_size - compressed_size
    savings_pct = (saved_bytes / original_size * 100.0) if original_size > 0 else 0.0
    ratio = (original_size / compressed_size) if compressed_size > 0 else 0.0

    return BackendResult(
        success=True,
        mode="compress",
        input_path=str(in_p),
        output_path=str(out_p),
        original_size=original_size,
        output_size=compressed_size,
        saved_bytes=saved_bytes,
        savings_pct=savings_pct,
        ratio=ratio,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def run_decompress(
    input_path: str | Path,
    output_path: str | Path,
    backend_exe: Optional[Path] = None,
) -> BackendResult:
    """
    Executes Huffman decompression on input_path writing to output_path.
    Verifies input archive and output restored size.
    """
    in_p = Path(input_path).resolve()
    out_p = Path(output_path).resolve()

    if not in_p.is_file():
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message=f"Input compressed file not found: {in_p}",
        )

    if in_p == out_p:
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message="Input and output paths cannot be identical.",
        )

    # Validate header first
    is_valid, header_orig_size, val_err = validate_huff_header(in_p)
    if not is_valid:
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message=f"Invalid HuffZip archive: {val_err}",
        )

    # Ensure output parent directory exists
    try:
        out_p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message=f"Cannot create destination directory: {exc}",
        )

    exe = backend_exe or find_backend_executable()
    if not exe:
        exe, compile_msg = ensure_backend_executable()
        if not exe:
            return BackendResult(
                success=False,
                mode="decompress",
                input_path=str(in_p),
                output_path=str(out_p),
                error_message=f"Backend executable unavailable: {compile_msg}",
            )

    cmd = [str(exe), "decompress", str(in_p), str(out_p)]

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        if out_p.is_file():
            out_p.unlink(missing_ok=True)
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message="Decompression timed out after 300 seconds.",
        )
    except Exception as exc:
        if out_p.is_file():
            out_p.unlink(missing_ok=True)
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message=f"Failed to execute backend process: {exc}",
        )

    if process.returncode != 0:
        if out_p.is_file():
            out_p.unlink(missing_ok=True)
        err = process.stderr.strip() or process.stdout.strip() or f"Process exited with code {process.returncode}"
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message=f"Decompression failed: {err}",
            stdout=process.stdout,
            stderr=process.stderr,
        )

    if not out_p.is_file():
        return BackendResult(
            success=False,
            mode="decompress",
            input_path=str(in_p),
            output_path=str(out_p),
            error_message="Backend reported success, but restored file was not created.",
            stdout=process.stdout,
            stderr=process.stderr,
        )

    restored_size = out_p.stat().st_size
    compressed_size = in_p.stat().st_size

    return BackendResult(
        success=True,
        mode="decompress",
        input_path=str(in_p),
        output_path=str(out_p),
        original_size=header_orig_size if header_orig_size is not None else restored_size,
        output_size=restored_size,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def open_in_file_manager(target_path: str | Path) -> bool:
    """
    Reveals the file in Windows File Explorer or OS file manager.
    """
    path = Path(target_path).resolve()
    try:
        current_os = platform.system()
        if current_os == "Windows":
            if path.exists():
                # /select,<path> selects the file in Explorer
                subprocess.run(["explorer", f"/select,{os.path.normpath(str(path))}"], check=False)
            else:
                folder = path.parent if path.parent.exists() else Path.home()
                subprocess.run(["explorer", os.path.normpath(str(folder))], check=False)
            return True
        elif current_os == "Darwin":
            if path.exists():
                subprocess.run(["open", "-R", str(path)], check=False)
            else:
                subprocess.run(["open", str(path.parent)], check=False)
            return True
        else:
            folder = path.parent if path.is_file() else path
            subprocess.run(["xdg-open", str(folder)], check=False)
            return True
    except Exception:
        return False
