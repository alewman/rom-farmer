"""SSH client wrapper using Paramiko.

Provides a clean interface for connecting to remote targets,
executing commands, and transferring files over SFTP.
"""

from __future__ import annotations

import logging
import os
import stat
import time
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

try:
    import paramiko
    from paramiko import SFTPClient, SSHClient as _ParamikoSSHClient

    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

# Type alias for progress callbacks: (bytes_transferred, total_bytes)
ProgressCallback = Callable[[int, int], None]


class SSHError(Exception):
    """SSH operation failed."""


class SSHClient:
    """Paramiko-based SSH client for Farm-Hand target operations.

    Manages a persistent SSH connection to a remote target, providing
    command execution and SFTP file transfer with progress tracking.

    Usage:
        client = SSHClient("10.10.20.183", user="root", password="linux")
        client.connect()
        output = client.run("df -h")
        client.upload("/local/file.chd", "/userdata/roms/psx/file.chd")
        client.close()

    Context manager:
        with SSHClient("10.10.20.183", user="root", password="linux") as ssh:
            output = ssh.run("uname -a")
    """

    def __init__(
        self,
        host: str,
        port: int = 22,
        user: str = "root",
        password: Optional[str] = None,
        key_file: Optional[str] = None,
        connect_timeout: float = 10.0,
    ) -> None:
        if not PARAMIKO_AVAILABLE:
            raise ImportError(
                "paramiko is required for Farm-Hand SSH operations. "
                "Install with: pip install 'romfarmer[farmhand]'"
            )

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.key_file = key_file
        self.connect_timeout = connect_timeout

        self._client: Optional[_ParamikoSSHClient] = None
        self._sftp: Optional[SFTPClient] = None

    # -- lifecycle ----------------------------------------------------------

    def connect(self) -> None:
        """Establish SSH connection to the target."""
        if self._client is not None:
            return  # already connected

        self._client = _ParamikoSSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs: dict[str, Any] = {
            "hostname": self.host,
            "port": self.port,
            "username": self.user,
            "timeout": self.connect_timeout,
            "allow_agent": False,
            "look_for_keys": False,
        }

        if self.key_file:
            kwargs["key_filename"] = self.key_file
        elif self.password:
            kwargs["password"] = self.password
        else:
            # Try agent / default keys as last resort
            kwargs["allow_agent"] = True
            kwargs["look_for_keys"] = True

        try:
            self._client.connect(**kwargs)
            logger.info("SSH connected to %s@%s:%d", self.user, self.host, self.port)
        except Exception as exc:
            self._client = None
            raise SSHError(f"SSH connection to {self.host}:{self.port} failed: {exc}") from exc

    def close(self) -> None:
        """Close the SSH connection and SFTP channel."""
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            logger.info("SSH disconnected from %s", self.host)

    @property
    def is_connected(self) -> bool:
        """Check if SSH connection is alive."""
        if self._client is None:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()

    def __enter__(self) -> "SSHClient":
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # -- command execution --------------------------------------------------

    def run(self, command: str, timeout: float = 30.0) -> str:
        """Execute a command on the remote target and return stdout.

        Args:
            command: Shell command to execute.
            timeout: Maximum seconds to wait for completion.

        Returns:
            stdout output as a string.

        Raises:
            SSHError: If the command fails (non-zero exit) or connection is down.
        """
        if not self.is_connected:
            raise SSHError("Not connected — call connect() first")

        assert self._client is not None
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")

            if exit_code != 0:
                logger.warning("Command '%s' exited %d: %s", command, exit_code, err.strip())
                # Still return output — many Batocera commands have
                # non-zero exits for benign reasons.

            return out
        except Exception as exc:
            raise SSHError(f"Command execution failed: {exc}") from exc

    def run_checked(self, command: str, timeout: float = 30.0) -> str:
        """Like run(), but raises SSHError on non-zero exit code."""
        if not self.is_connected:
            raise SSHError("Not connected — call connect() first")

        assert self._client is not None
        stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")

        if exit_code != 0:
            raise SSHError(
                f"Command '{command}' failed (exit {exit_code}): {err.strip()}"
            )
        return out

    # -- SFTP operations ----------------------------------------------------

    def _get_sftp(self) -> SFTPClient:
        """Get or create the SFTP channel."""
        if not self.is_connected:
            raise SSHError("Not connected — call connect() first")

        if self._sftp is None:
            assert self._client is not None
            self._sftp = self._client.open_sftp()
        return self._sftp

    def list_dir(self, remote_path: str) -> list[str]:
        """List directory contents on the remote target.

        Returns:
            List of entry names. Directories end with '/'.
        """
        sftp = self._get_sftp()
        results: list[str] = []
        for entry in sftp.listdir_attr(remote_path):
            name = entry.filename
            if stat.S_ISDIR(entry.st_mode or 0):
                name += "/"
            results.append(name)
        return sorted(results)

    def stat_remote(self, remote_path: str) -> Optional[paramiko.SFTPAttributes]:
        """Stat a remote file. Returns None if not found."""
        sftp = self._get_sftp()
        try:
            return sftp.stat(remote_path)
        except FileNotFoundError:
            return None

    def mkdir_p(self, remote_path: str) -> None:
        """Create remote directory, including parents (like mkdir -p)."""
        sftp = self._get_sftp()
        parts = PurePosixPath(remote_path).parts
        current = ""
        for part in parts:
            current = current + "/" + part if current else "/" + part
            if current == "/":
                continue
            try:
                sftp.stat(current)
            except FileNotFoundError:
                sftp.mkdir(current)
                logger.debug("Created remote dir: %s", current)

    def upload(
        self,
        local_path: str | Path,
        remote_path: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> int:
        """Upload a file to the remote target via SFTP.

        Args:
            local_path: Local file path.
            remote_path: Remote destination path.
            progress_callback: Called with (bytes_transferred, total_bytes).

        Returns:
            Bytes transferred.
        """
        sftp = self._get_sftp()
        local_path = Path(local_path)

        if not local_path.exists():
            raise SSHError(f"Local file not found: {local_path}")

        file_size = local_path.stat().st_size

        # Ensure remote directory exists
        remote_dir = str(PurePosixPath(remote_path).parent)
        self.mkdir_p(remote_dir)

        def _progress(transferred: int, total: int) -> None:
            if progress_callback:
                progress_callback(transferred, total)

        sftp.put(str(local_path), remote_path, callback=_progress)
        logger.debug("Uploaded %s -> %s (%d bytes)", local_path, remote_path, file_size)
        return file_size

    def download(
        self,
        remote_path: str,
        local_path: str | Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> int:
        """Download a file from the remote target via SFTP.

        Returns:
            Bytes transferred.
        """
        sftp = self._get_sftp()
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        remote_stat = sftp.stat(remote_path)
        file_size = remote_stat.st_size or 0

        def _progress(transferred: int, total: int) -> None:
            if progress_callback:
                progress_callback(transferred, total)

        sftp.get(remote_path, str(local_path), callback=_progress)
        logger.debug("Downloaded %s -> %s (%d bytes)", remote_path, local_path, file_size)
        return file_size

    def remove(self, remote_path: str) -> None:
        """Remove a remote file."""
        sftp = self._get_sftp()
        sftp.remove(remote_path)

    def disk_usage(self) -> str:
        """Get disk usage (df -h) from target."""
        return self.run("df -h")

    def file_count(self, remote_path: str) -> int:
        """Count files recursively under a remote path."""
        output = self.run(f"find {remote_path} -type f 2>/dev/null | wc -l", timeout=60)
        try:
            return int(output.strip())
        except ValueError:
            return 0

    def dir_size_bytes(self, remote_path: str) -> int:
        """Get total size of a remote directory in bytes."""
        output = self.run(f"du -sb {remote_path} 2>/dev/null | cut -f1", timeout=120)
        try:
            return int(output.strip())
        except ValueError:
            return 0
