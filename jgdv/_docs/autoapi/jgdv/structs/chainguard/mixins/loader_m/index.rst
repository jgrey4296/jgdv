 

 
.. _jgdv.structs.chainguard.mixins.loader_m:
   
    
=======================================
jgdv.structs.chainguard.mixins.loader_m
=======================================

   
.. py:module:: jgdv.structs.chainguard.mixins.loader_m

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.structs.chainguard.mixins.loader_m.T

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.chainguard.mixins.loader_m.TomlLoader_m
           
 
      
 
Module Contents
===============

 
.. py:data:: T
   :type:  TypeAlias
   :value: TypeVar('T')


 
 

.. _jgdv.structs.chainguard.mixins.loader_m.TomlLoader_m:
   
.. py:class:: TomlLoader_m
   
    
   Mixin for loading toml files

   
   .. py:method:: from_dict(data: dict[str, jgdv.structs.chainguard._interface.TomlTypes]) -> Self
      :classmethod:


   .. py:method:: load(*paths: str | pathlib.Path) -> Self
      :classmethod:


   .. py:method:: load_dir(dirp: str | pathlib.Path) -> Self
      :classmethod:


   .. py:method:: read(text: str) -> T
      :classmethod:


 
 
   
