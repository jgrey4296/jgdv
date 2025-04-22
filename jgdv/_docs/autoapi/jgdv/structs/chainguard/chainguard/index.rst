 

 
.. _jgdv.structs.chainguard.chainguard:
   
    
==================================
jgdv.structs.chainguard.chainguard
==================================

   
.. py:module:: jgdv.structs.chainguard.chainguard

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.chainguard.chainguard.ChainGuard
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.chainguard.chainguard.ChainGuard:
   
.. py:class:: ChainGuard(data: dict[str, jgdv.structs.chainguard._interface.TomlTypes] = None, *, index: jgdv.Maybe[list[str]] = None, mutable: bool = False)
   
   Bases: :py:obj:`jgdv.structs.chainguard._base.GuardBase` 
     
   The Final ChainGuard class.

   Takes the GuardBase object, and mixes in extra capabilities.


   
   .. py:method:: merge(*guards: Self, dfs: jgdv.Maybe[collections.abc.Callable] = None, index: jgdv.Maybe[str] = None, shadow: bool = False) -> Self
      :classmethod:


      Given an ordered list of guards and dicts, convert them to dicts,
      update an empty dict with each,
      then wrap that combined dict in a ChainGuard

      *NOTE*: classmethod, not instance. search order is same as arg order.
      So merge(a, b, c) will retrive from c only if a, then b, don't have the key

      # TODO if given a dfs callable, use it to merge more intelligently


   .. py:method:: remove_prefix(prefix: str) -> ChainGuard

      Try to remove a prefix from loaded data
      eg: ChainGuard(tools.ChainGuard.data..).remove_prefix("tools.ChainGuard")
      -> ChainGuard(data..)


 
 
   
