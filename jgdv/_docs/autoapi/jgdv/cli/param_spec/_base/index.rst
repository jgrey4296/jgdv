 

 
.. _jgdv.cli.param_spec._base:
   
    
=========================
jgdv.cli.param_spec._base
=========================

   
.. py:module:: jgdv.cli.param_spec._base

       
 

   
 

 

 
   
        

 
 
   
Enums
-----

.. autoapisummary::

   jgdv.cli.param_spec._base._SortGroups_e

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.param_spec._base.ParamSpecBase
           
 
      
 
Module Contents
===============

 
 

.. jgdv.cli.param_spec._base._SortGroups_e:
   
.. py:class:: _SortGroups_e
   
   Bases: :py:obj:`enum.IntEnum` 
     
   Enum where members are also (and must be) ints

   
   .. py:attribute:: by_pos
      :value: 20


   .. py:attribute:: by_prefix
      :value: 10


   .. py:attribute:: head
      :value: 0


   .. py:attribute:: last
      :value: 99


 
 
 

.. _jgdv.cli.param_spec._base.ParamSpecBase:
   
.. py:class:: ParamSpecBase(/, **data: Any)
   
   Bases: :py:obj:`*PSpecMixins`, :py:obj:`pydantic.BaseModel` 
     
   Declarative CLI Parameter Spec.

   | Declares the param name (turns into {prefix}{name})
   | The value will be parsed into a given {type}, and lifted to a list or set if necessary
   | If given, can have a {default} value.
   | {insist} will cause an error if it isn't parsed

   If {prefix} is a non-empty string, then its positional, and to parse it requires no -key.
   If {prefix} is an int, then the parameter has to be in the correct place in the given args.

   Can have a {desc} to help usage.
   Can be set using a short version of the name ({prefix}{name[0]}).
   If {implicit}, will not be listed when printing a param spec collection.


   
   .. py:method:: help_str(*, force=False)

   .. py:method:: inverse() -> None

   .. py:method:: key_func(x)
      :staticmethod:


      Sort Parameters

      > -{prefix len} < name < int positional < positional < --help



   .. py:method:: key_str() -> str

      Get how the param needs to be written in the cli.

      | eg: -test or --test


   .. py:method:: key_strs() -> list[str]

      all available key-str variations


   .. py:method:: positional() -> bool

   .. py:method:: repeatable()

   .. py:method:: short() -> str

   .. py:method:: short_key_str() -> jgdv.Maybe[str]

   .. py:method:: validate_default(val)

   .. py:method:: validate_model() -> Self

   .. py:method:: validate_type(val: str | type) -> type

   .. py:attribute:: _accumulation_types
      :type:  ClassVar[list[Any]]

   .. py:attribute:: _pad
      :type:  ClassVar[int]
      :value: 15


   .. py:attribute:: _short
      :type:  jgdv.Maybe[str]
      :value: None


   .. py:attribute:: _subtypes
      :type:  dict[type, type]

   .. py:attribute:: count
      :type:  int
      :value: 1


   .. py:attribute:: default
      :type:  Any | Callable
      :value: None


   .. py:attribute:: desc
      :type:  str
      :value: 'An undescribed parameter'


   .. py:attribute:: implicit
      :type:  bool
      :value: False


   .. py:attribute:: insist
      :type:  bool
      :value: False


   .. py:attribute:: name
      :type:  str

   .. py:attribute:: prefix
      :type:  int | str
      :value: '-'


   .. py:attribute:: separator
      :type:  str | Literal[False]
      :value: False


   .. py:attribute:: type_
      :type:  pydantic.InstanceOf[type]
      :value: None


 
 
   
