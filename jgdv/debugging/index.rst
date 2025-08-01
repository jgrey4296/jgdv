.. -*- mode: ReST -*-

.. _debug:

=========
Debugging
=========

.. contents:: Contents

This :ref:`package<jgdv.debugging>` provides utilities to help with debugging memory allocations,
function timing, stack traces, capturing signals, and pyparsing DSLs.

-------
Mallocs
-------

Utilities for measuring memory usage.
See :ref:`MallocTool<jgdv.debugging.malloc_tool.MallocTool>`, :func:`LogDel<jgdv.debugging.destruction.LogDel>`, and :ref:`LogDestruction<jgdv.debugging.destruction.LogDestruction>`.


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

See :ref:`TimeCtx<jgdv.debugging.timing.TimeCtx>` and :ref:`TimeDec<jgdv.debugging.timing.TimeDec>`. The first is a context manager timer, the second wraps it into
a decorator.

.. code:: python

    with TimeCtx() as obj:
        some_func()

    logging.info("The Function took: %s seconds", obj.total_s)
        
------
Traces
------

See :ref:`TraceContext<jgdv.debugging.trace_context.TraceContext>` and its utility classes :ref:`TraceObj<jgdv.debugging.trace_context.TraceObj>` and :ref:`TraceWriter<jgdv.debugging.trace_context.TraceWriter>`.
          
.. code:: python
          
    obj = TraceContext(targets=("call", "line", "return"),
                       targets=("trace","call","called"))
    with obj:
          other.do_something()

    obj.assert_called("package.module.class.method")
          

----------
Tracebacks
----------

See :ref:`TracebackFactory<jgdv.debugging.traceback_factory.TracebackFactory>`. A Simple way of creating a traceback of frames,
using item access to allow a slice of available frames.

.. code:: python

    tb = TracebackFactory()
    raise Exception().with_traceback(tb[:])

    
-------
Signals
-------

See :ref:`SignalHandler<jgdv.debugging.signal_handler.SignalHandler>` and it's default :ref:`NullHandler<jgdv.debugging.signal_handler.NullHandler>`.
``SignalHandler`` traps SIGINT signals and handles them,
rather than exit the program.


---------
Debuggers
---------

See :ref:`RunningDebugger<jgdv.debugging.running_debugger.RunningDebugger>`.


-------------
DSL Debugging
-------------

:ref:`PyParsingDebuggerControl<jgdv.debugging.dsl.PyParsingDebuggerControl>`.
