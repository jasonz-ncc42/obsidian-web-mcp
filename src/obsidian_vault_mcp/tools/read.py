"""Read tools for the Obsidian vault MCP server."""

import json
import logging
import re

from ..vault import resolve_vault_path, read_file

logger = logging.getLogger(__name__)

# Regex to extract YAML frontmatter block (between --- markers at file start)
_FM_PATTERN = re.compile(r"\A---\r?\n(.*?\r?\n)---\r?\n", re.DOTALL)


def _extract_frontmatter(content: str) -> str | None:
    """Extract raw YAML frontmatter text from file content.

    Returns the raw YAML string (without --- delimiters), or None if no frontmatter.
    Never parses or reformats — returns exactly what's in the file.
    """
    match = _FM_PATTERN.match(content)
    if not match:
        return None
    return match.group(1).rstrip("\n")


def vault_read(path: str) -> str:
    """Read a file from the vault. Returns raw content, file metadata, and parsed frontmatter."""
    try:
        resolve_vault_path(path)
        content, metadata = read_file(path)

        return json.dumps({
            "path": path,
            "content": content,
            "metadata": metadata,
            "frontmatter": _extract_frontmatter(content),
        })
    except ValueError as e:
        return json.dumps({"error": str(e), "path": path})
    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {path}", "path": path})
    except Exception as e:
        logger.error(f"vault_read error for {path}: {e}")
        return json.dumps({"error": str(e), "path": path})


def vault_batch_read(paths: list[str], include_content: bool = True) -> str:
    """Read multiple files from the vault in one call."""
    results = []
    found = 0
    missing = 0

    for path in paths:
        try:
            content, metadata = read_file(path)

            entry = {
                "path": path,
                "metadata": metadata,
                "frontmatter": _extract_frontmatter(content),
            }
            if include_content:
                entry["content"] = content

            results.append(entry)
            found += 1
        except (ValueError, FileNotFoundError) as e:
            results.append({"path": path, "error": str(e)})
            missing += 1
        except Exception as e:
            results.append({"path": path, "error": str(e)})
            missing += 1

    return json.dumps({"files": results, "found": found, "missing": missing})
