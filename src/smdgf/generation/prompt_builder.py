"""Modular prompt builder: merges base template with task-specific fragments."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SUPPORTED_FORMATS = ("mcq", "mcq_multi", "judge", "qa", "open_qa")


class PromptBuilder:
    """Build a complete prompt by merging a base template with a task fragment.

    File layout expected::

        prompts/
            templates/
                base_{format}.txt   # framework-level boilerplate per format
            {task_id}/
                fragment_{format}.txt  # human-authored few-shot examples per format

    Usage::

        builder = PromptBuilder(Path("prompts"))
        prompt = builder.build("emotion.contrasting", format="mcq")
        prompt = builder.build("emotion.contrasting", format="qa")
        prompt = builder.build("emotion.contrasting", format="open_qa")
    """

    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = Path(prompts_dir)

    def build(
        self,
        task_id: str,
        format: str = "mcq",
        context: dict[str, Any] | None = None,
    ) -> str:
        """Merge base template with task fragment.

        Args:
            task_id: subdirectory under prompts/ that holds the fragment.
            format: one of "mcq", "qa", "open_qa" — selects the base template.
            context: optional dict of ``{{key}}`` → ``value`` substitutions.
        """
        if format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}. Choose from {SUPPORTED_FORMATS}.")

        base_path = self.prompts_dir / "templates" / f"base_{format}.txt"
        fragment_path = self.prompts_dir / task_id / f"fragment_{format}.txt"

        base_text = base_path.read_text(encoding="utf-8")
        fragment_text = fragment_path.read_text(encoding="utf-8")

        merged = base_text.replace("{{fragment}}", fragment_text)

        if context:
            for key, value in context.items():
                merged = merged.replace(f"{{{{{key}}}}}", str(value))

        return merged

    def list_tasks(self) -> list[str]:
        """Return all task IDs that have at least one fragment file."""
        tasks: list[str] = []
        for item in self.prompts_dir.iterdir():
            if item.is_dir() and any(
                f.name.startswith("fragment_") and f.suffix == ".txt"
                for f in item.iterdir()
                if f.is_file()
            ):
                tasks.append(item.name)
        return sorted(tasks)

    def list_formats(self) -> list[str]:
        """Return all supported output formats."""
        return list(SUPPORTED_FORMATS)
