 

 
.. _jgdv.structs.dkey.core.formatter:
   
    
================================
jgdv.structs.dkey.core.formatter
================================

   
.. py:module:: jgdv.structs.dkey.core.formatter

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.core.formatter.DKeyFormatter
    jgdv.structs.dkey.core.formatter._DKeyFormatterEntry_m
    jgdv.structs.dkey.core.formatter._DKeyFormatter_Expansion_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.dkey.core.formatter.DKeyFormatter:
   
.. py:class:: DKeyFormatter
   
   Bases: :py:obj:`string.Formatter` 
     
   An Expander/Formatter to extend string formatting with options useful for dkey's
   and doot specs/state.


   
   .. py:method:: convert_field(value, conversion)

   .. py:method:: format(key: str | jgdv.structs.dkey._interface.Key_p, /, *args, **kwargs) -> str

      format keys as strings


   .. py:method:: format_field(val, spec) -> str
      :staticmethod:


      Take a value and a formatting spec, and apply that formatting


   .. py:method:: get_value(key, args, kwargs) -> str

      lowest level handling of keys being expanded


 
 
 

.. jgdv.structs.dkey.core.formatter._DKeyFormatterEntry_m:
   
.. py:class:: _DKeyFormatterEntry_m
   
    
   Mixin to make DKeyFormatter a singleton with static access

   and makes the formatter a context manager, to hold the current data sources

   
   .. py:method:: Parse(key: jgdv.structs.dkey._interface.Key_p | pathlib.Path) -> tuple(bool, list[RawKey])
      :classmethod:


      Use the python c formatter parser to extract keys from a string
      of form (prefix, key, format, conversion)

      Returns: (bool: non-key text), list[(key, format, conv)]

      see: cpython Lib/string.py
      and: cpython Objects/stringlib/unicode_format.h

      eg: '{test:w} :: {blah}' -> False, [('test', Any, Any), ('blah', Any, Any)]


   .. py:method:: expand(key: jgdv.structs.dkey._interface.Key_p, *, sources=None, max=None, **kwargs) -> jgdv.Maybe[Any]
      :classmethod:


      static method to a singleton key formatter


   .. py:method:: fmt(key: jgdv.structs.dkey._interface.Key_p | str, /, *args, **kwargs) -> str
      :classmethod:


      static method to a singleton key formatter


   .. py:method:: redirect(key: jgdv.structs.dkey._interface.Key_p, *, sources=None, **kwargs) -> list[jgdv.structs.dkey._interface.Key_p | str]
      :classmethod:


      static method to a singleton key formatter


   .. py:attribute:: _entered
      :type:  bool
      :value: False


   .. py:attribute:: _instance
      :type:  ClassVar[Self]
      :value: None


   .. py:attribute:: _original_key
      :type:  str | jgdv.structs.dkey._interface.Key_p
      :value: None


   .. py:attribute:: fallback
      :type:  Any
      :value: None


   .. py:attribute:: rec_remaining
      :type:  int
      :value: 200


   .. py:attribute:: sources
      :type:  list
      :value: []


 
 
 

.. jgdv.structs.dkey.core.formatter._DKeyFormatter_Expansion_m:
   
.. py:class:: _DKeyFormatter_Expansion_m
   
    
   A Mixin for  DKeyFormatter, to expand keys without recursion

   
   .. py:method:: _expand(key: jgdv.structs.dkey._interface.Key_p, *, fallback=None, count=DEFAULT_COUNT) -> jgdv.Maybe[Any]

      Expand the key, returning fallback if it fails,
      counting each loop as `count` attempts



   .. py:method:: _multi_expand(key: jgdv.structs.dkey._interface.Key_p) -> str

      expand a multi key,
      by formatting the anon key version using a sequence of expanded subkeys,
      this allows for duplicate keys to be used differenly in a single multikey


   .. py:method:: _single_expand(key: jgdv.structs.dkey._interface.Key_p, fallback=None) -> jgdv.Maybe[Any]

      Expand a single key up to {rec_remaining} times


   .. py:method:: _try_redirection(key: jgdv.structs.dkey._interface.Key_p) -> list[jgdv.structs.dkey._interface.Key_p]

      Try to redirect a key if necessary,
      if theres no redirection, return the key as a direct key


 
 
   
