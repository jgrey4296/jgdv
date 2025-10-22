"""
Utilities for debugging.

Provides:

#. SignalHandler     : For installing handlers for interrupts
#. TimeCtx           : A CtxManager for simple timing
#. TimeDec           : A Decorator to time functions
#. TracebackFactory  : For slicing the traceback provided in exceptions
#. TraceContext      : A CtxManager for tracing function calls.
#. MallocTool        : For profiling memory usage.
#. LogDel            : A class decorator for logging when __del__ is called

"""
from .signal_handler import SignalHandler, NullHandler
from .traceback_factory import TracebackFactory
from .traceback_factory import TracebackFactory as TraceBuilder
from .destruction import LogDel
