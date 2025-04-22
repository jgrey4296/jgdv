 

 
.. _jgdv.structs.strang.code_ref:
   
    
============================
jgdv.structs.strang.code_ref
============================

   
.. py:module:: jgdv.structs.strang.code_ref

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.structs.strang.code_ref.SpecialType

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.strang.code_ref.CodeReference
           
 
      
 
Module Contents
===============

 
.. py:data:: SpecialType
   :type:  TypeAlias
   :value: typing._SpecialForm


 
 

.. _jgdv.structs.strang.code_ref.CodeReference:
   
.. py:class:: CodeReference(*, value: jgdv.Maybe[type] = None, check: jgdv.Maybe[type] = None, **kwargs: Any)
   
   Bases: :py:obj:`jgdv.structs.strang.strang.Strang` 
     
   A reference to a class or function.

   can be created from a string (so can be used from toml),
   or from the actual object (from in python)

   Has the form::

       [cls::]module.a.b.c:ClassName

   Can be built with an imported value directly, and a type to check against

   __call__ imports the reference

   
   .. py:method:: _do_import(*, check: jgdv.Maybe[SpecialType | type]) -> Any

   .. py:method:: _post_process() -> None

      go through body elements, and parse UUIDs, markers, param
      setting self._body_meta and self._mark_idx


   .. py:method:: from_value(value: Any) -> CodeReference
      :classmethod:


   .. py:method:: module() -> str

   .. py:method:: pre_process(data: str, *, strict: bool = False) -> str
      :classmethod:


   .. py:method:: to_alias(group: str, plugins: dict | jgdv.structs.chainguard.ChainGuard) -> str

      TODO Given a nested dict-like, see if this reference can be reduced to an alias


   .. py:method:: to_uniq() -> Never
      :abstractmethod:


   .. py:method:: value() -> str

   .. py:method:: with_head() -> Never
      :abstractmethod:


   .. py:attribute:: _body_types
      :type:  ClassVar[Any]

   .. py:attribute:: _separator
      :type:  ClassVar[str]
      :value: '::'


   .. py:attribute:: _tail_separator
      :type:  ClassVar[str]
      :value: ':'


   .. py:attribute:: _value
      :type:  jgdv.Maybe[type]
      :value: None


   .. py:attribute:: _value_idx
      :type:  slice

   .. py:attribute:: gmark_e
      :type:  ClassVar[enum.StrEnum]

 
 
   
