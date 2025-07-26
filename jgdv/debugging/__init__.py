"""

jgdv.debugging : Utilities for debugging

Provides:
- SignalHandler      : for installing handlers for interrupts
- TimeBlock_ctx      : CtxManager for simple timing
- MultiTimeBlock_ctx : for more complicated timing
- TraceBuilder       : for slicing the traceback provided in exceptions
- LogDel             : a class decorator for logging when __del__ is called

"""
from .signal_handler import SignalHandler, NullHandler
from .traceback_factory import TracebackFactory
from .traceback_factory import TracebackFactory as TraceBuilder
from .log_del import LogDel
