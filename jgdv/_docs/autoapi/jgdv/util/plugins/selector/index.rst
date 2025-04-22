 

 
.. _jgdv.util.plugins.selector:
   
    
==========================
jgdv.util.plugins.selector
==========================

   
.. py:module:: jgdv.util.plugins.selector

.. autoapi-nested-parse::

   A function to select an appropriate plugin by passed in name or names

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
 

Functions
---------

.. autoapisummary::

    jgdv.util.plugins.selector.plugin_selector
           
 
  
           
 
      
 
Module Contents
===============

 
.. py:function:: plugin_selector(plugins: jgdv.structs.chainguard.ChainGuard, *, target: str = 'default', fallback: jgdv.Maybe[type] = None) -> jgdv.Maybe[type]

   Selects and loads a plugin from a chainguard,
   based on a target,
   with an available fallback constructor


 
   
