"""A `QRunnable` that runs a callable and reports back via signals."""

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

import traceback


class AsyncWorker(QRunnable):
    class Signals(QObject):
        started = Signal()
        finished = Signal(object)
        error = Signal(str)
        progress = Signal(int)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = self.Signals()
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        self.signals.started.emit()
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - reported to the caller
            self.signals.error.emit(f"{exc}\n{traceback.format_exc()}")
