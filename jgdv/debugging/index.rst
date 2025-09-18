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

.. include:: __examples/malloc_ex.py
   :code: python

Results in:
    
.. include:: __examples/malloc_result.txt
   :literal:


------
Timing
------

See :class:`TimeCtx<jgdv.debugging.timing.TimeCtx>`
and :class:`TimeDec<jgdv.debugging.timing.TimeDec>`.
The first is a context manager timer, the second wraps it into
a decorator.

.. include:: __examples/timectx_ex.py
   :code: python

.. include:: __examples/timedec_ex.py
   :code: python

   
Results in something like::

    Timed: basic took 10.005232 seconds
       
------
Traces
------

See :class:`TraceContext<jgdv.debugging.trace_context.TraceContext>` and its
utility classes :class:`TraceObj<jgdv.debugging.trace_context.TraceObj>` and
:class:`TraceWriter<jgdv.debugging.trace_context.TraceWriter>`.
          
.. include:: __examples/tracectx_ex.py
   :code: python


    
----------
Tracebacks
----------

See :class:`TracebackFactory<jgdv.debugging.traceback_factory.TracebackFactory>`.
A Simple way of creating a traceback of frames,
using item access to allow a slice of available frames.

.. include:: __examples/traceback_ex.py
   :code: python

    
-------
Signals
-------

See :class:`SignalHandler<jgdv.debugging.signal_handler.SignalHandler>` and it's
default :class:`NullHandler<jgdv.debugging.signal_handler.NullHandler>`.
``SignalHandler`` traps SIGINT signals and handles them,
rather than exit the program.
As `SignalHandler` is a a context manager, allows:
  
.. include:: __examples/signal_ex.py
   :code: python



---------
Debuggers
---------

See :class:`RunningDebugger<jgdv.debugging.running_debugger.RunningDebugger>`.


-------------
DSL Debugging
-------------

:class:`PyParsingDebuggerControl<jgdv.debugging.dsl.PyParsingDebuggerControl>`.
