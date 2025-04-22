 

 
.. _jgdv.structs.dkey.core.expander:
   
    
===============================
jgdv.structs.dkey.core.expander
===============================

   
.. py:module:: jgdv.structs.dkey.core.expander

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.core.expander.Expander
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.dkey.core.expander.Expander:
   
.. py:class:: Expander
   
    
   A Static class to control expansion.

   In order it does::

       - pre-format the value to (A, coerceA,B, coerceB)
       - (lookup A) or (lookup B) or None
       - manipulates the retrieved value
       - potentially recurses on retrieved values
       - type coerces the value
       - runs a post-coercion hook
       - checks the type of the value to be returned

   During the above, the hooks of Expandable_p will be called on the source,
   if they return nothing, the default hook implementation is used.

   All of those steps are fallible.
   When one of them fails, then the expansion tries to return, in order::

       - a fallback value passed into the expansion call
       - a fallback value stored on construction of the key
       - None

   Redirection Rules::

       - Hit          || {test}  => state[test=>blah]  => blah
       - Soft Miss    || {test}  => state[test_=>blah] => {blah}
       - Hard Miss    || {test}  => state[...]         => fallback or None

   Indirect Keys act as::

       - Indirect Soft Hit ||  {test_}  => state[test_=>blah] => {blah}
       - Indirect Hard Hit ||  {test_}  => state[test=>blah]  => blah
       - Indirect Miss     ||  {test_} => state[...]          => {test_}


   
   .. py:method:: _coerce_result_by_conv_param(val, conv, opts, *, source) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]
      :staticmethod:


      really, keys with conv params should been built as a
      specialized registered type, to use an exp_final_hook


   .. py:method:: check_result(source, val: jgdv.structs.dkey._interface.ExpInst_d, opts) -> None
      :staticmethod:


      check the type of the expansion is correct,
      throw a type error otherwise


   .. py:method:: coerce_result(val: jgdv.structs.dkey._interface.ExpInst_d, opts, *, source) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]
      :staticmethod:


      Coerce the expanded value accoring to source's expansion type ctor


   .. py:method:: do_lookup(targets: list[list[jgdv.structs.dkey._interface.ExpInst_d]], sources: list, opts: dict, *, source) -> jgdv.Maybe[list]
      :staticmethod:


      customisable method for each key subtype
      Target is a list (L1) of lists (L2) of target tuples (T).
      For each L2, the first T that returns a value is added to the final result


   .. py:method:: do_recursion(vals: list[jgdv.structs.dkey._interface.ExpInst_d], sources, opts, max_rec=RECURSION_GUARD, *, source) -> jgdv.Maybe[list[jgdv.structs.dkey._interface.ExpInst_d]]
      :staticmethod:


      For values that can expand futher, try to expand them



   .. py:method:: expand(source: jgdv.structs.dkey._interface.Expandable_p, *sources, **kwargs) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]
      :staticmethod:


   .. py:method:: extra_sources(source) -> list[Any]
      :staticmethod:


   .. py:method:: finalise(val: jgdv.structs.dkey._interface.ExpInst_d, opts, *, source) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]
      :staticmethod:


   .. py:method:: flatten(vals: list[jgdv.structs.dkey._interface.ExpInst_d], opts, *, source) -> jgdv.Maybe[jgdv.structs.dkey._interface.ExpInst_d]
      :staticmethod:


   .. py:method:: pre_lookup(sources, opts, *, source) -> list[list[jgdv.structs.dkey._interface.ExpInst_d]]
      :staticmethod:


      returns a list (L1) of lists (L2) of target tuples (T).
      When looked up, For each L2, the first T that returns a value is added
      to the final result


   .. py:method:: pre_recurse(vals: list[jgdv.structs.dkey._interface.ExpInst_d], sources, opts, *, source) -> jgdv.Maybe[list[jgdv.structs.dkey._interface.ExpInst_d]]
      :staticmethod:


      Produces a list[Key|Val|(Key, rec:int)]


   .. py:method:: redirect(source: jgdv.structs.dkey._interface.Expandable_p, *sources, **kwargs) -> list[jgdv.structs.dkey.core.meta.DKey]
      :staticmethod:


 
 
   
