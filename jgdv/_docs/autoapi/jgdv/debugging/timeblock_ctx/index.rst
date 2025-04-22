 

 
.. _jgdv.debugging.timeblock_ctx:
   
    
============================
jgdv.debugging.timeblock_ctx
============================

   
.. py:module:: jgdv.debugging.timeblock_ctx

.. autoapi-nested-parse::

   See EOF for license/metadata/notes as applicable

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.debugging.timeblock_ctx.Logger

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.debugging.timeblock_ctx.TimeBlock_ctx
    jgdv.debugging.timeblock_ctx.TrackTime
           
 
      
 
Module Contents
===============

 
.. py:data:: Logger
   :type:  TypeAlias
   :value: logmod.Logger


 
 

.. _jgdv.debugging.timeblock_ctx.TimeBlock_ctx:
   
.. py:class:: TimeBlock_ctx(*, logger: jgdv.Maybe[Logger | False] = None, enter: jgdv.Maybe[str] = None, exit: jgdv.Maybe[str] = None, level: jgdv.Maybe[int | str] = None)
   
   Bases: :py:obj:`jgdv.protos.DILogger_p` 
     
   A Simple Timer Ctx class to log how long things take
   Give it a logger, a message, and a level.
   The message doesn't do any interpolation

   eg: With TimeBlock():...


   
   .. py:attribute:: _enter_msg
      :value: 'Starting Timer'


   .. py:attribute:: _exit_msg
      :value: 'Time Elapsed'


   .. py:attribute:: elapsed_time
      :type:  jgdv.Maybe[float]

   .. py:attribute:: end_time
      :type:  jgdv.Maybe[float]

   .. py:attribute:: start_time
      :type:  jgdv.Maybe[float]

 
 
 

.. _jgdv.debugging.timeblock_ctx.TrackTime:
   
.. py:class:: TrackTime(logger: jgdv.Maybe[Logger] = None, level: jgdv.Maybe[int | str] = None, enter: jgdv.Maybe[str] = None, exit: jgdv.Maybe[str] = None, **kwargs: Any)
   
   Bases: :py:obj:`jgdv.decorators.MetaDec` 
     
   Decorate a callable to track its timing

   
   .. py:method:: wrap_fn(fn: Func[TrackTime.wrap_fn.I, TrackTime.wrap_fn.O]) -> Func[TrackTime.wrap_fn.I, TrackTime.wrap_fn.O]

   .. py:method:: wrap_method(fn: Method[TrackTime.wrap_method.I, TrackTime.wrap_method.O]) -> Method[TrackTime.wrap_method.I, TrackTime.wrap_method.O]

   .. py:attribute:: _entry

   .. py:attribute:: _exit
      :value: None


   .. py:attribute:: _level
      :value: None


   .. py:attribute:: _logger
      :value: None


 
 
   
