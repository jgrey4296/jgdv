 

 
.. _jgdv.structs.dkey.core._getter:
   
    
==============================
jgdv.structs.dkey.core._getter
==============================

   
.. py:module:: jgdv.structs.dkey.core._getter

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.core._getter.ChainGetter
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.dkey.core._getter.ChainGetter:
   
.. py:class:: ChainGetter
   
    
   The core logic to turn a key into a value.

   | Doesn't perform repeated expansions.
   | Tries sources in order.

   TODO replace this with collections.ChainMap ?

   
   .. py:method:: get(key: str, *sources: dict | jgdv._abstract.protocols.SpecStruct_p | jgdv.structs.locator.JGDVLocator, fallback: jgdv.Maybe = None) -> jgdv.Maybe[Any]
      :staticmethod:


      Get a key's value from an ordered sequence of potential sources.

      | Try to get {key} then {key\_} in order of sources passed in.


   .. py:method:: lookup(target: list[jgdv.structs.dkey._interface.ExpInst_d], sources: list) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]
      :staticmethod:


      Handle lookup instructions

      | pass through DKeys and (DKey, ..)
      | lift (str(), True, fallback)
      | don't lift (str(), False, fallback)



 
 
   
