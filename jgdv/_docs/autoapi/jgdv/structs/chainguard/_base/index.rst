 

 
.. _jgdv.structs.chainguard._base:
   
    
=============================
jgdv.structs.chainguard._base
=============================

   
.. py:module:: jgdv.structs.chainguard._base

.. autoapi-nested-parse::

   The core implementation of the ChainGuard object,
   which is then extended with mixins.

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.chainguard._base.GuardBase
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.chainguard._base.GuardBase:
   
.. py:class:: GuardBase(data: dict[str, jgdv.structs.chainguard._interface.TomlTypes] = None, *, index: jgdv.Maybe[list[str]] = None, mutable: bool = False)
   
   Bases: :py:obj:`dict` 
     
   Provides access to toml data (ChainGuard.load(apath))
   but as attributes (data.a.path.in.the.data)
   instead of key access (data['a']['path']['in']['the']['data'])

   while also providing typed, guarded access:
   data.on_fail("test", str | int).a.path.that.may.exist()

   while it can then report missing paths:
   data.report_defaulted() -> ['a.path.that.may.exist.<str|int>']

   
   .. py:method:: _index() -> list[str]

   .. py:method:: _table() -> dict[str, jgdv.structs.chainguard._interface.TomlTypes]

   .. py:method:: items() -> collections.abc.ItemsView[str, jgdv.structs.chainguard._interface.TomlTypes]

      D.items() -> a set-like object providing a view on D's items


   .. py:method:: keys() -> collections.abc.KeysView[str]

      D.keys() -> a set-like object providing a view on D's keys


   .. py:method:: update(*args)
      :abstractmethod:


      D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
      If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
      If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
      In either case, this is followed by: for k in F:  D[k] = F[k]


   .. py:method:: values() -> collections.abc.ValuesView[jgdv.structs.chainguard._interface.TomlTypes]

      D.values() -> an object providing a view on D's values


 
 
   
