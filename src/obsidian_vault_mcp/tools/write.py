"""Write tools for the Obsidian vault MCP server."""

import json
import logging

from ..vault import resolve_vault_path, read_file, write_file_atomic

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


def vault_patch(path: str, old_text: str, new_text: str) -> str:
    """Replace a unique text occurrence in a file. Fails if old_text is not found or matches multiple times."""
    try:
        content, _ = read_file(path)
        count = content.count(old_text)
        if count == 0:
            return json.dumps({"error": "old_text not found in file", "path": path})
        if count > 1:
            return json.dumps({
                "error": f"old_text matches {count} times — provide more context to make it unique",
                "path": path,
            })
        new_content = content.replace(old_text, new_text, 1)
        _, size = write_file_atomic(path, new_content, create_dirs=False)
        return json.dumps({"path": path, "patched": True, "size": size})
    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {path}", "path": path})
    except ValueError as e:
        return json.dumps({"error": str(e), "path": path})
    except Exception as e:
        logger.error(f"vault_patch error for {path}: {e}")
        return json.dumps({"error": str(e), "path": path})


def vault_append(path: str, content: str, create_if_missing: bool = False) -> str:
    """Append content to the end of a file. Adds a newline before appending if the file doesn't end with one."""
    try:
        try:
            existing, _ = read_file(path)
            if existing and not existing.endswith("\n"):
                content = "\n" + content
            new_content = existing + content
        except FileNotFoundError:
            if not create_if_missing:
                return json.dumps({"error": f"File not found: {path}", "path": path})
            new_content = content

        _, size = write_file_atomic(path, new_content, create_dirs=create_if_missing)
        return json.dumps({"path": path, "appended": True, "size": size})
    except ValueError as e:
        return json.dumps({"error": str(e), "path": path})
    except Exception as e:
        logger.error(f"vault_append error for {path}: {e}")
        return json.dumps({"error": str(e), "path": path})
