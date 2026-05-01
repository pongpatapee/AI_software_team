from __future__ import annotations

from pathlib import Path


def inspect_target_project(target_project: Path) -> str:
    """Return a structured summary of Target Project files for the Architect Agent."""
    resolved = target_project.resolve()
    files = sorted(
        str(path.relative_to(resolved))
        for path in resolved.rglob("*")
        if path.is_file() and not _is_hidden(path, resolved)
    )
    if not files:
        return "No files found in target project."
    file_list = "\n".join(f"  - {f}" for f in files)
    return f"Files ({len(files)} total):\n{file_list}"


def _is_hidden(path: Path, root: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(root).parts)
