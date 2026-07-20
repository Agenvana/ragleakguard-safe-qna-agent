"""Local file iteration for pre-ingestion scans. Read-only, text-like files."""
import os
from typing import Iterator

TEXT_EXTS = {
    ".txt", ".md", ".markdown", ".rst", ".csv", ".tsv", ".json", ".jsonl",
    ".log", ".html", ".htm", ".xml", ".yaml", ".yml",
}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode"}
MAX_BYTES = 2_000_000  # per-file read cap


def iter_text_files(root: str, max_files: int = 500) -> Iterator[str]:
    """Yield text-like files under root. A single-file root is yielded as-is
    (explicit paths are trusted regardless of extension)."""
    if os.path.isfile(root):
        yield root
        return
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in TEXT_EXTS:
                yield os.path.join(dirpath, name)
                count += 1
                if count >= max_files:
                    return


def read_text(path: str) -> str:
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES)
    return data.decode("utf-8", errors="replace")
