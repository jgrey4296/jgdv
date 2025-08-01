.. -*- mode: ReST -*-

.. _structs:

=======
Structs
=======

.. contents:: Contents


:ref:`jgdv.structs` provides some of the key classes of JGDV.
Especially:

1. :ref:`jgdv.structs.chainguard`, a type guarded failable accessor to nested mappings.
2. :ref:`jgdv.structs.dkey`, a type guarded Key for getting values from dicts.
3. :ref:`jgdv.structs.locator`, a Location/Path central store.
4. :ref:`jgdv.structs.pathy`, a subtype of `Path <path_>`_ for disguishing directories from files at the type level.
5. :ref:`jgdv.structs.strang`, a Structured `str` subtype.
   
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

Extends :ref:`Strang` to become a key.

.. code:: python

   # TODO

Locator
=======

A :ref:`Locator` and :ref:`Location` pair, to provide a central store of paths.

.. code:: python

   # TODO 

   
.. Links:
.. _path: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath
