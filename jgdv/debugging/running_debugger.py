# adapted from https://stackoverflow.com/questions/50691169
import logging as logmod
import sys
from bdb import Breakpoint
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)

logging      = logmod.getLogger(__name__)
trace_logger = logmod.getLogger('dejavu._debug')

class RunningDebugger(metaclass=SingletonMeta):
    """
      The usual debugger stops execution when you call it.
      This starts the tracing, without pausing execution.
      so on a future breakpoint, you can pause and have a trace from where you started the debugger
    """

    def __init__(self):
        super().__init__()
        self.running = False

    def __bool__(self):
        return self.running

    def precmd(self, line):
        trace_logger.info("[db]>>> " + line)
        return line

    def do_help(self, *args):
        print("Acab Debugger Help")
        super().do_help(*args)


    def set_running_trace(self, frame=None):
        """ Start debugging from frame, without pausing execution.
        This is to allow setting a future breakpoint, without having
        to enter the debugger and exit again.
        """
        self.running = True
        if frame is None:
            frame = sys._getframe().f_back
        self.reset()
        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
        self.set_continue()
        sys.settrace(self.trace_dispatch)

    def set_trace(self, frame=None):
        """Start debugging from frame.

        If frame is not specified, debugging starts from caller's frame.
        """
        self.running = True
        if frame is None:
            frame = sys._getframe().f_back
        # removed "reset" here.
        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
        self.set_step()
        sys.settrace(self.trace_dispatch)
