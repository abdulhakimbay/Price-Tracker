"""Utilities for running async code from synchronous Celery tasks."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar


T = TypeVar("T")


class AsyncTaskRunner:
    """Keep one dedicated event loop for synchronous worker code."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="celery-async-runner",
            daemon=True,
        )
        self._thread.start()

    def _run_loop(self) -> None:
        """Start the dedicated event loop in a background thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coroutine: Coroutine[Any, Any, T]) -> T:
        """Execute a coroutine on the dedicated event loop and wait for the result."""
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return future.result()


async_task_runner = AsyncTaskRunner()
