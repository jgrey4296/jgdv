 

 
.. _jgdv.structs.metalord.core:
   
    
==========================
jgdv.structs.metalord.core
==========================

   
.. py:module:: jgdv.structs.metalord.core

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.metalord.core.MetalordCore
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.metalord.core.MetalordCore:
   
.. py:class:: MetalordCore(name, bases: tuple, namespace: dict, **kwargs)
   
   Bases: :py:obj:`type` 
     
   The Core of Metalord.

   By default classes are constructed using type().
   https://docs.python.org/3/reference/datamodel.html#metaclasses

   Execution order::

       - Metaclass Definition
       - Metaclass Creation

       - Class Definition:
           1) MRO resolution           : __mro_entries__(self, bases)
           2) metaclass selection      : (most dervied of (type | metaclasses))
           3) namespace preparation    : metacls.__prepare__(metacls, name, bases, **kwargs) -> dict
           4) class body execution     : exec(body, globals, namespace)
           5) class object creation    : metaclass.__new__(name, bases, namespace, **kwargs) -> classobj
           6) subclass init            : parent.__init_subclass__(cls, **kwargs)
           7) class object init        : metaclass.__init__(cls, na,e, bases, namespace, **kwargs)

       - Instance Creation::
           1) metaclass.__call__(cls, ...) -> instance
           1.b) cls.__new__(cls, ...) -> instance
           1.c) cls.__init__(instance, ...)


   
 
 
   
