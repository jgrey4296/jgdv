 

 
.. _jgdv.structs.locator.errors:
   
    
===========================
jgdv.structs.locator.errors
===========================

   
.. py:module:: jgdv.structs.locator.errors

       
 

   
 

 

 
   
        

           

 
 

           
   
 

Exceptions
----------

.. autoapisummary::

   jgdv.structs.locator.errors.DirAbsent
   jgdv.structs.locator.errors.LocationError
   jgdv.structs.locator.errors.LocationExpansionError

             
  
           
 
  
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.locator.errors.DirAbsent:
   
.. py:exception:: DirAbsent
   
   Bases: :py:obj:`LocationError` 
     
   In the course of startup verification, a directory was not found

   
   .. py:attribute:: general_msg
      :value: 'Missing Directory:'


 
 
 

.. _jgdv.structs.locator.errors.LocationError:
   
.. py:exception:: LocationError
   
   Bases: :py:obj:`jgdv.structs.strang.errors.StrangError` 
     
   A Task tried to access a location that didn't existing

   
   .. py:attribute:: general_msg
      :value: 'Location Error:'


 
 
 

.. _jgdv.structs.locator.errors.LocationExpansionError:
   
.. py:exception:: LocationExpansionError
   
   Bases: :py:obj:`LocationError` 
     
   When trying to resolve a location, something went wrong.

   
   .. py:attribute:: general_msg
      :value: 'Expansion of Location hit max value:'


 
 
   
