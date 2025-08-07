.. -*- mode: ReST -*-

.. _structs:

=======
Structs
=======

.. contents:: Contents


:ref:`structs<jgdv.structs>` provides some of the key classes of ``JGDV``.
Especially:

1. :ref:`ChainGuard<jgdv.structs.chainguard>`, a type guarded failable accessor to nested mappings.
2. :ref:`Strang<jgdv.structs.strang>`, a Structured ``str`` subtype.
3. :ref:`DKey<jgdv.structs.dkey>`, extends ``Strang`` into a type guarded Key for getting values from dicts.
4. :ref:`Locator<jgdv.structs.locator>`, extends ``DKey`` into a Location/Path central store.
5. :ref:`rxmatcher<jgdv.structs.rxmatcher.RxMatcher>`, a utility for using the ``match`` statement with regular expressions.
   
Chainguard
==========

.. code:: python

   data = ChainGuard.load("some.toml")
   data['key']
   data.key
   data.table.sub.value
   data.on_fail(2).table.sub.value()

Strang
======

A Structured String class.

.. code:: python

   example : Strang = Strang("head.meta.data::tail.value")
   example[0:] == "head.meta.data"
   example[1:] == "tail.value"
   
DKey
====

Extends ``Strang`` to become a key.

.. code:: python

   # TODO

Locator
=======

A :ref:`Locator<jgdv.structs.locator.locator.JGDVLocator>` and :ref:`Location<jgdv.structs.locator.location.Location>` pair, to provide a central store of paths.

.. code:: python

   # TODO 


---------
RxMatcher
---------

.. code:: python

   # TODO 

          
   
.. Links:
.. _path: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath
