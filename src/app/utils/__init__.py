"""Background-work helpers.

Identical in spirit to Momentum's `app/utils`: heavy or blocking work (image
import, chart export) can be pushed off the GUI thread and the result delivered
back through Qt signals.
"""

from .async_helper import AsyncHelper
from .async_worker import AsyncWorker

__all__ = ["AsyncHelper", "AsyncWorker"]
