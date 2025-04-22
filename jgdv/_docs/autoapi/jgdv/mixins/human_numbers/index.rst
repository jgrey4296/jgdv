 

 
.. _jgdv.mixins.human_numbers:
   
    
=========================
jgdv.mixins.human_numbers
=========================

   
.. py:module:: jgdv.mixins.human_numbers

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.mixins.human_numbers.HumanNumbers_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.mixins.human_numbers.HumanNumbers_m:
   
.. py:class:: HumanNumbers_m
   
    
   Simple Mixin for human related functions

   
   .. py:method:: humanize(val: int | float, *, force_sign: bool = True) -> str
      :staticmethod:


      Format {val} in a human readable way as a size.
      Uses tracemalloc._format_size.
      Depending on size, will use on of the units:
      B, KiB, MiB, GiB, TiB.


   .. py:method:: round_time(dt: jgdv.DateTime = None, *, round: jgdv.Seconds = 60) -> jgdv.DateTime
      :staticmethod:


      Round a datetime object to any time lapse in seconds
      dt : datetime.datetime object, default now.
      round : Closest number of seconds to round to, default 1 minute.
      Author: Thierry Husson 2012 - Use it as you want but don't blame me.
      from: https://stackoverflow.com/questions/3463930


 
 
   
