 

 
.. _jgdv.logging.filter.simple:
   
    
==========================
jgdv.logging.filter.simple
==========================

   
.. py:module:: jgdv.logging.filter.simple

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.filter.simple.SimpleFilter
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.logging.filter.simple.SimpleFilter:
   
.. py:class:: SimpleFilter(allow: jgdv.Maybe[list[RxStr]] = None, reject: jgdv.Maybe[list[str]] = None)
   
    
   A Simple filter to reject based on:
   1) a whitelist of regexs,
   2) a simple list of rejection names


   
   .. py:attribute:: allowed
      :value: []


   .. py:attribute:: allowed_re

   .. py:attribute:: rejections
      :value: []


 
 
   
