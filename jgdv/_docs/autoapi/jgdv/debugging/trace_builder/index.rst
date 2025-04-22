 

 
.. _jgdv.debugging.trace_builder:
   
    
============================
jgdv.debugging.trace_builder
============================

   
.. py:module:: jgdv.debugging.trace_builder

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.debugging.trace_builder.TraceBuilder
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.debugging.trace_builder.TraceBuilder:
   
.. py:class:: TraceBuilder(*, chop_self: bool = True)
   
    
   A Helper to simplify access to tracebacks.
   By Default, removes the frames of this tracebuilder from the trace
   ie     : TraceBuilder._get_frames() -> TraceBuilder.__init__() -> call -> call -> root
   will be: call -> call -> root

   use item acccess to limit the frames,
   eg: tb[2:], will remove the two most recent frames from the traceback

   Use as:
   tb = TraceBuilder()
   raise Exception().with_traceback(tb[:])

   
   .. py:method:: _get_frames() -> None

      from https://stackoverflow.com/questions/27138440
      Builds the frame stack from most recent to least,


   .. py:method:: to_tb(frames: jgdv.Maybe[list[jgdv.Frame]] = None) -> jgdv.Traceback

   .. py:attribute:: frames
      :type:  list[jgdv.Frame]
      :value: []


 
 
   
