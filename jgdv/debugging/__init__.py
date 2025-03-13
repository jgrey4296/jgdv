"""

jgdv.debugging : Utilities for debugging

Provides:
- SignalHandler      : for installing handlers for interrupts
- TimeBlock_ctx      : CtxManager for simple timing
- MultiTimeBlock_ctx : for more complicated timing
- TraceBuilder       : for slicing the traceback provided in exceptions

"""
from .signal_handler import SignalHandler
from .trace_builder import TraceBuilder
from .timeblock_ctx import TimeBlock_ctx
from .multi_time_block import MultiTimeBlock_ctx
