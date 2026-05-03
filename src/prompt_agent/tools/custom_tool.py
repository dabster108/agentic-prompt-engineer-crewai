from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


DEFAULT_INCLUDE_GLOBS = [
    "**/*.py",
    "**/*.md",
    "**/*.yaml",
    "**/*.yml",
    "**/*.json",
    "**/*.toml",
    "**/*.txt",
    "**/*.js",
    "**/*.ts",
    "**/*.tsx",
    "**/*.jsx",
]

DEFAULT_EXCLUDE_GLOBS = [
    "**/.git/**",
    "**/.venv/**",
    "**/venv/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
]


class RepoContextInput(BaseModel):
    """Input schema for RepoContextTool."""

    goal: str = Field(..., description="Reason for collecting repo context.")
    include_globs: list[str] = Field(default_factory=list, description="Optional include globs.")
    exclude_globs: list[str] = Field(default_factory=list, description="Optional exclude globs.")
    max_files: int = Field(default=8, ge=1, le=40, description="Maximum files to return.")
    max_chars_per_file: int = Field(
        default=3000,
        ge=200,
        le=20000,
        description="Maximum characters per file excerpt.",
    )
    include_line_numbers: bool = Field(default=True, description="Prefix excerpts with line numbers.")


class RepoContextTool(BaseTool):
    name: str = "repo_context_tool"
    description: str = (
        "Collect curated repo context by reading a limited set of files using include/exclude globs. "
        "Returns JSON with paths and excerpts for prompt engineering context analysis."
    )
    args_schema: Type[BaseModel] = RepoContextInput

    def _resolve_root(self) -> Path:
        override = os.getenv("PROMPTFORGE_REPO_ROOT", "").strip()
        if override:
            return Path(override).resolve()

        try:
            return Path(__file__).resolve().parents[3]
        except IndexError:
            return Path.cwd().resolve()

    def _match_any(self, path: str, patterns: list[str]) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

    def _collect_files(self, root: Path, include_globs: list[str], exclude_globs: list[str]) -> list[Path]:
        include_patterns = include_globs or DEFAULT_INCLUDE_GLOBS
        exclude_patterns = DEFAULT_EXCLUDE_GLOBS + exclude_globs
        matched: set[Path] = set()

        for pattern in include_patterns:
            for file_path in root.glob(pattern):
                if not file_path.is_file():
                    continue
                relative = file_path.relative_to(root).as_posix()
                if self._match_any(relative, exclude_patterns):
                    continue
                matched.add(file_path)

        return sorted(matched)

    def _read_excerpt(self, file_path: Path, max_chars: int, include_line_numbers: bool) -> tuple[str, bool]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if include_line_numbers:
            lines = text.splitlines()
            text = "\n".join(f"{index + 1:04d}: {line}" for index, line in enumerate(lines))
        truncated = len(text) > max_chars
        return text[:max_chars], truncated

    def _run(
        self,
        goal: str,
        include_globs: list[str] | None = None,
        exclude_globs: list[str] | None = None,
        max_files: int = 8,
        max_chars_per_file: int = 3000,
        include_line_numbers: bool = True,
    ) -> str:
        root = self._resolve_root()
        include_globs = include_globs or []
        exclude_globs = exclude_globs or []
        files = self._collect_files(root, include_globs, exclude_globs)

        payload = {
            "tool": self.name,
            "goal": goal,
            "root": root.as_posix(),
            "files": [],
            "skipped": [],
        }

        for file_path in files[:max_files]:
            excerpt, truncated = self._read_excerpt(file_path, max_chars_per_file, include_line_numbers)
            payload["files"].append(
                {
                    "path": file_path.relative_to(root).as_posix(),
                    "excerpt": excerpt,
                    "truncated": truncated,
                }
            )

        if len(files) > max_files:
            payload["skipped"].append(
                {
                    "reason": "max_files_limit",
                    "count": len(files) - max_files,
                }
            )

        return json.dumps(payload, ensure_ascii=True)
