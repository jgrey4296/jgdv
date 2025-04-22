.. -*- mode: ReST -*-

.. _decorate:

==========
Decorators
==========

.. contents:: Contents


:ref:`jgdv.decorators` provides base classes for
more easily creating reusable decorators.
The core of this is the `DecoratorBase` class, which
detects whether a decorator is being applied to a function, method,
or class, and calls the appropriate method, `_wrap_fn`, `_wrap_method`, or `_wrap_fn`.
Use of `functools.wrap` is not needed, as the `DecoratorBase` handles that.

In addition, if the same decorator is applied repeatedly with different
data, that can be detected, and only a single decoration will be applied,
the data being added to the target's `__dict__`.

