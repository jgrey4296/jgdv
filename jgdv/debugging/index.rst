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
See :class:`MallocTool <jgdv.debugging.malloc_tool.MallocTool>`,
:func:`LogDel <jgdv.debugging.destruction.LogDel>`, and
:class:`LogDestruction<jgdv.debugging.destruction.LogDestruction>`.


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


Results in::
    
   [TraceMalloc]: --> Entering, tracking 1 frames
   [TraceMalloc]: Taking Snapshot: _init_          (Current: 0 B       , Peak: 0 B)
   [TraceMalloc]: Taking Snapshot: before          (Current: 584 B     , Peak: 632 B)
   [TraceMalloc]: Taking Snapshot: after           (Current: 32.2 KiB  , Peak: 32.3 KiB)
   [TraceMalloc]: Taking Snapshot: cleared         (Current: 16 B      , Peak: 16 B)
   [TraceMalloc]: Taking Snapshot: _final_         (Current: 0 B       , Peak: 0 B)
   [TraceMalloc]: <-- Exited, with 5 snapshots
   [TraceMalloc]: ---- Comparing (traceback): before -> after. Objects:2 ----
   [TraceMalloc]: (obj:0) +32.0 KiB       : vals = [random.random() for x in range(1000)]      (test_malloc_tool.py:130)
   [TraceMalloc]: (obj:1) +216 B          : a_dict = {"blah": 23, "bloo": set([1,2,3,4])}      (test_malloc_tool.py:131)
   [TraceMalloc]: -- Compare (2/2) --


------
Timing
------

See :class:`TimeCtx<jgdv.debugging.timing.TimeCtx>`
and :class:`TimeDec<jgdv.debugging.timing.TimeDec>`.
The first is a context manager timer, the second wraps it into
a decorator.

.. code:: python

    with TimeCtx() as obj:
        some_func()

    logging.info("The Function took: %s seconds", obj.total_s)
        

.. code:: python

   @TimeDec()
   def basic():
       time.sleep(10)
    
   basic()
   
Results in::

    Timed: basic took 10.005232 seconds
       
------
Traces
------

See :class:`TraceContext<jgdv.debugging.trace_context.TraceContext>` and its
utility classes :class:`TraceObj<jgdv.debugging.trace_context.TraceObj>` and
:class:`TraceWriter<jgdv.debugging.trace_context.TraceWriter>`.
          
.. code:: python
          
    obj = TraceContext(targets=("call", "line", "return"),
                       targets=("trace","call","called"))
    with obj:
          other.do_something()

    obj.assert_called("package.module.class.method")
          

    
----------
Tracebacks
----------

See :class:`TracebackFactory<jgdv.debugging.traceback_factory.TracebackFactory>`.
A Simple way of creating a traceback of frames,
using item access to allow a slice of available frames.

.. code:: python

    tb = TracebackFactory()
    raise Exception().with_traceback(tb[:])

    
-------
Signals
-------

See :class:`SignalHandler<jgdv.debugging.signal_handler.SignalHandler>` and it's
default :class:`NullHandler<jgdv.debugging.signal_handler.NullHandler>`.
``SignalHandler`` traps SIGINT signals and handles them,
rather than exit the program.
As `SignalHandler` is a a context manager, allows:
  
.. code:: python

   with SignalHandler():
        sys.exit(-1)

---------
Debuggers
---------

See :class:`RunningDebugger<jgdv.debugging.running_debugger.RunningDebugger>`.


-------------
DSL Debugging
-------------

:class:`PyParsingDebuggerControl<jgdv.debugging.dsl.PyParsingDebuggerControl>`.
