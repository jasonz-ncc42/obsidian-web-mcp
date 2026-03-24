"""Management tools for the Obsidian vault MCP server."""

import json
import logging

from .. import config
from ..vault import list_directory, move_path, delete_path, resolve_vault_path

logger = logging.getLogger(__name__)


def vault_list(
    path: str = "",
    depth: int = 1,
    include_files: bool = True,
    include_dirs: bool = True,
    pattern: str | None = None,
) -> str:
    """List directory contents in the vault."""
    try:
        items = list_directory(
            path,
            depth=depth,
            include_files=include_files,
            include_dirs=include_dirs,
            pattern=pattern,
        )
        return json.dumps({"items": items, "total": len(items)})
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except FileNotFoundError:
        return json.dumps({"error": f"Directory not found: {path}"})
    except Exception as e:
        logger.error(f"vault_list error: {e}")
        return json.dumps({"error": str(e)})


def vault_tree(path: str = "", depth: int = 3) -> str:
    """Return a nested JSON tree of the vault directory structure with file counts."""
    try:
        vault_root = config.VAULT_PATH.resolve()
        start = resolve_vault_path(path) if path else vault_root
        if not start.is_dir():
            return json.dumps({"error": f"Not a directory: {path}"})

        depth = min(depth, 10)

        def _build(dir_path, current_depth):
            node = {"name": dir_path.name, "files": [], "dirs": []}
            try:
                entries = sorted(dir_path.iterdir(), key=lambda p: p.name.lower())
            except PermissionError:
                return node

            for entry in entries:
                if entry.name in config.EXCLUDED_DIRS:
                    continue
                if entry.is_file():
                    node["files"].append(entry.name)
                elif entry.is_dir():
                    if current_depth < depth:
                        node["dirs"].append(_build(entry, current_depth + 1))
                    else:
                        # Beyond max depth, just show name and counts
                        try:
                            children = list(entry.iterdir())
                            fc = sum(1 for c in children if c.is_file() and c.name not in config.EXCLUDED_DIRS)
                            dc = sum(1 for c in children if c.is_dir() and c.name not in config.EXCLUDED_DIRS)
                        except PermissionError:
                            fc, dc = 0, 0
                        node["dirs"].append({"name": entry.name, "file_count": fc, "dir_count": dc})

            return node

        tree = _build(start, 0)
        tree["path"] = path or "/"
        return json.dumps(tree)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"vault_tree error: {e}")
        return json.dumps({"error": str(e)})


def vault_move(source: str, destination: str, create_dirs: bool = True) -> str:
    """Move a file or directory within the vault."""
    try:
        moved = move_path(source, destination, create_dirs=create_dirs)
        return json.dumps({"source": source, "destination": destination, "moved": moved})
    except ValueError as e:
        return json.dumps({"error": str(e), "source": source, "destination": destination})
    except Exception as e:
        logger.error(f"vault_move error: {e}")
        return json.dumps({"error": str(e), "source": source, "destination": destination})


def vault_delete(path: str, confirm: bool = False) -> str:
    """Delete a file by moving it to .trash/ in the vault."""
    if not confirm:
        return json.dumps({
            "error": "Set confirm=true to execute deletion. Files are moved to .trash/, not hard deleted.",
            "path": path,
        })

    try:
        deleted = delete_path(path)
        return json.dumps({"path": path, "deleted": deleted})
    except ValueError as e:
        return json.dumps({"error": str(e), "path": path})
    except Exception as e:
        logger.error(f"vault_delete error: {e}")
        return json.dumps({"error": str(e), "path": path})
