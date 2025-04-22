 

 
.. _jgdv.files.tags.tag_file:
   
    
========================
jgdv.files.tags.tag_file
========================

   
.. py:module:: jgdv.files.tags.tag_file

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.files.tags.tag_file.TagFile
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.files.tags.tag_file.TagFile:
   
.. py:class:: TagFile(/, **data: Any)
   
   Bases: :py:obj:`pydantic.BaseModel` 
     
   A Basic TagFile holds the counts for each tag use

   Tag file format is single lines of:
   ^{tag} {sep} {count}$

   cls.read can be used to change the {sep}

   # TODO use a collections.Counter

   
   .. py:method:: _inc(key: str, *, amnt: int = 1) -> jgdv.Maybe[str]

   .. py:method:: _normalize_counts() -> Self

   .. py:method:: _validate_counts(val: dict) -> dict

   .. py:method:: _validate_regex(val: str | jgdv.Rx) -> jgdv.Rx

   .. py:method:: get_count(tag: str) -> int

   .. py:method:: norm_tag(tag: str) -> str

   .. py:method:: read(fpath: pathlib.Path, **kwargs: dict) -> TagFile
      :classmethod:


   .. py:method:: to_set() -> set[str]

   .. py:method:: update(*values: str | TagFile | set | dict) -> Self

   .. py:attribute:: comment
      :type:  str
      :value: '%%'


   .. py:attribute:: counts
      :type:  dict[str, int]

   .. py:attribute:: ext
      :type:  str
      :value: '.tags'


   .. py:attribute:: norm_regex
      :type:  jgdv.Rx

   .. py:attribute:: norm_replace
      :type:  str
      :value: '_'


   .. py:attribute:: sep
      :type:  str
      :value: ' : '


 
 
   
