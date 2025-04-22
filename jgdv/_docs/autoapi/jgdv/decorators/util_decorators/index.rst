 

 
.. _jgdv.decorators.util_decorators:
   
    
===============================
jgdv.decorators.util_decorators
===============================

   
.. py:module:: jgdv.decorators.util_decorators

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.decorators.util_decorators.Logger

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.decorators.util_decorators.Breakpoint
    jgdv.decorators.util_decorators.CanRaise
    jgdv.decorators.util_decorators.DoEither
    jgdv.decorators.util_decorators.DoMaybe
    jgdv.decorators.util_decorators.NoSideEffects
           
 
      
 
Module Contents
===============

 
.. py:data:: Logger
   :type:  TypeAlias
   :value: logmod.Logger


 
 

.. _jgdv.decorators.util_decorators.Breakpoint:
   
.. py:class:: Breakpoint(*args, prefix: jgdv.Maybe[str] = None, mark: jgdv.Maybe[str] = None, data: jgdv.Maybe[str] = None)
   
   Bases: :py:obj:`jgdv.decorators.core.IdempotentDec` 
     
   Decorator to attach a breakpoint to a function, without pausing execution

   
 
 
 

.. _jgdv.decorators.util_decorators.CanRaise:
   
.. py:class:: CanRaise(value: str | list[str], **kwargs)
   
   Bases: :py:obj:`jgdv.decorators.core.MetaDec` 
     
   TODO mark a target as able to raise certain errors.
   Non-exaustive, doesn't change runtime behaviour,
   just to simplify documentation


   
 
 
 

.. _jgdv.decorators.util_decorators.DoEither:
   
.. py:class:: DoEither(*args, prefix: jgdv.Maybe[str] = None, mark: jgdv.Maybe[str] = None, data: jgdv.Maybe[str] = None)
   
   Bases: :py:obj:`jgdv.decorators.core.MonotonicDec` 
     
   Either do the fn/method, or propagate the error

   
   .. py:method:: _wrap_fn_h(fn: jgdv.Func[DoEither._wrap_fn_h.I, DoEither._wrap_fn_h.O]) -> jgdv.Func[DoEither._wrap_fn_h.I, jgdv.Either[DoEither._wrap_fn_h.O]]

      override this to add a decorator to a function


   .. py:method:: _wrap_method_h(meth: jgdv.Method[DoEither._wrap_method_h.I, DoEither._wrap_method_h.O]) -> jgdv.Method[DoEither._wrap_method_h.I, jgdv.Either[DoEither._wrap_method_h.O]]

      Override this to add a decoration function to method


 
 
 

.. _jgdv.decorators.util_decorators.DoMaybe:
   
.. py:class:: DoMaybe(*args, prefix: jgdv.Maybe[str] = None, mark: jgdv.Maybe[str] = None, data: jgdv.Maybe[str] = None)
   
   Bases: :py:obj:`jgdv.decorators.core.MonotonicDec` 
     
   Make a fn or method propagate None's

   
   .. py:method:: _wrap_fn_h(fn: jgdv.Func[DoMaybe._wrap_fn_h.I, DoMaybe._wrap_fn_h.O]) -> jgdv.Func[DoMaybe._wrap_fn_h.I, jgdv.Maybe[DoMaybe._wrap_fn_h.O]]

      override this to add a decorator to a function


   .. py:method:: _wrap_method_h(meth: jgdv.Method[DoMaybe._wrap_method_h.I, DoMaybe._wrap_method_h.O]) -> jgdv.Method[DoMaybe._wrap_method_h.I, jgdv.Maybe[DoMaybe._wrap_method_h.O]]

      Override this to add a decoration function to method


 
 
 

.. _jgdv.decorators.util_decorators.NoSideEffects:
   
.. py:class:: NoSideEffects(value: str | list[str], **kwargs)
   
   Bases: :py:obj:`jgdv.decorators.core.MetaDec` 
     
   TODO Mark a Target as not modifying external variables

   
 
 
   
