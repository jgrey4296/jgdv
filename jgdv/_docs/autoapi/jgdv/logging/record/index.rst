 

 
.. _jgdv.logging.record:
   
    
===================
jgdv.logging.record
===================

   
.. py:module:: jgdv.logging.record

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.record.JGDVLogRecord
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.logging.record.JGDVLogRecord:
   
.. py:class:: JGDVLogRecord(name, level, pathname, lineno, msg, args, exc_info, func=None, sinfo=None, **kwargs)
   
   Bases: :py:obj:`logmod.getLogRecordFactory`\ (\ ) 
     
   A Basic extension of the log record.

   needs the signature::

       factory(name, level, fn, lno, msg, args, exc_info, func=None, sinfo=None, **kwargs)


   
 
 
   
