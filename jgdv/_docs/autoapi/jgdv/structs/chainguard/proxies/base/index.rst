 

 
.. _jgdv.structs.chainguard.proxies.base:
   
    
====================================
jgdv.structs.chainguard.proxies.base
====================================

   
.. py:module:: jgdv.structs.chainguard.proxies.base

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.chainguard.proxies.base.GuardProxy
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.chainguard.proxies.base.GuardProxy:
   
.. py:class:: GuardProxy(data: jgdv.structs.chainguard._base.GuardBase, types: Any = None, index: jgdv.Maybe[list[str]] = None, fallback: jgdv.structs.chainguard._base.TomlTypes | Never = Never)
   
    
   A Base Class for Proxies

   
   .. py:method:: _index(sub: str = None) -> list[str]

   .. py:method:: _inject(val: tuple[Any] = Never, attr: jgdv.Maybe[str] = None, clear: bool = False) -> GuardProxy

   .. py:method:: _match_type(val: jgdv.structs.chainguard._base.TomlTypes) -> jgdv.structs.chainguard._base.TomlTypes

   .. py:method:: _notify() -> None

   .. py:method:: _types_str() -> str

   .. py:attribute:: __index
      :type:  list[str]
      :value: ['<root>']


   .. py:attribute:: _data

   .. py:attribute:: _types

 
 
   
