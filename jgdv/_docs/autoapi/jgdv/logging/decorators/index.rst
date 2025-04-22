 

 
.. _jgdv.logging.decorators:
   
    
=======================
jgdv.logging.decorators
=======================

   
.. py:module:: jgdv.logging.decorators

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.decorators.LogCall
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.logging.decorators.LogCall:
   
.. py:class:: LogCall(enter: jgdv.Maybe[str | jgdv.Lambda] = None, exit: jgdv.Maybe[str | jgdv.Lambda] = None, level: int | str = logmod.INFO, logger: jgdv.Maybe[jgdv.logging._interface.Logger] = None)
   
   Bases: :py:obj:`jgdv.decorators.Decorator` 
     
   A Decorator for announcing the entry/exit of a function call

   eg:
   @LogCall(enter="Entering", exit="Exiting", level=logmod.INFO)
   def a_func()...

   
   .. py:method:: _log_msg(msg: jgdv.Maybe[str | jgdv.Lambda], fn: collections.abc.Callable, args: list, **kwargs)

   .. py:method:: _wrap_class(cls) -> type
      :abstractmethod:


   .. py:method:: _wrap_fn(fn) -> collections.abc.Callable

   .. py:method:: _wrap_method(fn) -> collections.abc.Callable

   .. py:attribute:: _enter_msg
      :value: None


   .. py:attribute:: _exit_msg
      :value: None


   .. py:attribute:: _logger

 
 
   
