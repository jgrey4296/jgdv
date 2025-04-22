 

 
.. _jgdv.mixins.enum_builders:
   
    
=========================
jgdv.mixins.enum_builders
=========================

   
.. py:module:: jgdv.mixins.enum_builders

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.mixins.enum_builders.EnumBuilder_m
    jgdv.mixins.enum_builders.FlagsBuilder_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.mixins.enum_builders.EnumBuilder_m:
   
.. py:class:: EnumBuilder_m
   
    
   A Mixin to add a .build(str) method for the enum

   
   .. py:method:: build(val: str, *, strict=True) -> Self
      :classmethod:


 
 
 

.. _jgdv.mixins.enum_builders.FlagsBuilder_m:
   
.. py:class:: FlagsBuilder_m
   
    
   A Mixin to add a .build(vals) method for EnumFlags

   
   .. py:method:: build(vals: str | list | dict, *, strict=True) -> Self
      :classmethod:


 
 
   
