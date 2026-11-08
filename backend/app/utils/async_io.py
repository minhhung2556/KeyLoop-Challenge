from collections.abc import Callable
from typing import TypeVar

import anyio

T = TypeVar("T")


async def run_in_thread(fn: Callable[[], T]) -> T:
    return await anyio.to_thread.run_sync(fn)
