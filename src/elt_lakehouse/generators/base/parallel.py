from __future__ import annotations

import multiprocessing as mp
import os
import random
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import pyarrow as pa

MAX_DEFAULT_WORKERS = 8

""" 
Note:
Run CPU-bound generators in seeded, ordered, memory-bounded processes.

Workers return Arrow tables; the parent writes them. Configure with
GENERATOR_WORKERS, GENERATOR_START_METHOD, and GENERATOR_SEED.
"""

def worker_count() -> int:
    """Number of worker processes to use (1 means run in this process)."""
    raw = os.environ.get("GENERATOR_WORKERS")
    if raw:
        return max(1, int(raw))
    cores = os.cpu_count() or 1
    return max(1, min(cores - 2, MAX_DEFAULT_WORKERS))



def base_seed() -> int:
    """Base seed for one run: from ``GENERATOR_SEED`` or fresh OS entropy."""
    raw = os.environ.get("GENERATOR_SEED")
    if raw:
        return int(raw)
    return int.from_bytes(os.urandom(8), "big")


def chunk_seed(base: int, index: int) -> int:
    """Distinct, stable seed for chunk ``index`` of a run."""
    return (base * 1_000_003 + index * 7_919 + 12_345) % (2**63)


def split_counts(total: int, chunk_size: int) -> list[int]:
    """Split ``total`` rows into chunk sizes of at most ``chunk_size``."""
    full, rest = divmod(total, chunk_size)
    return [chunk_size] * full + ([rest] if rest else [])


def rows_to_table(rows: list[dict]) -> pa.Table:
    return pa.Table.from_pylist(rows)


def _context() -> mp.context.BaseContext:
    # fork keeps the already-imported modules (distributions, config, logging);
    # spawn is the fallback where fork does not exist (Windows). Set
    # GENERATOR_START_METHOD=spawn if fork ever hangs in a threaded parent.
    method = os.environ.get("GENERATOR_START_METHOD")
    if not method:
        method = "fork" if "fork" in mp.get_all_start_methods() else "spawn"
    return mp.get_context(method)


def map_chunks(
    fn: Callable[[Any], Any],
    tasks: Iterable[Any],
    *,
    initializer: Callable[..., None] | None = None,
    initargs: tuple = (),
    workers: int | None = None,
) -> Iterator[Any]:
    """Yield ``fn(task)`` for every task, in task order, using worker processes.

    ``fn`` and ``initializer`` must be module-level functions. ``tasks`` is
    consumed lazily, so a generator of tasks keeps memory bounded.
    """
    workers = workers or worker_count()
    if workers <= 1:
        if initializer is not None:
            initializer(*initargs)
        for task in tasks:
            yield fn(task)
        return

    window = workers * 2
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=_context(),
        initializer=initializer,
        initargs=initargs,
    ) as executor:
        pending: deque = deque()
        for task in tasks:
            pending.append(executor.submit(fn, task))
            if len(pending) >= window:
                yield pending.popleft().result()
        while pending:
            yield pending.popleft().result()


def seed_this_process(seed: int) -> None:
    """Seed the ``random`` module for one chunk."""
    random.seed(seed)
