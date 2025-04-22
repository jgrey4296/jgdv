 

 
.. _jgdv.logging.format.colour:
   
    
==========================
jgdv.logging.format.colour
==========================

   
.. py:module:: jgdv.logging.format.colour

.. autoapi-nested-parse::

   see `Alexandra Zaharia <https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/>`_

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.logging.format.colour.StyleChar

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.format.colour.ColourFormatter
    jgdv.logging.format.colour.StripColourFormatter
           
 
      
 
Module Contents
===============

 
.. py:data:: StyleChar
   :type:  TypeAlias
   :value: Literal['%', '{', '$']


 
 

.. _jgdv.logging.format.colour.ColourFormatter:
   
.. py:class:: ColourFormatter(*, fmt: jgdv.Maybe[str] = None, style: jgdv.Maybe[StyleChar] = None)
   
   Bases: :py:obj:`logging.Formatter` 
     
   Stream Formatter for logging, enables use of colour sent to console

   Guarded Formatter for adding colour.
   Uses the sty module.
   If sty is missing, behaves as the default formatter class

   # Do *not* use for on filehandler
   Usage reminder:
   # Create stdout handler for logging to the console (logs all five levels)
   stdout_handler = logging.StreamHandler()
   stdout_handler.setFormatter(ColourFormatter(fmt))
   logger.addHandler(stdout_handler)

   
   .. py:method:: apply_colour_mapping(mapping: dict[int | str, tuple[str, str]]) -> None

      applies a mapping of colours by treating each value as a pair of attrs of sty

      eg: {logging.DEBUG: ("fg", "blue"), logging.INFO: ("bg", "red")}


   .. py:method:: format(record: logging.LogRecord) -> str

      Format the specified record as text.

      The record's attribute dictionary is used as the operand to a
      string formatting operation which yields the returned string.
      Before formatting the dictionary, a couple of preparatory steps
      are carried out. The message attribute of the record is computed
      using LogRecord.getMessage(). If the formatting string uses the
      time (as determined by a call to usesTime(), formatTime() is
      called to format the event time. If there is exception information,
      it is formatted using formatException() and appended to the message.


   .. py:attribute:: _default_date_fmt
      :type:  str
      :value: '%H:%M:%S'


   .. py:attribute:: _default_fmt
      :type:  str
      :value: '{asctime} | {levelname:9} | {message}'


   .. py:attribute:: _default_style
      :type:  StyleChar
      :value: '{'


   .. py:attribute:: colours
      :type:  dict[int | str, str]

 
 
 

.. _jgdv.logging.format.colour.StripColourFormatter:
   
.. py:class:: StripColourFormatter(*, fmt: jgdv.Maybe[str] = None, style: jgdv.Maybe[StyleChar] = None)
   
   Bases: :py:obj:`logging.Formatter` 
     
   Force Colour Command codes to be stripped out of a string.
   Useful for when you redirect printed strings with colour
   to a file

   
   .. py:method:: format(record: logging.LogRecord) -> str

      Format the specified record as text.

      The record's attribute dictionary is used as the operand to a
      string formatting operation which yields the returned string.
      Before formatting the dictionary, a couple of preparatory steps
      are carried out. The message attribute of the record is computed
      using LogRecord.getMessage(). If the formatting string uses the
      time (as determined by a call to usesTime(), formatTime() is
      called to format the event time. If there is exception information,
      it is formatted using formatException() and appended to the message.


   .. py:attribute:: _colour_strip_re
      :type:  jgdv.Rx

   .. py:attribute:: _default_date_fmt
      :type:  str
      :value: '%Y-%m-%d %H:%M:%S'


   .. py:attribute:: _default_fmt
      :type:  str
      :value: '{asctime} | {levelname:9} | {shortname:25} | {message}'


   .. py:attribute:: _default_style
      :type:  StyleChar
      :value: '{'


 
 
   
