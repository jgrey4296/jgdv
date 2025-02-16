.. -*- mode: ReST -*-

.. _structs:

=======
Structs
=======

.. contents:: Contents


:doc:`_api/jgdv.structs` provides some of the key classes of JGDV.
Especially:

1. :doc:`_api/jgdv.structs.chainguard`, a type guarded failable accessor to nested mappings.
2. :doc:`_api/jgdv.structs.dkey`, a type guarded Key for getting values from dicts.
3. :doc:`_api/jgdv.structs.locator`, a Location/Path central store.
4. :doc:`_api/jgdv.structs.pathy`, a subtype of `Path <path_>`_ for disguishing directories from files at the type level.
5. :doc:`_api/jgdv.structs.strang`, a Structured `str` subtype.
   

Strang
======

.. code:: python

   example : Strang = Strang("head.meta.data::tail.value")
   example[0:] == "head.meta.data"
   example[1:] == "tail.value"
   
   
.. Links:
.. _path: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath
