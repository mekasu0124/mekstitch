"""Thin wrapper around `QThreadPool` for fire-and-forget background work."""

from PySide6.QtCore import QThreadPool

from .async_worker import AsyncWorker


class AsyncHelper:
    def __init__(self):
        self.threadpool = QThreadPool.globalInstance()

    def run_async(self, fn, *args, **kwargs):
        worker = AsyncWorker(fn, *args, **kwargs)
        self.threadpool.start(worker)
        return worker
