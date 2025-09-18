from jgdv.debugging import TracebackFactory

tb = TracebackFactory()
raise Exception().with_traceback(tb[:])
