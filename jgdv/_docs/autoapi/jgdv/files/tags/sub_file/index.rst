 

 
.. _jgdv.files.tags.sub_file:
   
    
========================
jgdv.files.tags.sub_file
========================

   
.. py:module:: jgdv.files.tags.sub_file

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.files.tags.sub_file.SubstitutionFile
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.files.tags.sub_file.SubstitutionFile:
   
.. py:class:: SubstitutionFile(/, **data: Any)
   
   Bases: :py:obj:`jgdv.files.tags.tag_file.TagFile` 
     
   SubstitutionFiles add a replacement tag for some tags

   Substitution file format is single lines of:
   ^{tag} {sep} {count} [{sep} {replacement}]*$


   
   .. py:method:: _add_sub(key: str, subs: list[str], *, count: str | int = 1) -> None

   .. py:method:: canonical() -> jgdv.files.tags.tag_file.TagFile

      create a tagfile of just canonical tags


   .. py:method:: has_sub(value: str) -> bool

   .. py:method:: known() -> jgdv.files.tags.tag_file.TagFile

      Get a TagFile of all known tags. both canonical and not


   .. py:method:: sub(value: str) -> set[str]

      apply a substitution if it exists


   .. py:method:: sub_many(*values: str) -> set[str]

   .. py:method:: update(*values: str | tuple | dict | SubstitutionFile | jgdv.files.tags.tag_file.TagFile | set) -> Self

      Overrides TagFile.update to handle tuples of (tag, count, replacements*)
      and (tag, replacements*)


   .. py:attribute:: ext
      :type:  str
      :value: '.sub'


   .. py:attribute:: sep
      :type:  str
      :value: ' : '


   .. py:attribute:: substitutions
      :type:  dict[str, set[str]]

 
 
   
