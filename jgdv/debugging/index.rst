.. -*- mode: ReST -*-

.. _debug:

=========
Debugging
=========

.. contents:: Contents

The package :ref:`jgdv.debugging` provides utilities to help with debugging memory allocations,
function timing, stack traces, capturing signals, and pyparsing DSLs.


-------
Mallocs
-------

Utilities for measuring memory usage.
See `MallocTool`, `LogDel`, and `LogDestruction`.


.. code:: python

    with MallocTool(frame_count=1) as dm:
        dm.whitelist(__file__)
        dm.blacklist("*.venv")
        val = 2
        dm.snapshot("before")
        vals = [random.random() for x in range(1000)]
        a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
        dm.snapshot("after")
        empty_dict = {"basic": [10, 20]}
        vals = None
        dm.snapshot("cleared")
          
    dm.compare("before", "after", filter=True, fullpath=False)

------
Timing
------

See `TimeCtx` and `TimeDec`. The first is a context manager timer, the second wraps it into
a decorator.

.. code:: python

    with TimeCtx() as obj:
        some_func()

    logging.info("The Function took: %s seconds", obj.total_s)
        
------
Traces
------

See `TraceContext` and its utility classes `TraceObj` and `TraceWriter`.
          
.. code:: python
          
    obj = TraceContext(targets=("call", "line", "return"),
                       targets=("trace","call","called"))
    with obj:
          other.do_something()

    obj.assert_called("package.module.class.method")
          

----------
Tracebacks
----------

See `TracebackFactory`. A Simple way of creating a traceback of frames,
using item access to allow a slice of available frames.

.. code:: python

    tb = TraceBuilder()
    raise Exception().with_traceback(tb[:])

-------
Signals
-------
See `SignalHandler` and it's default `NullHandler`.
`SignalHandler` traps SIGINT signals and handles them,
rather than exit the program.

---------
Debuggers
---------

See `RunningDebugger`.

-------------
DSL Debugging
-------------
`PyParsingDebuggerControl`.
