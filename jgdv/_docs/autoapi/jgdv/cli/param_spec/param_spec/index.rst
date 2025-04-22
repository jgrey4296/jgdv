 

 
.. _jgdv.cli.param_spec.param_spec:
   
    
==============================
jgdv.cli.param_spec.param_spec
==============================

   
.. py:module:: jgdv.cli.param_spec.param_spec

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.param_spec.param_spec.ParamSpec
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.param_spec.param_spec.ParamSpec:
   
.. py:class:: ParamSpec
   
    
   A Top Level Access point for building param specs

   
   .. py:method:: _discrim_data(data: dict) -> jgdv.Maybe[type]
      :staticmethod:


      Extract from data dict values to determine sort of param


   .. py:method:: _discrim_to_type(data: jgdv.Maybe[type | str | tuple[str, type]]) -> jgdv.Maybe[type]
      :staticmethod:


      Determine what sort of parameter to use.
      Literals: assign, position, "toggle"

      Default: KEyParam



   .. py:method:: build(data: dict) -> jgdv.cli.param_spec._base.ParamSpecBase
      :classmethod:


   .. py:method:: key_func(x)
      :classmethod:


   .. py:attribute:: _override_type
      :type:  ClassVar[type | str]
      :value: None


 
 
   
