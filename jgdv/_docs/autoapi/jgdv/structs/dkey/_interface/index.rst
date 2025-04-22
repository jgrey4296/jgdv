 

 
.. _jgdv.structs.dkey._interface:
   
    
============================
jgdv.structs.dkey._interface
============================

   
.. py:module:: jgdv.structs.dkey._interface

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.structs.dkey._interface.KeyMark

        

 
 
   
Enums
-----

.. autoapisummary::

   jgdv.structs.dkey._interface.DKeyMark_e

           

 
 

 
 

Protocols
---------

.. autoapisummary::

   jgdv.structs.dkey._interface.Expandable_p
   jgdv.structs.dkey._interface.Key_p

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey._interface.ExpInst_d
           
 
      
 
Module Contents
===============

 
.. py:data:: KeyMark
   :type:  TypeAlias
   :value: DKeyMark_e | str | type


 
 

.. _jgdv.structs.dkey._interface.DKeyMark_e:
   
.. py:class:: DKeyMark_e
   
   Bases: :py:obj:`jgdv.mixins.enum_builders.EnumBuilder_m`, :py:obj:`enum.StrEnum` 
     
   Enums for how to use/build a dkey


   
   .. py:attribute:: ARGS

   .. py:attribute:: CODE

   .. py:attribute:: FREE
      :value: 'free'


   .. py:attribute:: IDENT

   .. py:attribute:: INDIRECT
      :value: 'indirect'


   .. py:attribute:: KWARGS

   .. py:attribute:: MULTI

   .. py:attribute:: NULL

   .. py:attribute:: PATH

   .. py:attribute:: POSTBOX

   .. py:attribute:: STR

   .. py:attribute:: default

 
 
 

.. _jgdv.structs.dkey._interface.Expandable_p:
   
.. py:class:: Expandable_p
   
   Bases: :py:obj:`Protocol` 
     
   An expandable, like a DKey,
   uses these hooks to customise the expansion

   
   .. py:method:: exp_check_result_h(val: ExpInst_d, opts) -> None

   .. py:method:: exp_coerce_h(val: ExpInst_d, opts) -> jgdv.Maybe[ExpInst_d]

   .. py:method:: exp_extra_sources_h() -> jgdv.Maybe[list]

   .. py:method:: exp_final_h(val: ExpInst_d, opts) -> jgdv.Maybe[LitFalse | ExpInst_d]

   .. py:method:: exp_flatten_h(vals: list[ExpInst_d], opts) -> jgdv.Maybe[LitFalse | ExpInst_d]

   .. py:method:: exp_pre_lookup_h(sources, opts) -> jgdv.Maybe[LookupList]

   .. py:method:: exp_pre_recurse_h(vals: list[ExpInst_d], sources, opts) -> jgdv.Maybe[list[ExpInst_d]]

   .. py:method:: expand(*args, **kwargs) -> jgdv.Maybe

 
 
 

.. _jgdv.structs.dkey._interface.Key_p:
   
.. py:class:: Key_p
   
   Bases: :py:obj:`Protocol` 
     
   The protocol for a Key, something that used in a template system

   
   .. py:method:: expand(spec=None, state=None, *, rec=False, insist=False, chain: jgdv.Maybe[list[Key_p]] = None, on_fail=Any, locs: jgdv.Maybe[collections.abc.Mapping] = None, **kwargs) -> str

   .. py:method:: keys() -> list[Key_p]

   .. py:method:: redirect(spec=None) -> Key_p

   .. py:property:: multi
      :type: bool


 
 
 

.. _jgdv.structs.dkey._interface.ExpInst_d:
   
.. py:class:: ExpInst_d(**kwargs)
   
    
   The lightweight holder of expansion instructions, passed through the
   expander mixin.
   Uses slots to make it as lightweight as possible


   
   .. py:attribute:: convert

   .. py:attribute:: fallback

   .. py:attribute:: lift

   .. py:attribute:: literal

   .. py:attribute:: rec

   .. py:attribute:: total_recs

 
 
   
