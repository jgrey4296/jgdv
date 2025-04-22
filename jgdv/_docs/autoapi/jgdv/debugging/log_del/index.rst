 

 
.. _jgdv.debugging.log_del:
   
    
======================
jgdv.debugging.log_del
======================

   
.. py:module:: jgdv.debugging.log_del

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
 

Functions
---------

.. autoapisummary::

    jgdv.debugging.log_del.LogDel
    jgdv.debugging.log_del._decorate_del
    jgdv.debugging.log_del._log_del
           
 
  
           
 
      
 
Module Contents
===============

 
.. py:function:: LogDel(cls: type) -> type

   A Class Decorator, attaches a debugging statement to the object destructor
   To activate, add classvar of {jgdv.debugging._interface.DEL_LOG_K} = True
   to the class.


 
.. py:function:: _decorate_del(fn: jgdv.Func[Ellipsis, None]) -> jgdv.Func[Ellipsis, None]

   wraps existing del method


 
.. py:function:: _log_del(self: Any) -> None

   standalone del logging


 
   
