 

 
.. _jgdv.decorators._interface:
   
    
==========================
jgdv.decorators._interface
==========================

   
.. py:module:: jgdv.decorators._interface

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.decorators._interface.Decorable
   jgdv.decorators._interface.Decorated
   jgdv.decorators._interface.Signature

        

 
 
   
Enums
-----

.. autoapisummary::

   jgdv.decorators._interface.DForm_e

           

 
 

 
 

Protocols
---------

.. autoapisummary::

   jgdv.decorators._interface.Decorator_p

           
   
             
  
           
 
  
           
 
      
 
Module Contents
===============

 
.. py:data:: Decorable
   :type:  TypeAlias
   :value: type | Func | Method


 
.. py:data:: Decorated
   :type:  TypeAlias
   :value: F


 
.. py:data:: Signature
   :type:  TypeAlias
   :value: inspect.Signature


 
 

.. _jgdv.decorators._interface.DForm_e:
   
.. py:class:: DForm_e(*args, **kwds)
   
   Bases: :py:obj:`enum.Enum` 
     
   This is necessary because you can't use Callable or MethodType
   in match statement

   
   .. py:attribute:: CLASS

   .. py:attribute:: FUNC

   .. py:attribute:: METHOD

 
 
 

.. _jgdv.decorators._interface.Decorator_p:
   
.. py:class:: Decorator_p
   
   Bases: :py:obj:`Protocol` 
     
   Base class for protocol classes.

   Protocol classes are defined as::

       class Proto(Protocol):
           def meth(self) -> int:
               ...

   Such classes are primarily used with static type checkers that recognize
   structural subtyping (static duck-typing).

   For example::

       class C:
           def meth(self) -> int:
               return 0

       def func(x: Proto) -> int:
           return x.meth()

       func(C())  # Passes static type check

   See PEP 544 for details. Protocol classes decorated with
   @typing.runtime_checkable act as simple-minded runtime protocols that check
   only the presence of given attributes, ignoring their type signatures.
   Protocol classes can be generic, they are defined as::

       class GenProto[T](Protocol):
           def meth(self) -> T:
               ...

   
   .. py:method:: _build_annotations_h(target: Decorable, current: list) -> jgdv.Maybe[list]

   .. py:method:: _validate_sig_h(sig: Signature, form: DForm_e, args: jgdv.Maybe[list] = None) -> None

   .. py:method:: _validate_target_h(target: Decorable, form: DForm_e, args: jgdv.Maybe[list] = None) -> None

   .. py:method:: _wrap_class_h(cls: type) -> jgdv.Maybe[Decorated]

   .. py:method:: _wrap_fn_h(fn: jgdv._abstract.types.Func[Decorator_p._wrap_fn_h.In, Decorator_p._wrap_fn_h.Out]) -> Decorated[jgdv._abstract.types.Func[Decorator_p._wrap_fn_h.In, Decorator_p._wrap_fn_h.Out]]

   .. py:method:: _wrap_method_h(meth: jgdv._abstract.types.Method[Decorator_p._wrap_method_h.In, Decorator_p._wrap_method_h.Out]) -> Decorated[jgdv._abstract.types.Method[Decorator_p._wrap_method_h.In, Decorator_p._wrap_method_h.Out]]

   .. py:method:: annotate_decorable(target: Decorable) -> list

   .. py:method:: apply_mark(*args: Decorable) -> None

   .. py:method:: dec_name() -> str

   .. py:method:: get_annotations(target: Decorable) -> list[str]

   .. py:method:: is_annotated(target: Decorable) -> bool

   .. py:method:: is_marked(target: Decorable) -> bool

 
 
   
