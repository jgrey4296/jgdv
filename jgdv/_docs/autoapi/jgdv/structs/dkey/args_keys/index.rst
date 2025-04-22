 

 
.. _jgdv.structs.dkey.args_keys:
   
    
===========================
jgdv.structs.dkey.args_keys
===========================

   
.. py:module:: jgdv.structs.dkey.args_keys

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.args_keys.ArgsDKey
    jgdv.structs.dkey.args_keys.KwargsDKey
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.dkey.args_keys.ArgsDKey:
   
.. py:class:: ArgsDKey(*args, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.dkey.keys.SingleDKey` 
     
   A Key representing the action spec's args

   
   .. py:method:: expand(*sources, **kwargs) -> list

      args are simple, just get the first specstruct's args value


   .. py:attribute:: _expansion_type

   .. py:attribute:: _typecheck

 
 
 

.. _jgdv.structs.dkey.args_keys.KwargsDKey:
   
.. py:class:: KwargsDKey(*args, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.dkey.keys.SingleDKey` 
     
   A Key representing all of an action spec's kwargs

   
   .. py:method:: expand(*sources, fallback=None, **kwargs) -> dict

      kwargs are easy, just get the first specstruct's kwargs value


   .. py:attribute:: _expansion_type

   .. py:attribute:: _typecheck

 
 
   
