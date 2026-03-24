"""Pydantic input models for obsidian-vault-mcp tool endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from .config import (
    CONTEXT_LINES,
    DEFAULT_SEARCH_RESULTS,
    MAX_BATCH_SIZE,
    MAX_CONTENT_SIZE,
    MAX_LIST_DEPTH,
    MAX_SEARCH_RESULTS,
)


class VaultReadInput(BaseModel):
    """Read a single file from the vault."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        ...,
        description="Relative path from vault root (e.g. 'projects/acme/notes.md')",
        min_length=1,
        max_length=500,
    )


class VaultWriteInput(BaseModel):
    """Write or overwrite a file in the vault."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        ...,
        description="Relative path from vault root",
        min_length=1,
        max_length=500,
    )
    content: str = Field(
        ...,
        description="Full file content to write",
        max_length=MAX_CONTENT_SIZE,
    )
    create_dirs: bool = Field(
        default=True,
        description="Create parent directories if they don't exist",
    )


class VaultListInput(BaseModel):
    """List files and directories under a vault path."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        default="",
        description="Relative directory path from vault root; empty string for root",
        max_length=500,
    )
    depth: int = Field(
        default=1,
        ge=1,
        le=MAX_LIST_DEPTH,
        description="How many levels deep to recurse",
    )
    include_files: bool = Field(
        default=True,
        description="Include files in the listing",
    )
    include_dirs: bool = Field(
        default=True,
        description="Include directories in the listing",
    )
    pattern: str | None = Field(
        default=None,
        description="Optional glob pattern to filter results (e.g. '*.md')",
        max_length=100,
    )


class VaultMoveInput(BaseModel):
    """Move or rename a file/directory within the vault."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source: str = Field(
        ...,
        description="Current relative path of the file or directory",
        min_length=1,
        max_length=500,
    )
    destination: str = Field(
        ...,
        description="New relative path for the file or directory",
        min_length=1,
        max_length=500,
    )
    create_dirs: bool = Field(
        default=True,
        description="Create destination parent directories if they don't exist",
    )


class VaultDeleteInput(BaseModel):
    """Delete a file from the vault."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        ...,
        description="Relative path of the file to delete",
        min_length=1,
        max_length=500,
    )
    confirm: bool = Field(
        ...,
        description="Must be true to execute deletion -- safety gate to prevent accidental deletes",
    )


class VaultSearchInput(BaseModel):
    """Full-text search across vault files."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ...,
        description="Search string to find in file contents",
        min_length=1,
        max_length=200,
    )
    path_prefix: str | None = Field(
        default=None,
        description="Limit search to files under this directory prefix",
        max_length=500,
    )
    file_pattern: str = Field(
        default="*.md",
        description="Glob pattern for files to search (e.g. '*.md', '*.canvas')",
        max_length=50,
    )
    max_results: int = Field(
        default=DEFAULT_SEARCH_RESULTS,
        ge=1,
        le=MAX_SEARCH_RESULTS,
        description="Maximum number of matching files to return",
    )
    context_lines: int = Field(
        default=CONTEXT_LINES,
        ge=0,
        le=10,
        description="Number of lines of context to show around each match",
    )


class VaultBatchReadInput(BaseModel):
    """Read multiple vault files in a single request."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    paths: list[str] = Field(
        ...,
        description="List of relative paths to read",
        min_length=1,
        max_length=MAX_BATCH_SIZE,
    )
    include_content: bool = Field(
        default=True,
        description="If false, return metadata only (size, modified) without file body",
    )


