"""Read tools for the Obsidian vault MCP server."""

import json
import logging
import re

from .. import config
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


def vault_context() -> str:
    """Return all Claude Code context files from the vault: CLAUDE.md and .claude/**/*.md.

    Designed to be called once at session start so Claude Code has full
    project context without multiple round-trips.
    """
    vault_root = config.VAULT_PATH.resolve()
    files = []

    # Collect CLAUDE.md at vault root
    claude_md = vault_root / "CLAUDE.md"
    if claude_md.is_file():
        files.append(claude_md)

    # Collect all .md files under .claude/
    claude_dir = vault_root / ".claude"
    if claude_dir.is_dir():
        for md_file in sorted(claude_dir.rglob("*.md")):
            if md_file.is_file():
                files.append(md_file)

    results = []
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8")
            rel_path = str(fp.relative_to(vault_root))
            results.append({
                "path": rel_path,
                "content": content,
            })
        except Exception as e:
            rel_path = str(fp.relative_to(vault_root))
            results.append({"path": rel_path, "error": str(e)})

    return json.dumps({"files": results, "count": len(results)})
