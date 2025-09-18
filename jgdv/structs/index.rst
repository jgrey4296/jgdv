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

.. include:: __examples/chainguard_ex.toml
   :code: toml

.. include:: __example/chainguard_ex.py
   :code: python


Strang
======

A Structured String class.

.. include:: __examples/strang_ex.py
   :code: python


DKey
====

Extends ``Strang`` to become a key.

.. include:: __examples/dkey_ex.py
   :code: python



Locator
=======

A :ref:`Locator<jgdv.structs.locator.locator.JGDVLocator>` and :ref:`Location<jgdv.structs.locator.location.Location>` pair, to provide a central store of paths.

.. include:: __examples/locator_ex.py
   :code: python



---------
RxMatcher
---------

.. include:: __examples/rx_matcher_ex.py
   :code: python

          
   
.. Links:
.. _path: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath
