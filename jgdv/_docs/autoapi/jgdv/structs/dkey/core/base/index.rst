 

 
.. _jgdv.structs.dkey.core.base:
   
    
===========================
jgdv.structs.dkey.core.base
===========================

   
.. py:module:: jgdv.structs.dkey.core.base

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.structs.dkey.core.base.KeyMark

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.core.base.DKeyBase
           
 
      
 
Module Contents
===============

 
.. py:data:: KeyMark
   :type:  TypeAlias
   :value: API.KeyMark


 
 

.. _jgdv.structs.dkey.core.base.DKeyBase:
   
.. py:class:: DKeyBase(data: str, **kwargs)
   
   Bases: :py:obj:`jgdv.mixins.annotate.SubAnnotate_m`, :py:obj:`str` 
     
     Base class for implementing actual DKeys.
     adds:
     `_mark`
     `_expansion_type`
     `_typecheck`

     plus some util methods

   init takes kwargs:
   fmt, mark, check, ctor, help, fallback, max_exp

   on class definition, can register a 'mark', 'multi', and a conversion parameter str

   
   .. py:method:: _set_help(help: jgdv.Maybe[str]) -> Self

   .. py:method:: exp_check_result_h(val: jgdv.structs.dkey._interface.ExpInst_d, opts) -> None

   .. py:method:: exp_coerce_h(val: jgdv.structs.dkey._interface.ExpInst_d, opts) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]

   .. py:method:: exp_extra_sources_h() -> list

   .. py:method:: exp_final_h(val: jgdv.structs.dkey._interface.ExpInst_d, opts) -> jgdv.Maybe[LitFalse | jgdv.structs.dkey._interface.ExpInst_d]

   .. py:method:: exp_flatten_h(vals: list[jgdv.structs.dkey._interface.ExpInst_d], opts) -> jgdv.Maybe[LitFalse | jgdv.structs.dkey._interface.ExpInst_d]

   .. py:method:: exp_pre_lookup_h(sources, opts) -> jgdv.Maybe[LookupList]

   .. py:method:: exp_pre_recurse_h(vals: list[jgdv.structs.dkey._interface.ExpInst_d], sources, opts) -> jgdv.Maybe[list[jgdv.structs.dkey._interface.ExpInst_d]]

   .. py:method:: expand(*args, **kwargs) -> jgdv.Maybe

   .. py:method:: keys() -> list[jgdv.structs.dkey._interface.Key_p]

      Get subkeys of this key. by default, an empty list.
      (named 'keys' to be in keeping with dict)


   .. py:method:: redirect(*args, **kwargs) -> list[jgdv.structs.dkey.core.meta.DKey]

   .. py:method:: var_name() -> str

      When testing the dkey for its inclusion in a decorated functions signature,
      this gives the 'named' val if its not None, otherwise the str of the key


   .. py:attribute:: _conv_params
      :type:  jgdv.Maybe[jgdv.FmtStr]

   .. py:attribute:: _expansion_type
      :type:  jgdv.Ctor

   .. py:attribute:: _extra_kwargs
      :type:  ClassVar[set[str]]

   .. py:attribute:: _fallback
      :type:  jgdv.Maybe[Any]

   .. py:attribute:: _fmt_params
      :type:  jgdv.Maybe[jgdv.FmtStr]

   .. py:attribute:: _help
      :type:  jgdv.Maybe[str]

   .. py:attribute:: _mark
      :type:  KeyMark

   .. py:attribute:: _max_expansions

   .. py:attribute:: _named
      :type:  jgdv.Maybe[str]

   .. py:attribute:: _typecheck
      :type:  jgdv.CHECKTYPE

   .. py:property:: multi
      :type: bool


      utility property to test if the key is a multikey,
      without having to do reflection
      (to avoid some recursive import issues)

 
 
   
