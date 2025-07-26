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

See `JGDVTimer`, `TrackTime`, `TimeBlock_ctx`, and `MultiTimeBlock_ctx`.

------
Traces
------

See `TraceBuilder`, and `TraceContext`.
`TraceBuilder` manually builds a `Traceback` stack,
in place of the overly verbose default `Exception` tracebacks.
Meanwhile `TraceContext` runs an execution trace.

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

`RunningDebugger`.

-------------
DSL Debugging
-------------
`PyParsingDebuggerControl`.
