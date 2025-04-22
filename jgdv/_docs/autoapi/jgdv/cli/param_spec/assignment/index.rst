 

 
.. _jgdv.cli.param_spec.assignment:
   
    
==============================
jgdv.cli.param_spec.assignment
==============================

   
.. py:module:: jgdv.cli.param_spec.assignment

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.param_spec.assignment.AssignParam
    jgdv.cli.param_spec.assignment.WildcardParam
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.param_spec.assignment.AssignParam:
   
.. py:class:: AssignParam(*args, **kwargs)
   
   Bases: :py:obj:`jgdv.cli.param_spec._base.ParamSpecBase` 
     
   TODO a joined --key=val param

   
   .. py:method:: next_value(args: list) -> tuple[str, list, int]

      get the value for a --key=val


 
 
 

.. _jgdv.cli.param_spec.assignment.WildcardParam:
   
.. py:class:: WildcardParam(*args, **kwargs)
   
   Bases: :py:obj:`AssignParam` 
     
   TODO a wildcard param that matches any --{key}={val}

   
   .. py:method:: matches_head(val) -> bool

   .. py:method:: next_value(args: list) -> tuple[str, list, int]

      get the value for a --key=val


 
 
   
