 

 
.. _jgdv.cli.param_spec.positional:
   
    
==============================
jgdv.cli.param_spec.positional
==============================

   
.. py:module:: jgdv.cli.param_spec.positional

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.param_spec.positional.PositionalParam
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.param_spec.positional.PositionalParam:
   
.. py:class:: PositionalParam(/, **data: Any)
   
   Bases: :py:obj:`jgdv.cli.param_spec._base.ParamSpecBase` 
     
   TODO a param that is specified by its position in the arg list

   
   .. py:method:: key_str() -> str

      Get how the param needs to be written in the cli.

      | eg: -test or --test


   .. py:method:: matches_head(val) -> bool

   .. py:method:: next_value(args: list) -> tuple[str, list, int]

 
 
   
