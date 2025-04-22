.. -*- mode: ReST -*-

.. _logging:

=======
Logging
=======

.. contents:: Contents


:ref:`jgdv.logging` provides a `JGDVLogConfig` which sets up
various loggers, using log specs able to be defined in `TOML`.
Also provided are a `Formatter` for adding colour to stdout,
some `Filter` classes, and a `StackFormatter_m` mixin, using `stackprinter`
to print error stack traces a bit nicer.



New Logging Levels
==================

After reading Nicole Tietz's
`The only two log levels you need are info and error <tieztpost_>`_,
I prefer a different log level hierarchy than the default `Python Levels <pyLogLevels_>`_.
They are, from highest to lowest:


1. Error  : For when things go really wrong.
2. User   : Things the user should see.
3. Trace  : Landmarks to track program execution paths.
4. Detail : Actual values for use in debuggging.

and

5. Bootstrap : For before the logging is fully set up.
   


.. Links
.. _tieztpost: https://ntietz.com/blog/the-only-two-log-levels-you-need-are-info-and-error/

.. _pyLogLevels: https://docs.python.org/3/library/logging.html#logging-levels
