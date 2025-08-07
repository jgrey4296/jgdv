.. -*- mode: ReST -*-

.. _decorate:

==========
Decorators
==========

.. contents:: Contents


:ref:`decorators<jgdv.decorators>` provides base classes for
creating reusable decorators.
The core of this is the :class:`Decorator<jgdv.decorators._core.Decorator>` class, which
detects whether a decorator is being applied to a function, method,
or class, and calls the appropriate method, ``_wrap_fn_h``, ``_wrap_method_h``, or ``_wrap_fn_h``. These preserve type variables
by using the stdlib's `ParamSpec`_.

Use of ``functools.wrap`` is not needed, as the ``Decorator`` handles that.

In addition, if the same decorator is applied repeatedly with different
data, that can be detected, and only a single decoration will be applied,
the data being added to the target's ``__dict__``.

.. code:: python

    from jgdv.decorators import Decorator

    class MyDecorator(Decorator):

        def _wrap_fn_h[**In](self, fn:Func[In, int]) -> Decorated[In, int|None]:

            def myfunc(*vals:In.args) -> int|None:
                if bool(vals[0]):
                    return fn(*vals)
                return None

            return myfunc

.. code:: python

    @MyDecorator()
    def a_func(val:int) -> int:
          return 2

    assert(a_func(0) is None)
    assert(a_func(5) is 2)
    

Specialised Decorators
======================

The Point of this module is to create certain decorator tools to
simplify certain styles of decorators, such as:

* Monotonic Decorators, that intentionally stack.
* Idempotent Decorators, that only apply to a function once.
* Metadata Decorators, that only add annotations without changing runtime behaviour.
* Data Decorators, that update function data for an idempotent decorator to work with.
  
One example is the ``@DKeyed`` decorator in :ref:`jgdv.structs.dkey`.
This adds key data to a function, so when the function is called,
values are extracted from data and provided as arguments.
It is better to have one extraction function (an ``Idempotent`` decorator),
but with ``Monotonic`` data decoration.

Mixin
=====

:class:`@Mixin <jgdv.decorators.mixin.Mixin>` is a decorator to apply
mixin classes into the MRO of a base class.

So, instead of:

.. code:: python

   class MyClass(Mixin1, Mixin2, Mixin3, Base):
       ...

Mixins can be more clearly added thus:

.. code:: python

    @Mixin(Mixin1, Mixin2)
    class MyClass(Base):
        ...


Proto
=====

:class:`@Proto <jgdv.decorators.proto.Proto>` is similar to ``Mixin``,
but for annotating Protocols explicitly, with optional **definition-time**
checking that all required methods are implemented.
This ensures that if a protocol changes, implementing classes will
notify when they no longer fulfill the contract:

.. code:: python

    @Proto(MyProto_p)
    class Implementer:
          ...



            
.. Links:
            
.. _ParamSpec: https://docs.python.org/3/library/typing.html#typing.ParamSpec
