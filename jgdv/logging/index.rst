.. -*- mode: ReST -*-

.. _logging:

=======
Logging
=======

.. contents:: Contents


:mod:`jgdv.logging.config` provides a :class:`JGDVLogConfig <jgdv.logging.config.JGDVLogConfig>`
which sets up various loggers, using log specs able to be defined in `TOML`.
Also provided are a :class:`ColourFormatter <jgdv.logging.format.colour.ColourFormatter>` for adding colour to stdout,
some :mod:`Filters <jgdv.logging.filter>`, and a :class:`StackFormatter_m <jgdv.logging.format.stack_m.StackFormatter_m>` mixin, using `stackprinter`_
to print error stack traces a bit nicer.




Personal Logging Levels
=======================

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

.. _stackprinter: https://github.com/cknd/stackprinter
