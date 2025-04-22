 

 
.. _jgdv.cli.param_spec.defaults:
   
    
============================
jgdv.cli.param_spec.defaults
============================

   
.. py:module:: jgdv.cli.param_spec.defaults

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.param_spec.defaults.HelpParam
    jgdv.cli.param_spec.defaults.SeparatorParam
    jgdv.cli.param_spec.defaults.VerboseParam
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.param_spec.defaults.HelpParam:
   
.. py:class:: HelpParam(**kwargs)
   
   Bases: :py:obj:`jgdv.cli.param_spec.core.ToggleParam` 
     
   The --help flag that is always available

   
 
 
 

.. _jgdv.cli.param_spec.defaults.SeparatorParam:
   
.. py:class:: SeparatorParam(**kwargs)
   
   Bases: :py:obj:`jgdv.cli.param_spec.core.LiteralParam` 
     
   A Parameter to separate subcmds

   
 
 
 

.. _jgdv.cli.param_spec.defaults.VerboseParam:
   
.. py:class:: VerboseParam(**kwargs)
   
   Bases: :py:obj:`jgdv.cli.param_spec.core.RepeatToggleParam` 
     
   The implicit -verbose flag

   
 
 
   
