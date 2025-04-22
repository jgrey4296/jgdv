 

 
.. _jgdv.mixins.annotate:
   
    
====================
jgdv.mixins.annotate
====================

   
.. py:module:: jgdv.mixins.annotate

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.mixins.annotate.SubAnnotate_m
    jgdv.mixins.annotate.SubRegistry_m
    jgdv.mixins.annotate.Subclasser
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.mixins.annotate.SubAnnotate_m:
   
.. py:class:: SubAnnotate_m
   
    
   A Mixin to create simple subclasses through annotation.
   Annotation var name can be customized through the subclass kwarg 'annotate_to'.
   eg:

   class MyExample(SubAnnotate_m, annotate_to='blah'):
       pass

   a_sub = MyExample[int]
   a_sub.__class__.blah == int


   
   .. py:method:: _get_annotation() -> jgdv.Maybe[str]
      :classmethod:


   .. py:attribute:: _annotate_to
      :type:  ClassVar[str]
      :value: '_typevar'


 
 
 

.. _jgdv.mixins.annotate.SubRegistry_m:
   
.. py:class:: SubRegistry_m
   
   Bases: :py:obj:`SubAnnotate_m` 
     
   Create Subclasses in a registry

   By doing:

   class MyReg(SubRegistry_m):
       _registry : dict[str, type] = {}

   class MyClass(MyReg['blah']: ...

   MyClass is created as a subclass of MyReg, with a parameter set to 'blah'.
   This is added into MyReg._registry

   
   .. py:method:: _get_subclass_form(*, param: jgdv.Maybe = None) -> Self
      :classmethod:


   .. py:method:: _maybe_subclass_form(*, param: jgdv.Maybe = None) -> jgdv.Maybe[Self]
      :classmethod:


   .. py:attribute:: _registry
      :type:  ClassVar[dict]

 
 
 

.. _jgdv.mixins.annotate.Subclasser:
   
.. py:class:: Subclasser
   
    
   
   .. py:method:: _new_pydantic_class(name: str, cls: type, *, namespace: jgdv.Maybe[dict] = None) -> type
      :staticmethod:


   .. py:method:: _new_std_class(name: str, cls: type, *, namespace: jgdv.Maybe[dict] = None, mro: jgdv.Maybe[collections.abc.Iterable] = None) -> type
      :staticmethod:


      Dynamically creates a new class


   .. py:method:: decorate_name(cls: str | type, *vals: str, params: jgdv.Maybe[str] = None) -> str
      :staticmethod:


   .. py:method:: make_annotated_subclass(cls: type, *params: Any) -> type
      :staticmethod:


      Make a subclass of cls,
      annotated to have params in cls[cls._annotate_to]


   .. py:method:: make_subclass(name: str, cls: type, *, namespace: jgdv.Maybe[dict] = None, mro: jgdv.Maybe[collections.abc.Iterable] = None) -> type
      :staticmethod:


      Build a dynamic subclass of cls, with name,
      possibly with a maniplated mro and internal namespace


 
 
   
