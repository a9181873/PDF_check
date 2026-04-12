from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock

from models.diff_models import DiffReport


@dataclass
class TaskState:
    status: str
    progress_percent: int
    current_step: str
    error_message: str | None = None
    result: DiffReport | None = None


class InMemoryTaskStore:
    def __init__(self):
        self._tasks: dict[str, TaskState] = {}
        self._lock = Lock()

    def create(self, task_id: str) -> TaskState:
        state = TaskState(status="parsing", progress_percent=0, current_step="queued")
        with self._lock:
            self._tasks[task_id] = state
        return state

    def get(self, task_id: str) -> TaskState | None:
        with self._lock:
            return self._tasks.get(task_id)

    def update(self, task_id: str, updater: Callable[[TaskState], None]) -> TaskState | None:
        with self._lock:
            state = self._tasks.get(task_id)
            if not state:
                return None
            updater(state)
            return state


TASK_STORE = InMemoryTaskStore()
