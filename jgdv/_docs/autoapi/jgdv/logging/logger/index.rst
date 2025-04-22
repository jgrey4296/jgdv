 

 
.. _jgdv.logging.logger:
   
    
===================
jgdv.logging.logger
===================

   
.. py:module:: jgdv.logging.logger

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.logging.logger.Logger

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.logger.JGDVLogger
           
 
      
 
Module Contents
===============

 
.. py:data:: Logger
   :type:  TypeAlias
   :value: logmod.Logger


 
 

.. _jgdv.logging.logger.JGDVLogger:
   
.. py:class:: JGDVLogger(*args, **kwargs)
   
   Bases: :py:obj:`logmod.getLoggerClass`\ (\ ) 
     
   Basic extension of the logger class

   checks the classvar _levels (intEnum) for additional log levels
   which can be accessed as attributes and items.
   eg: logger.trace(...)
   and: logger['trace'](...)

   
   .. py:method:: getChild(name)

      Get a logger which is a descendant to this one.

      This is a convenience method, such that

      logging.getLogger('abc').getChild('def.ghi')

      is the same as

      logging.getLogger('abc.def.ghi')

      It's useful, for example, when the parent logger is named using
      __name__ rather than a literal string.


   .. py:method:: install()
      :classmethod:


   .. py:method:: makeRecord(*args, **kwargs)

      A factory method which can be overridden in subclasses to create
      specialized LogRecords.
      args: name, level, fn, lno, msg, args, exc_info,
      kwargs: func=None, extra=None, sinfo=None


   .. py:method:: prefix(prefix: str | callable) -> Logger

   .. py:method:: set_colour(colour: str)

   .. py:method:: set_prefixes(*prefixes: jgdv.Maybe[str | callable])

   .. py:attribute:: _colour
      :value: None


   .. py:attribute:: _prefixes
      :value: []


 
 
   
