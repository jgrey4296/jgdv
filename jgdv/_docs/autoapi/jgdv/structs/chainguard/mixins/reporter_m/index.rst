 

 
.. _jgdv.structs.chainguard.mixins.reporter_m:
   
    
=========================================
jgdv.structs.chainguard.mixins.reporter_m
=========================================

   
.. py:module:: jgdv.structs.chainguard.mixins.reporter_m

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.chainguard.mixins.reporter_m.DefaultedReporter_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.chainguard.mixins.reporter_m.DefaultedReporter_m:
   
.. py:class:: DefaultedReporter_m
   
    
   A Mixin for reporting values that a failure proxy defaulted on.

   
   .. py:method:: add_defaulted(index: str | list[str], val: jgdv.structs.chainguard._interface.TomlTypes, types: str = 'Any') -> None
      :staticmethod:


   .. py:method:: report_defaulted() -> list[str]
      :staticmethod:


      Report the index paths inject default values


   .. py:attribute:: _defaulted
      :type:  ClassVar[set[str]]

 
 
   
