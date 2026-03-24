"""Write tools for the Obsidian vault MCP server."""

import json
import logging

from ..vault import resolve_vault_path, write_file_atomic

logger = logging.getLogger(__name__)


def vault_write(path: str, content: str, create_dirs: bool = True) -> str:
    """Write a file to the vault. Content is written exactly as provided — no parsing or reformatting."""
    try:
        resolve_vault_path(path)
        is_new, size = write_file_atomic(path, content, create_dirs=create_dirs)
        return json.dumps({"path": path, "created": is_new, "size": size})
    except ValueError as e:
        return json.dumps({"error": str(e), "path": path})
    except Exception as e:
        logger.error(f"vault_write error for {path}: {e}")
        return json.dumps({"error": str(e), "path": path})
