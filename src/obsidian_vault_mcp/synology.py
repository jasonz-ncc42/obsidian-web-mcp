"""Synology FileStation API client for Drive sync notification.

Uploads files via the official FileStation API so that Synology Drive Server
detects changes and syncs them to connected clients. Falls back gracefully
if the API is unreachable.
"""

import io
import logging
import threading
import time
from pathlib import PurePosixPath

import httpx

from . import config

logger = logging.getLogger(__name__)

_session_lock = threading.Lock()
_sid: str | None = None
_sid_ts: float = 0
_SID_TTL = 3600  # Re-authenticate every hour


def _base_url() -> str:
    return f"{config.SYNO_SCHEME}://{config.SYNO_HOST}:{config.SYNO_PORT}"


def _login() -> str:
    """Authenticate and return a session ID."""
    global _sid, _sid_ts
    resp = httpx.get(
        f"{_base_url()}/webapi/entry.cgi",
        params={
            "api": "SYNO.API.Auth",
            "version": 6,
            "method": "login",
            "account": config.SYNO_USER,
            "passwd": config.SYNO_PASS,
            "session": "FileStation",
            "format": "sid",
        },
        verify=False,
        timeout=10,
    )
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Synology login failed: {data}")
    _sid = data["data"]["sid"]
    _sid_ts = time.time()
    logger.info("Synology FileStation session acquired")
    return _sid


def _get_sid() -> str:
    """Get a valid session ID, re-authenticating if needed."""
    global _sid, _sid_ts
    with _session_lock:
        if _sid and (time.time() - _sid_ts) < _SID_TTL:
            return _sid
        return _login()


def _filestation_path(relative_path: str) -> str:
    """Convert a vault-relative path to a FileStation absolute path."""
    return str(PurePosixPath(config.SYNO_VAULT_PATH) / relative_path)


def upload_file(relative_path: str, content: str, create_parents: bool = True) -> bool:
    """Upload a file via FileStation API to trigger Drive sync.

    Returns True on success, False on failure (caller should log but not crash).
    """
    if not config.SYNO_ENABLED:
        return False

    try:
        sid = _get_sid()
        folder_path = _filestation_path(str(PurePosixPath(relative_path).parent))
        filename = PurePosixPath(relative_path).name

        resp = httpx.post(
            f"{_base_url()}/webapi/entry.cgi?_sid={sid}",
            data={
                "api": "SYNO.FileStation.Upload",
                "version": "2",
                "method": "upload",
                "path": folder_path,
                "create_parents": str(create_parents).lower(),
                "overwrite": "true",
            },
            files={"file": (filename, io.BytesIO(content.encode("utf-8")), "application/octet-stream")},
            verify=False,
            timeout=30,
        )
        data = resp.json()
        if data.get("success"):
            logger.debug(f"FileStation upload OK: {relative_path}")
            return True
        else:
            logger.warning(f"FileStation upload failed for {relative_path}: {data}")
            return False
    except Exception as e:
        logger.warning(f"FileStation upload error for {relative_path}: {e}")
        return False


def create_folder(relative_path: str) -> bool:
    """Create a folder via FileStation API."""
    if not config.SYNO_ENABLED:
        return False

    try:
        sid = _get_sid()
        parent = _filestation_path(str(PurePosixPath(relative_path).parent))
        name = PurePosixPath(relative_path).name

        resp = httpx.get(
            f"{_base_url()}/webapi/entry.cgi",
            params={
                "api": "SYNO.FileStation.CreateFolder",
                "version": 2,
                "method": "create",
                "folder_path": parent,
                "name": name,
                "_sid": sid,
            },
            verify=False,
            timeout=10,
        )
        data = resp.json()
        if data.get("success"):
            return True
        else:
            logger.warning(f"FileStation create folder failed for {relative_path}: {data}")
            return False
    except Exception as e:
        logger.warning(f"FileStation create folder error for {relative_path}: {e}")
        return False


def move_file(source: str, destination: str) -> bool:
    """Move/rename a file via FileStation API."""
    if not config.SYNO_ENABLED:
        return False

    try:
        sid = _get_sid()
        src_path = _filestation_path(source)
        dst_folder = _filestation_path(str(PurePosixPath(destination).parent))

        resp = httpx.get(
            f"{_base_url()}/webapi/entry.cgi",
            params={
                "api": "SYNO.FileStation.CopyMove",
                "version": 3,
                "method": "start",
                "path": f'["{src_path}"]',
                "dest_folder_path": dst_folder,
                "overwrite": "false",
                "remove_src": "true",
                "_sid": sid,
            },
            verify=False,
            timeout=10,
        )
        data = resp.json()
        if data.get("success"):
            return True
        else:
            logger.warning(f"FileStation move failed {source} → {destination}: {data}")
            return False
    except Exception as e:
        logger.warning(f"FileStation move error {source} → {destination}: {e}")
        return False


def delete_file(relative_path: str) -> bool:
    """Delete a file via FileStation API (actual delete, not soft-delete)."""
    if not config.SYNO_ENABLED:
        return False

    try:
        sid = _get_sid()
        path = _filestation_path(relative_path)

        resp = httpx.get(
            f"{_base_url()}/webapi/entry.cgi",
            params={
                "api": "SYNO.FileStation.Delete",
                "version": 2,
                "method": "start",
                "path": f'["{path}"]',
                "_sid": sid,
            },
            verify=False,
            timeout=10,
        )
        data = resp.json()
        if data.get("success"):
            return True
        else:
            logger.warning(f"FileStation delete failed for {relative_path}: {data}")
            return False
    except Exception as e:
        logger.warning(f"FileStation delete error for {relative_path}: {e}")
        return False
