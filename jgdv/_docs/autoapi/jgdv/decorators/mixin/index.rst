 

 
.. _jgdv.decorators.mixin:
   
    
=====================
jgdv.decorators.mixin
=====================

   
.. py:module:: jgdv.decorators.mixin

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.decorators.mixin.DelayMixin
    jgdv.decorators.mixin.Mixin
    jgdv.decorators.mixin.MixinNow
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.decorators.mixin.DelayMixin:
   
.. py:class:: DelayMixin(keys: str | list[str], **kwargs)
   
   Bases: :py:obj:`jgdv.decorators.core.DataDec` 
     
   TODO A Decorator for annotating a class with mixins

   Delays the construction of the True class until later,
   using @MixinNow

   
 
 
 

.. _jgdv.decorators.mixin.Mixin:
   
.. py:class:: Mixin(*mixins: jgdv.Maybe[type], allow_inheritance: bool = False, silent: bool = False)
   
   Bases: :py:obj:`jgdv.decorators.core.MonotonicDec` 
     
   Decorator to App/Prepend Mixins into the decorated class.

   Converts::

       class ClsName(mixins, Supers, Protocols, metaclass=MCls, **kwargs):...

   into::

       @Protocols(*ps)
       @Mixin(*ms, None)
       class ClsName(Supers): ...


   ('None' is used to separate pre and post mixins)

   
   .. py:method:: _build_annotations_h(target: jgdv.decorators._interface.Decorable, current: list) -> jgdv.Maybe[list]

      Given a list of the current annotation list,
      return its replacement


   .. py:method:: _validate_mixins() -> None

   .. py:method:: _validate_target_h(target: jgdv.decorators._interface.Decorable, form: jgdv.decorators._interface.DForm_e, args: jgdv.Maybe[list] = None) -> None

      Abstract class for specialization.
      Given the original target, throw an error here if it isn't 'correct' in some way


   .. py:method:: _wrap_class_h(cls: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Decorated

      Override this to decorate a class


   .. py:attribute:: _name_mod
      :value: 'M'


   .. py:attribute:: _silent
      :value: False


   .. py:attribute:: needs_args
      :value: True


 
 
 

.. _jgdv.decorators.mixin.MixinNow:
   
.. py:class:: MixinNow(*args, prefix: jgdv.Maybe[str] = None, mark: jgdv.Maybe[str] = None, data: jgdv.Maybe[str] = None)
   
   Bases: :py:obj:`jgdv.decorators.core.MonotonicDec` 
     
   TODO The trigger for delayed mixins.

   After using @DelayMixin,
   trigger the True class using this.

   eg::

       @MixinNow
       @DelayMixin(m3, None, m4)
       @DelayMixin(m1, m2)
       class Blah:...


   
 
 
   
