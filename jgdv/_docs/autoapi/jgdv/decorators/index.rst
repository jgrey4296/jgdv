 

 
.. _jgdv.decorators:
   
    
===============
jgdv.decorators
===============

   
.. py:module:: jgdv.decorators

.. autoapi-nested-parse::

   Idenpotent Decorators, as an extendable class

   Key Classes:
   - DecoratorBase : Simplifies decorations to writing a _wrap_[method/fn/class] method.
   - MetaDecorator : Adds metadata to callable, without changing the behaviour of it.
   - DataDecorator : Stacks data onto the callable, with only one wrapping function

       
 

Submodules
----------
   
.. toctree::
   :maxdepth: 1

   /_docs/autoapi/jgdv/decorators/_interface/index
   /_docs/autoapi/jgdv/decorators/core/index
   /_docs/autoapi/jgdv/decorators/mixin/index
   /_docs/autoapi/jgdv/decorators/proto/index
   /_docs/autoapi/jgdv/decorators/util_decorators/index

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.decorators.DecoratorAccessor_m
           
 
      
 
Package Contents
================

 
 

.. _jgdv.decorators.DecoratorAccessor_m:
   
.. py:class:: DecoratorAccessor_m
   
    
   A mixin for building Decorator Accessors like DKeyed.
   Holds a _decoration_builder class, and helps you build it

   
   .. py:method:: _build_decorator(keys) -> _interface.Decorator_p
      :classmethod:


   .. py:method:: get_keys(target: _interface.Decorated) -> list[jgdv.Ident]
      :classmethod:


      Retrieve key annotations from a Decorated


   .. py:attribute:: _decoration_builder
      :type:  ClassVar[type[core.Decorator]]

 
 
   
