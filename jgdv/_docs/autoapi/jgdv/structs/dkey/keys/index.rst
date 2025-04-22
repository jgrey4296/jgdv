 

 
.. _jgdv.structs.dkey.keys:
   
    
======================
jgdv.structs.dkey.keys
======================

   
.. py:module:: jgdv.structs.dkey.keys

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.keys.IndirectDKey
    jgdv.structs.dkey.keys.MultiDKey
    jgdv.structs.dkey.keys.NonDKey
    jgdv.structs.dkey.keys.SingleDKey
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.dkey.keys.IndirectDKey:
   
.. py:class:: IndirectDKey(data, multi=False, re_mark=None, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.dkey.core.base.DKeyBase` 
     
   A Key for getting a redirected key.
   eg: RedirectionDKey(key) -> SingleDKey(value)

   re_mark :

   
   .. py:method:: exp_pre_lookup_h(sources, opts) -> list[list[jgdv.structs.dkey._interface.ExpInst_d]]

      Lookup the indirect version, the direct version, then use the fallback


   .. py:attribute:: multi_redir
      :value: False


   .. py:attribute:: re_mark
      :value: None


 
 
 

.. _jgdv.structs.dkey.keys.MultiDKey:
   
.. py:class:: MultiDKey(data: str | pathlib.Path, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.dkey.core.base.DKeyBase` 
     
   Multi keys allow 1+ explicit subkeys.

   They have additional fields:

   _subkeys  : parsed information about explicit subkeys


   
   .. py:method:: exp_flatten_h(vals: list[jgdv.structs.dkey._interface.ExpInst_d], opts) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]

      Flatten the multi-key expansion into a single string,
      by using the anon-format str


   .. py:method:: exp_pre_lookup_h(sources, opts) -> list[list[jgdv.structs.dkey._interface.ExpInst_d]]

      Lift subkeys to expansion instructions


   .. py:method:: keys() -> list[jgdv.structs.dkey._interface.Key_p]

      Get subkeys of this key. by default, an empty list.
      (named 'keys' to be in keeping with dict)


   .. py:attribute:: _anon
      :value: ''


   .. py:attribute:: _subkeys
      :type:  list[jgdv.structs.dkey.core.parser.RawKey]

   .. py:property:: multi
      :type: bool


      utility property to test if the key is a multikey,
      without having to do reflection
      (to avoid some recursive import issues)

 
 
 

.. _jgdv.structs.dkey.keys.NonDKey:
   
.. py:class:: NonDKey(data, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.dkey.core.base.DKeyBase` 
     
   Just a string, not a key.

   ::

       But this lets you call no-ops for key specific methods.
       It can coerce itself though

   
   .. py:method:: expand(*args, **kwargs) -> jgdv.Maybe

      A Non-key just needs to be coerced into the correct str format


   .. py:method:: format(fmt) -> str

      Just does normal str formatting


   .. py:attribute:: nonkey
      :value: True


 
 
 

.. _jgdv.structs.dkey.keys.SingleDKey:
   
.. py:class:: SingleDKey(data, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.dkey.core.base.DKeyBase` 
     
   A Single key with no extras.
   ie: {x}. not {x}{y}, or {x}.blah.

   
   .. py:method:: _set_params(*, fmt: jgdv.Maybe[str] = None, conv: jgdv.Maybe[str] = None) -> None

      str formatting and conversion parameters.
      These only make sense for single keys, as they need to be wrapped.
      see: https://docs.python.org/3/library/string.html#format-string-syntax


 
 
   
