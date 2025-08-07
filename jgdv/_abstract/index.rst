.. -*- mode: ReST -*-

.. _abstract:

=============
Abstract APIs
=============

.. contents:: Contents

This module provides various abstractions for reuse, mainly:

1. :ref:`Protocols<jgdv._abstract.protocols>`.
2. :ref:`Type Aliases<jgdv._abstract.types>`.
3. :ref:`Type Guards<jgdv._abstract.typeguards>`.
4. An import :ref:`Prelude<jgdv._abstract.prelude>`.
5. A :ref:`JGDVError<jgdv._abstract.error.JGDVError>` class.
   
---------
Protocols
---------

Some :ref:`General<jgdv._abstract.protocols.general>` and
:ref:`more<jgdv._abstract.protocols.pre_processable>`
:ref:`specific<jgdv._abstract.protocols.pre_processable>` protocols.
Also some protocol adaptions of the :ref:`stdlib<jgdv._abstract.protocols.stdlib>`.
    

------------
Type Aliases
------------

Rather than ``str | None``, I prefer
:py:type:`Maybe[str] <jgdv._abstract.types.Maybe>`.
Similarly :py:type:`Result[str, IndexError] <jgdv._abstract.types.Result>`
etc.


-------
Prelude
-------
