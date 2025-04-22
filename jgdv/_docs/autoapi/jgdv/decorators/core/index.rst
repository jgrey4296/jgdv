 

 
.. _jgdv.decorators.core:
   
    
====================
jgdv.decorators.core
====================

   
.. py:module:: jgdv.decorators.core

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.decorators.core.DataDec
    jgdv.decorators.core.Decorator
    jgdv.decorators.core.IdempotentDec
    jgdv.decorators.core.MetaDec
    jgdv.decorators.core.MonotonicDec
    jgdv.decorators.core._DecAnnotate_m
    jgdv.decorators.core._DecIdempotentLogic_m
    jgdv.decorators.core._DecInspect_m
    jgdv.decorators.core._DecMark_m
    jgdv.decorators.core._DecWrap_m
    jgdv.decorators.core._DecoratorCombined_m
    jgdv.decorators.core._DecoratorHooks_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.decorators.core.DataDec:
   
.. py:class:: DataDec(keys: str | list[str], **kwargs)
   
   Bases: :py:obj:`IdempotentDec` 
     
   An extended IdempotentDec, which uses a data annotation
   on the original Decorable,
   to run the single wrapping function

   
   .. py:method:: _build_annotations_h(target, current: list) -> list

      Given a list of the current annotation list,
      return its replacement


   .. py:method:: _decoration_logic(target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Decorated

 
 
 

.. _jgdv.decorators.core.Decorator:
   
.. py:class:: Decorator(*args, prefix: jgdv.Maybe[str] = None, mark: jgdv.Maybe[str] = None, data: jgdv.Maybe[str] = None)
   
   Bases: :py:obj:`_DecoratorCombined_m`, :py:obj:`jgdv.decorators._interface.Decorator_p` 
     
   The abstract Superclass of Decorators
   A subclass implements '_decoration_logic'

   
   .. py:method:: _decoration_logic(target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Decorated
      :abstractmethod:


   .. py:method:: dec_name() -> str

   .. py:attribute:: Form
      :type:  ClassVar[enum.EnumMeta]

   .. py:attribute:: _annotation_prefix
      :type:  str

   .. py:attribute:: _data_key
      :type:  str

   .. py:attribute:: _data_suffix
      :type:  str

   .. py:attribute:: _mark_key
      :type:  str

   .. py:attribute:: _mark_suffix
      :type:  str

   .. py:attribute:: _wrapper_assignments
      :type:  list[str]

   .. py:attribute:: _wrapper_updates
      :type:  list[str]

   .. py:attribute:: needs_args
      :type:  ClassVar[bool]
      :value: False


 
 
 

.. _jgdv.decorators.core.IdempotentDec:
   
.. py:class:: IdempotentDec(*args, prefix: jgdv.Maybe[str] = None, mark: jgdv.Maybe[str] = None, data: jgdv.Maybe[str] = None)
   
   Bases: :py:obj:`Decorator` 
     
   The Base Idempotent Decorator

   Already decorated targets are 'marked' with _mark_key as an attr.

   Can annotate targets with metadata without modifying the runtime behaviour,
   or modify the runtime behaviour

   annotations are assigned as setattr(fn, DecoratorBase._data_key, [])
   the mark is set(fn, DecoratorBase._mark_key, True)

   Moving data from wrapped to wrapper is taken care of,
   so no need for ftz.wraps in _wrap_method_h or _wrap_fn_h


   
   .. py:method:: _decoration_logic(target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Decorated

 
 
 

.. _jgdv.decorators.core.MetaDec:
   
.. py:class:: MetaDec(value: str | list[str], **kwargs)
   
   Bases: :py:obj:`Decorator` 
     
   Adds metadata without modifying runtime behaviour of target,
   Or validates a class

   ie: annotates without wrapping

   
   .. py:method:: _build_annotations_h(target, current: list) -> list

      Given a list of the current annotation list,
      return its replacement


   .. py:method:: _decoration_logic(target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Decorated

 
 
 

.. _jgdv.decorators.core.MonotonicDec:
   
.. py:class:: MonotonicDec(*args, prefix: jgdv.Maybe[str] = None, mark: jgdv.Maybe[str] = None, data: jgdv.Maybe[str] = None)
   
   Bases: :py:obj:`Decorator` 
     
   The Base Monotonic Decorator

   Applying the decorator repeatedly adds successive decoration functions
   Monotonic's don't annotate

   
   .. py:method:: _decoration_logic(target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Decorated

 
 
 

.. jgdv.decorators.core._DecAnnotate_m:
   
.. py:class:: _DecAnnotate_m
   
    
   Utils for manipulating annotations related to the decorator
   Annotations for a decorator are stored in a dict entry.
   of the form: '{annotation_prefix}:{data_suffix}'

   
   .. py:method:: annotate_decorable(target: jgdv.decorators._interface.Decorable) -> list

      Essentially: target[data_key] += self[data_key][:]


   .. py:method:: data_key() -> str

   .. py:method:: get_annotations(target: jgdv.decorators._interface.Decorable) -> list[str]

      Get the annotations of the target


   .. py:method:: is_annotated(target: jgdv.decorators._interface.Decorable) -> bool

   .. py:attribute:: _annotation_prefix
      :type:  str

   .. py:attribute:: _data_key
      :type:  str

   .. py:attribute:: _data_suffix
      :type:  str

 
 
 

.. jgdv.decorators.core._DecIdempotentLogic_m:
   
.. py:class:: _DecIdempotentLogic_m
   
    
   Decorate the passed target in an idempotent way

   
 
 
 

.. jgdv.decorators.core._DecInspect_m:
   
.. py:class:: _DecInspect_m
   
    
   
   .. py:method:: _discrim_form(target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.DForm_e

      Determine the type of the thing being decorated


   .. py:method:: _signature(target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Signature

 
 
 

.. jgdv.decorators.core._DecMark_m:
   
.. py:class:: _DecMark_m
   
    
   For Marking and checking Decorables.
   Marks are for easily testing if Decorator decorated something already


   
   .. py:method:: apply_mark(*args: jgdv.decorators._interface.Decorable) -> None

      Mark the UNWRAPPED, original target as already decorated


   .. py:method:: is_marked(target: jgdv.decorators._interface.Decorable) -> bool

   .. py:method:: mark_key() -> str

   .. py:attribute:: _mark_key
      :type:  str

 
 
 

.. jgdv.decorators.core._DecWrap_m:
   
.. py:class:: _DecWrap_m
   
    
   Utils for unwrapping and wrapping a

   
   .. py:method:: _apply_onto(wrapper: jgdv.decorators._interface.Decorated, target: jgdv.decorators._interface.Decorable) -> jgdv.decorators._interface.Decorated

      Uses functools.update_wrapper,
      Modify cls._wrapper_assignments and cls._wrapper_updates as necessary


   .. py:method:: _build_wrapper(form: jgdv.decorators._interface.DForm_e, target: jgdv.decorators._interface.Decorable) -> jgdv.Maybe[jgdv.decorators._interface.Decorated]

      Create a new decoration using the appropriate hook


   .. py:method:: _unwrap(target: jgdv.decorators._interface.Decorated) -> jgdv.decorators._interface.Decorable

      Get the un-decorated function if there is one


   .. py:method:: _unwrapped_depth(target: jgdv.decorators._interface.Decorated) -> int

      the code of inspect.unwrap, but used for counting the unwrap depth


 
 
 

.. jgdv.decorators.core._DecoratorCombined_m:
   
.. py:class:: _DecoratorCombined_m
   
   Bases: :py:obj:`_DecAnnotate_m`, :py:obj:`_DecWrap_m`, :py:obj:`_DecMark_m`, :py:obj:`_DecInspect_m`, :py:obj:`_DecoratorHooks_m` 
     
   Combines the util mixins

   
 
 
 

.. jgdv.decorators.core._DecoratorHooks_m:
   
.. py:class:: _DecoratorHooks_m
   
    
   The main hooks used to actually specify the decoration

   
   .. py:method:: _build_annotations_h(target: jgdv.decorators._interface.Decorable, current: list) -> jgdv.Maybe[list]

      Given a list of the current annotation list,
      return its replacement


   .. py:method:: _validate_sig_h(sig: jgdv.decorators._interface.Signature, form: jgdv.decorators._interface.DForm_e, args: jgdv.Maybe[list] = None) -> None

   .. py:method:: _validate_target_h(target: jgdv.decorators._interface.Decorable, form: jgdv.decorators._interface.DForm_e, args: jgdv.Maybe[list] = None) -> None

      Abstract class for specialization.
      Given the original target, throw an error here if it isn't 'correct' in some way


   .. py:method:: _wrap_class_h(cls: type) -> jgdv.Maybe[jgdv.decorators._interface.Decorated]

      Override this to decorate a class


   .. py:method:: _wrap_fn_h(fn: jgdv.Func[_DecoratorHooks_m._wrap_fn_h.In, _DecoratorHooks_m._wrap_fn_h.Out]) -> jgdv.decorators._interface.Decorated[jgdv.Func[_DecoratorHooks_m._wrap_fn_h.In, _DecoratorHooks_m._wrap_fn_h.Out]]

      override this to add a decorator to a function


   .. py:method:: _wrap_method_h(meth: jgdv._abstract.types.Method[_DecoratorHooks_m._wrap_method_h.In, _DecoratorHooks_m._wrap_method_h.Out]) -> jgdv.decorators._interface.Decorated[jgdv._abstract.types.Method[_DecoratorHooks_m._wrap_method_h.In, _DecoratorHooks_m._wrap_method_h.Out]]

      Override this to add a decoration function to method


 
 
   
