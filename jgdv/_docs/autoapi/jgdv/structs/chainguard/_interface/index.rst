 

 
.. _jgdv.structs.chainguard._interface:
   
    
==================================
jgdv.structs.chainguard._interface
==================================

   
.. py:module:: jgdv.structs.chainguard._interface

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.structs.chainguard._interface.TomlTypes

        

           

 
 

 
 

Protocols
---------

.. autoapisummary::

   jgdv.structs.chainguard._interface.ChainGuard_p
   jgdv.structs.chainguard._interface.ChainProxy_p

           
   
             
  
           
 
  
           
 
      
 
Module Contents
===============

 
.. py:data:: TomlTypes
   :type:  TypeAlias
   :value: str | int | float | bool | list['TomlTypes'] | dict[str, 'TomlTypes'] | datetime.datetime


 
 

.. _jgdv.structs.chainguard._interface.ChainGuard_p:
   
.. py:class:: ChainGuard_p
   
   Bases: :py:obj:`Protocol` 
     
   The interface for a base ChainGuard object

   
   .. py:method:: from_dict(data: dict[str, TomlTypes]) -> Self
      :classmethod:


   .. py:method:: get(key: str, default: jgdv.Maybe[TomlTypes] = None) -> jgdv.Maybe[TomlTypes]

   .. py:method:: load(*paths: str | pathlib.Path) -> Self
      :classmethod:


   .. py:method:: load_dir(dirp: str | pathlib.Path) -> Self
      :classmethod:


   .. py:method:: read(text: str) -> T
      :classmethod:


 
 
 

.. _jgdv.structs.chainguard._interface.ChainProxy_p:
   
.. py:class:: ChainProxy_p
   
   Bases: :py:obj:`Protocol` 
     
   The proxy interface

   Used for special access like::

       cg.on_fail(...).val()


   
 
 
   
