 

 
.. _jgdv.structs.dkey.core.parser:
   
    
=============================
jgdv.structs.dkey.core.parser
=============================

   
.. py:module:: jgdv.structs.dkey.core.parser

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.core.parser.DKeyParser
    jgdv.structs.dkey.core.parser.RawKey
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.dkey.core.parser.DKeyParser:
   
.. py:class:: DKeyParser
   
    
   Parser for extracting {}-format params from strings.

   ::

       see: https://peps.python.org/pep-3101/
       and: https://docs.python.org/3/library/string.html#format-string-syntax

   
   .. py:method:: make_param(*args)

   .. py:method:: parse(format_string, *, implicit=False) -> collections.abc.Iterator[RawKey]

 
 
 

.. _jgdv.structs.dkey.core.parser.RawKey:
   
.. py:class:: RawKey(/, **data: Any)
   
   Bases: :py:obj:`pydantic.BaseModel` 
     
   Utility class for parsed {}-format string parameters.

   ::

       see: https://peps.python.org/pep-3101/
       and: https://docs.python.org/3/library/string.html#format-string-syntax

   Provides the data from string.Formatter.parse, but in a structure
   instead of a tuple.

   
   .. py:method:: _validate_conv(val)

      Ensure the conv params are valid


   .. py:method:: _validate_format(val: str) -> str

      Ensure the format params are valid


   .. py:method:: anon() -> str

      Make a format str of this key, with anon variables.

      eg: blah {key:f!p} -> blah {}


   .. py:method:: direct() -> str

      Returns this key in direct form

      ::

          eg: blah -> blah
              blah_ -> blah


   .. py:method:: indirect() -> str

      Returns this key in indirect form

      ::

          eg: blah -> blah_
              blah_ -> blah_


   .. py:method:: is_indirect() -> bool

   .. py:method:: joined() -> str

      Returns the key and params as one string

      eg: blah, fmt=5, conv=p -> blah:5!p


   .. py:method:: wrapped() -> str

      Returns this key in simple wrapped form

      (it ignores format, conv params and prefix)

      eg: blah -> {blah}


   .. py:attribute:: conv
      :type:  jgdv.Maybe[str]
      :value: None


   .. py:attribute:: format
      :type:  jgdv.Maybe[str]
      :value: None


   .. py:attribute:: key
      :type:  jgdv.Maybe[str]
      :value: None


   .. py:attribute:: prefix
      :type:  jgdv.Maybe[str]
      :value: ''


 
 
   
