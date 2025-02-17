.. -*- mode: ReST -*-

.. _debug:

=========
Debugging
=========

.. contents:: Contents

The package :ref:`jgdv.debugging` provides two main classes,
`SignalHandler` and `TraceBuilder`.

`SignalHandler` traps SIGINT signals and handles them,
rather than exit the program.
While `TraceBuilder` manually builds a `Traceback` stack,
in place of the overly verbose default `Exception` tracebacks.
