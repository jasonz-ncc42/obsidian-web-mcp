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
    """Return a compact tree view of the vault directory structure.

    Shows directories with file counts, keeping the output small.
    """
    try:
        vault_root = config.VAULT_PATH.resolve()
        start = resolve_vault_path(path) if path else vault_root
        if not start.is_dir():
            return json.dumps({"error": f"Not a directory: {path}"})

        depth = min(depth, 10)
        lines = []

        def _walk(dir_path, prefix, current_depth):
            if current_depth > depth:
                return
            try:
                entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                return

            dirs = []
            file_count = 0
            for entry in entries:
                if entry.name in config.EXCLUDED_DIRS:
                    continue
                if entry.is_dir():
                    dirs.append(entry)
                elif entry.is_file():
                    file_count += 1

            # Show file count for this directory
            if file_count > 0 and current_depth > 0:
                lines[-1] += f" ({file_count} files)" if lines else ""

            for i, d in enumerate(dirs):
                is_last = (i == len(dirs) - 1) and file_count == 0
                connector = "└── " if is_last or (i == len(dirs) - 1) else "├── "
                child_prefix = prefix + ("    " if is_last or (i == len(dirs) - 1) else "│   ")

                # Count files in this subdir
                sub_files = 0
                sub_dirs = 0
                try:
                    for child in d.iterdir():
                        if child.name in config.EXCLUDED_DIRS:
                            continue
                        if child.is_file():
                            sub_files += 1
                        elif child.is_dir():
                            sub_dirs += 1
                except PermissionError:
                    pass

                suffix = ""
                if sub_files > 0:
                    suffix = f" ({sub_files} files)"

                lines.append(f"{prefix}{connector}{d.name}/{suffix}")

                if current_depth < depth and sub_dirs > 0:
                    _walk(d, child_prefix, current_depth + 1)

        root_name = start.name if path else "vault"

        # Count root-level files
        root_files = sum(1 for f in start.iterdir()
                         if f.is_file() and f.name not in config.EXCLUDED_DIRS)
        root_suffix = f" ({root_files} files)" if root_files > 0 else ""
        lines.append(f"{root_name}/{root_suffix}")
        _walk(start, "", 0)

        return json.dumps({"tree": "\n".join(lines)})
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
