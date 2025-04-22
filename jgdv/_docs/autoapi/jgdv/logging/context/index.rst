 

 
.. _jgdv.logging.context:
   
    
====================
jgdv.logging.context
====================

   
.. py:module:: jgdv.logging.context

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.context.LogContext
    jgdv.logging.context.TempLogger
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.logging.context.LogContext:
   
.. py:class:: LogContext(logger, level=None)
   
    
     a really simple wrapper to set a logger's level, then roll it back

   use as:
   with LogContext(logger, level=logmod.INFO) as ctx:
   ctx.log("blah")
   # or
   logger.info("blah")

   
   .. py:method:: log(msg, *args, **kwargs)

   .. py:attribute:: _level_stack

   .. py:attribute:: _logger

   .. py:attribute:: _original_level

   .. py:attribute:: _temp_level

 
 
 

.. _jgdv.logging.context.TempLogger:
   
.. py:class:: TempLogger(logger: type[jgdv.logging._interface.Logger])
   
    
   For using a specific type of logger in a context, or getting
   a custom logger class without changing it globally

   use as:
   with TempLogger(MyLoggerClass) as ctx:
   # Either:
   ctx['name'].info(...)
   # or:
   logmod.getLogger('name').info(...)

   
   .. py:method:: __exit(*exc)

   .. py:attribute:: _original
      :type:  jgdv.Maybe[logging.Logger]
      :value: None


   .. py:attribute:: _target_cls

 
 
   
