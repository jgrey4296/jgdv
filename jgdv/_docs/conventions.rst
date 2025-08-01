.. -*- mode: ReST -*-

.. _conventions:

===========
Conventions
===========

.. contents:: Contents
   :local:

Package-wide conventions I prefer.

Naming
======

#. Ctx Managers                                 ``{}_ctx``.
#. Enums:                                       ``{}_e``.
#. Flags:                                       ``{}_f``.
#. :term:`Hooks <Hook>`:                              ``{}_h``.
#. :term:`Interfaces <Interface>`:              ``{}_i``.
#. Loggers:                                     ``{}_l``.
#. :term:`Mixins <Mixin>`:                             ``{}_m``.
#. :term:`Protocols <Interface>`:                                   ``{}_p``.
#. :term:`Slot`-based Data:                             ``{}_d``.
#. Specs:                                       ``{}_c``.
#. Structs:                                     ``{}_s``.
#. ``util`` not ``utils``.

Package Structure
=================

Top Level Package Structure.
Note the **in-tree** rst documentation.

.. code-block:: none

    <pacakge>/
    ├── __init__.py
    ├── py.typed
    ├── index.rst
    ├── _abstract/
    ├── _docs/
       └── conf.py
       └── _static/
       └── _templates/
   
Module Structure
================

Module structure is similar to top level package structure.
Interfaces, protocols, simple data structures etc go into the ``_interface.py`` file.

.. code-block:: none

    <module>/
    ├── __init__.py
    ├── _interface_.py
    ├── index.rst
    └── __tests/
       └── __init__.py
       └── test_{class}.py
