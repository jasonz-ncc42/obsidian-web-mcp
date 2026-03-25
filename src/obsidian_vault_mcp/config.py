import os
from pathlib import Path

# Vault configuration
VAULT_PATH = Path(os.environ.get("VAULT_PATH", os.path.expanduser("~/Obsidian/MyVault")))
VAULT_MCP_TOKEN = os.environ.get("VAULT_MCP_TOKEN", "")
VAULT_MCP_PORT = int(os.environ.get("VAULT_MCP_PORT", "8420"))
VAULT_MCP_HOST = os.environ.get("VAULT_MCP_HOST", "0.0.0.0")
VAULT_ALLOWED_HOSTS = os.environ.get("VAULT_ALLOWED_HOSTS", "")

# OAuth 2.0 client credentials (used by Claude desktop/mobile integration)
VAULT_OAUTH_CLIENT_ID = os.environ.get("VAULT_OAUTH_CLIENT_ID", "vault-mcp-client")
VAULT_OAUTH_CLIENT_SECRET = os.environ.get("VAULT_OAUTH_CLIENT_SECRET", "")

# Synology FileStation API (optional — enables Drive sync notification on writes)
# Set all three to enable; if any is empty, falls back to direct disk writes.
SYNO_HOST = os.environ.get("SYNO_HOST", "")  # e.g., "localhost" or NAS IP
SYNO_PORT = int(os.environ.get("SYNO_PORT", "5001"))
SYNO_USER = os.environ.get("SYNO_USER", "")
SYNO_PASS = os.environ.get("SYNO_PASS", "")
SYNO_VAULT_PATH = os.environ.get("SYNO_VAULT_PATH", "")  # FileStation path, e.g., "/homes/Jason/Drive/..."
SYNO_ENABLED = bool(SYNO_HOST and SYNO_USER and SYNO_PASS and SYNO_VAULT_PATH)

# Safety limits
MAX_CONTENT_SIZE = 1_000_000  # 1MB max write size
MAX_BATCH_SIZE = 20           # Max files per batch operation
MAX_SEARCH_RESULTS = 50       # Max results per search
DEFAULT_SEARCH_RESULTS = 20
MAX_LIST_DEPTH = 5            # Max directory recursion depth
CONTEXT_LINES = 2             # Default lines of context in search results

# Directories to never expose or modify
EXCLUDED_DIRS = {".obsidian", ".trash", ".git", ".DS_Store"}

