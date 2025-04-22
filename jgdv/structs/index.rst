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

   # TODO

DKey
====

.. code:: python

   # TODO

Locator
=======

.. code:: python

   # TODO 

Pathy
=====

.. code:: python

   # TODO

Strang
======

.. code:: python

   example : Strang = Strang("head.meta.data::tail.value")
   example[0:] == "head.meta.data"
   example[1:] == "tail.value"
   
   
.. Links:
.. _path: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath
