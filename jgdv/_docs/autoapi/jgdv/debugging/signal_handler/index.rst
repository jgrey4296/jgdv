 

 
.. _jgdv.debugging.signal_handler:
   
    
=============================
jgdv.debugging.signal_handler
=============================

   
.. py:module:: jgdv.debugging.signal_handler

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.debugging.signal_handler.NullHandler
    jgdv.debugging.signal_handler.SignalHandler
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.debugging.signal_handler.NullHandler:
   
.. py:class:: NullHandler
   
    
   An interrupt handler that does nothing

   
   .. py:method:: handle(signum, frame)
      :staticmethod:


   .. py:method:: install(sig=signal.SIGINT)
      :staticmethod:


   .. py:method:: uninstall(sig=signal.SIGINT)
      :staticmethod:


 
 
 

.. _jgdv.debugging.signal_handler.SignalHandler:
   
.. py:class:: SignalHandler
   
    
   Install a breakpoint to run on (by default) SIGINT

   disables itself if PRE_COMMIT is in the environment.
   Can act as a context manager


   
   .. py:method:: handle(signum, frame)
      :staticmethod:


   .. py:method:: install(sig=signal.SIGINT)
      :staticmethod:


   .. py:method:: uninstall(sig=signal.SIGINT)
      :staticmethod:


   .. py:attribute:: _disabled

 
 
   
