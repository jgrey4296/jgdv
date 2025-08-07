.. -*- mode: ReST -*-

.. _logging:

=======
Logging
=======

.. contents:: Contents


:mod:`Logging<jgdv.logging>` provides:
     
1. :class:`JGDVLogConfig <jgdv.logging.config.JGDVLogConfig>`, which sets up various loggers, using ``TOML`` defined specs.
2. :class:`ColourFormatter <jgdv.logging.format.colour.ColourFormatter>` for adding colour to stdout,
3. :mod:`Filters <jgdv.logging.filter>`,
4. A :class:`StackFormatter_m <jgdv.logging.format.stack_m.StackFormatter_m>` mixin, using `stackprinter`_ for simplifying the formatting of logging, to print error stack traces a bit nicer.

   
----------
Toml Specs
----------

.. code:: toml

    [logging]
    [logging.stream]
    level   = "user"
    filter  = []
    target  = "stdout"
    format  = "{levelname:<8}  : {message}"
    
    [logging.file]
    level        = "trace"
    filter       = []
    target       = "rotate"
    format       = "{levelname:<8} : {message:<20} :|: ({module}.{lineno}.{funcName})"
    filename_fmt = "doot.log"
    
    [logging.printer]
    level        = "NOTSET"
    colour       = true
    target       = ["stdout", "rotate"]
    format       = "{message}"
    filename_fmt = "doot_printed.log"
    
    [logging.extra]


.. code:: python

    # TODO

There are 4 key sorts of ``Toml`` specified loggers:
1. The `stream` logger, for logging messages that escalate to output on ``stdout`` or ``stderr``.
2. The `file` logger, for all messages, which will be written to a file.
3. The `printer` logger, a replacement for ``print``. ie: It is what the user sees during normal operation, but in a way the logging architecture can control it rather than straight ``print``ing to ``stdout``.
4. `extra` loggers. These are for customising the logger of any module you want. eg: ``jgdv.decorators``, or ``sphinx``, or ``networkx.digraph``.
   
--------------
The Log Config
--------------

The :class:`~jgdv.logging.config.JGDVLogConfig` is for taking loaded ``TOML`` specs of loggers, and applying them.

.. code:: python
          
   from jgdv.structs.chainguard import ChainGuard
   from jgdv.logging import JGDVLogConfig

   data    = ChainGuard.load(Path("data/specs.toml"))
   config  = JGDVLogConfig()
   config.setup(data)
   config.set_level("DEBUG")
   
   
    
-----------------------
Personal Logging Levels
-----------------------

After reading Nicole Tietz's
`The only two log levels you need are info and error <tieztpost_>`_,
I prefer a different log level hierarchy than the default `Python Levels <pyLogLevels_>`_.
They are, from highest to lowest:


1. ``Error``  : For when things go really wrong.
2. ``User``   : Things the user should see.
3. ``Trace``  : Landmarks to track program execution paths.
4. ``Detail`` : Actual values for use in debuggging.

and

5. ``Bootstrap`` : For before the logging is fully set up.
   


.. Links
.. _tieztpost: https://ntietz.com/blog/the-only-two-log-levels-you-need-are-info-and-error/

.. _pyLogLevels: https://docs.python.org/3/library/logging.html#logging-levels

.. _stackprinter: https://github.com/cknd/stackprinter
