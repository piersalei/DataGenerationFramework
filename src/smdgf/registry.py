"""Task registry for canonical contract definitions."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from smdgf.schemas.task import TaskDefinition


class TaskRegistry:
    """In-memory registry for task definitions."""

    def __init__(self, tasks: Optional[Iterable[TaskDefinition]] = None) -> None:
        self._tasks: dict[str, TaskDefinition] = {}
        for task in tasks or ():
            self.register(task)

    def register(self, task: TaskDefinition) -> None:
        if task.task_id in self._tasks:
            raise ValueError(f"duplicate task_id: {task.task_id}")
        self._tasks[task.task_id] = task

    def get(self, task_id: str) -> TaskDefinition:
        return self._tasks[task_id]

    def list(self) -> list[TaskDefinition]:
        return [self._tasks[key] for key in sorted(self._tasks)]

    def clear(self) -> None:
        self._tasks.clear()
