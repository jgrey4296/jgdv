 

 
.. _jgdv.structs.dkey.core.meta:
   
    
===========================
jgdv.structs.dkey.core.meta
===========================

   
.. py:module:: jgdv.structs.dkey.core.meta

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.core.meta.DKey
    jgdv.structs.dkey.core.meta.DKeyMeta
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.dkey.core.meta.DKey:
   
.. py:class:: DKey
   
   Bases: :py:obj:`str` 
     
   A facade for DKeys and variants.
   Implements __new__ to create the correct key type, from a string, dynamically.

   kwargs:
   explicit = insists that keys in the string are wrapped in braces '{akey} {anotherkey}'.
   mark     = pre-register expansion parameters / type etc
   check    = dictate a type that expanding this key must match
   fparams  = str formatting instructions for the key

   Eg:
   DKey('blah')
   -> SingleDKey('blah')
   -> SingleDKey('blah').format('w')
   -> '{blah}'
   -> [toml] aValue = '{blah}'

   Because cls.__new__ calls __init__ automatically for return values of type cls,
   DKey is the factory, but all DKeys are subclasses of DKeyBase,
   to allow control over __init__.

   
   .. py:method:: MarkOf(target: DKey) -> jgdv.structs.dkey._interface.KeyMark
      :staticmethod:


      Get the mark of the key type or instance


   .. py:method:: add_sources(*sources) -> None
      :classmethod:


      register additional sources that are always included


   .. py:attribute:: ExpInst
      :type:  ClassVar[type]

   .. py:attribute:: Mark
      :type:  ClassVar[enum.EnumMeta]

   .. py:attribute:: __match_args
      :value: ('_mark',)


   .. py:attribute:: _extra_sources
      :type:  ClassVar[list[dict]]
      :value: []


 
 
 

.. _jgdv.structs.dkey.core.meta.DKeyMeta:
   
.. py:class:: DKeyMeta
   
   Bases: :py:obj:`StrMeta` 
     
     The Metaclass for keys, which ensures that subclasses of DKeyBase
     are DKey's, despite there not being an actual subclass relation between them.

   This allows DKeyBase to actually bottom out at str

   
   .. py:method:: extract_raw_keys(data: str, *, implicit=False) -> list[jgdv.structs.dkey.core.parser.RawKey]
      :staticmethod:


      Calls the Python format string parser to extract
      keys and their formatting/conversion specs.

      if 'implicit' then will parse the entire string as {str}


   .. py:method:: get_subtype(mark: jgdv.structs.dkey._interface.KeyMark, *, multi=False) -> type
      :staticmethod:


      Get the Ctor for a given mark from those registered.


   .. py:method:: mark_alias(val: Any) -> jgdv.Maybe[jgdv.structs.dkey._interface.KeyMark]
      :staticmethod:


      aliases for marks


   .. py:method:: register_key_type(ctor: type, mark: jgdv.structs.dkey._interface.KeyMark, conv: jgdv.Maybe[str] = None, multi: bool = False) -> None
      :staticmethod:


      Register a DKeyBase implementation to a mark

      Can be a single key, or a multi key,
      and can map a conversion char to the mark

      eg: "p" -> DKeyMark_e.Path -> Path[Single/Multi]Key


   .. py:attribute:: _conv_registry
      :type:  ClassVar[dict[str, jgdv.structs.dkey._interface.KeyMark]]

   .. py:attribute:: _expected_init_keys
      :type:  ClassVar[list[str]]

   .. py:attribute:: _multi_registry
      :type:  ClassVar[dict[jgdv.structs.dkey._interface.KeyMark, type]]

   .. py:attribute:: _parser
      :type:  ClassVar[jgdv.structs.dkey.core.parser.DKeyParser]

   .. py:attribute:: _single_registry
      :type:  ClassVar[dict[jgdv.structs.dkey._interface.KeyMark, type]]

 
 
   
