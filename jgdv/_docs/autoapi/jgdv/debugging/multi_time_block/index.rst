 

 
.. _jgdv.debugging.multi_time_block:
   
    
===============================
jgdv.debugging.multi_time_block
===============================

   
.. py:module:: jgdv.debugging.multi_time_block

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.debugging.multi_time_block.Logger

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.debugging.multi_time_block.MultiTimeBlock_ctx
           
 
      
 
Module Contents
===============

 
.. py:data:: Logger
   :type:  TypeAlias
   :value: logmod.Logger


 
 

.. _jgdv.debugging.multi_time_block.MultiTimeBlock_ctx:
   
.. py:class:: MultiTimeBlock_ctx(*, count: int = 10, repeat: int = 5, keep_gc: bool = False, group: jgdv.Maybe[str] = None, logger: jgdv.Maybe[Logger] = None, level: jgdv.Maybe[int | str] = None)
   
    
   CtxManager for timing statements multiple times

   see https://docs.python.org/3/library/timeit.html

   
   .. py:method:: _log(msg: str, *args: Any, time: jgdv.Maybe[float] = None, prefix: jgdv.Maybe[str] = None) -> None

      The internal log method


   .. py:method:: _set_name(*, name: str, stmt: collections.abc.Callable) -> None

      Default Name builder


   .. py:method:: auto(stmt: collections.abc.Callable, *, name: jgdv.Maybe[str] = None) -> float

      Try the statement with larger trial sizes until it takes at least 0.2 seconds


   .. py:method:: autorange_cb(number: int, took: float) -> None

      Callback for autorange.
      Called after each trial.


   .. py:method:: block(stmt: collections.abc.Callable, *, name: jgdv.Maybe[str] = None) -> float

      Run the stmt {count} numnber of times and report the time it took


   .. py:method:: once(stmt: collections.abc.Callable, *, name: jgdv.Maybe[str] = None) -> float

      Run the statement once, and return the time it took


   .. py:method:: repeats(stmt: collections.abc.Callable, *, name: jgdv.Maybe[str] = None) -> list[float]

      Repeat the stmt and report the results


   .. py:attribute:: _current_name
      :type:  jgdv.Maybe[str]

   .. py:attribute:: _logger
      :type:  jgdv.Maybe[Logger]

   .. py:attribute:: autorange_total
      :type:  float

   .. py:attribute:: count
      :type:  int

   .. py:attribute:: group
      :type:  str

   .. py:attribute:: keep_gc
      :type:  bool

   .. py:attribute:: log_level
      :type:  int

   .. py:attribute:: once_log
      :type:  list[tuple[str, float]]

   .. py:attribute:: repeat
      :type:  int

 
 
   
