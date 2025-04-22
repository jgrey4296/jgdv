 

 
.. _jgdv.structs.strang._mixins:
   
    
===========================
jgdv.structs.strang._mixins
===========================

   
.. py:module:: jgdv.structs.strang._mixins

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.strang._mixins.PostStrang_m
    jgdv.structs.strang._mixins.PreStrang_m
    jgdv.structs.strang._mixins._Strang_cmp_m
    jgdv.structs.strang._mixins._Strang_format_m
    jgdv.structs.strang._mixins._Strang_subgen_m
    jgdv.structs.strang._mixins._Strang_test_m
    jgdv.structs.strang._mixins._Strang_validation_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.strang._mixins.PostStrang_m:
   
.. py:class:: PostStrang_m
   
   Bases: :py:obj:`_Strang_validation_m`, :py:obj:`_Strang_subgen_m`, :py:obj:`jgdv.mixins.annotate.SubAnnotate_m` 
     
   Mixins that don't override str defaults

   
 
 
 

.. _jgdv.structs.strang._mixins.PreStrang_m:
   
.. py:class:: PreStrang_m
   
   Bases: :py:obj:`_Strang_cmp_m`, :py:obj:`_Strang_test_m`, :py:obj:`_Strang_format_m` 
     
   Mixins that override str defaults

   
 
 
 

.. jgdv.structs.strang._mixins._Strang_cmp_m:
   
.. py:class:: _Strang_cmp_m
   
    
   The mixin of Strang Comparison methods

   
 
 
 

.. jgdv.structs.strang._mixins._Strang_format_m:
   
.. py:class:: _Strang_format_m
   
    
   The mixin for formatting strangs into pure strings

   
   .. py:method:: _expanded_str(*, stop: jgdv.Maybe[int] = None) -> str

      Create a str of the Strang with gen uuid's replaced with actual uuids


   .. py:method:: _format_subval(val: str, *, no_expansion: bool = False) -> str

 
 
 

.. jgdv.structs.strang._mixins._Strang_subgen_m:
   
.. py:class:: _Strang_subgen_m
   
    
   Operations Mixin for manipulating TaskNames

   
   .. py:method:: _subjoin(lst: list) -> str
      :classmethod:


   .. py:method:: canon() -> Self

      canonical name. no UUIDs
      eg: group::a.b.c.$gen$.<uuid>.c.d.e
      ->  group::a.b.c..c.d.e


   .. py:method:: de_uniq() -> Self

      return the strang up to, but not including, the first instance mark.

      eg: 'group.a::q.w.e.<uuid>.t.<uuid>.y'.de_uniq() -> 'group.a::q.w.e'


   .. py:method:: pop(*, top: bool = False) -> Self

      Strip off one marker's worth of the name, or to the top marker.
      eg:
      root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
      root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c


   .. py:method:: push(*vals: str) -> Self

      Add a root marker if the last element isn't already a root marker
      eg: group::a.b.c => group.a.b.c.
      (note the trailing '.')


   .. py:method:: root() -> Self

      Pop off to the top marker


   .. py:method:: to_uniq(*, suffix: jgdv.Maybe[str] = None) -> Self

      Generate a concrete instance of this name with a UUID appended,
      optionally can add a suffix

        ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>


   .. py:method:: with_head() -> Self

      generate a canonical group/completion task name for this name
      eg: (concrete) group::simple.task..$gen$.<UUID> ->  group::simple.task..$gen$.<UUID>..$group$
      eg: (abstract) group::simple.task. -> group::simple.task..$head$



 
 
 

.. jgdv.structs.strang._mixins._Strang_test_m:
   
.. py:class:: _Strang_test_m
   
    
   The mixin of strang test method

   
   .. py:method:: is_head() -> bool

   .. py:method:: is_uniq() -> bool

      utility method to test if this name refers to a name with a UUID


 
 
 

.. jgdv.structs.strang._mixins._Strang_validation_m:
   
.. py:class:: _Strang_validation_m
   
    
   The mixin for validating strangs on construction

   
   .. py:method:: _get_slices(start: int = 0, max: jgdv.Maybe[int] = None, *, add_offset: bool = False) -> list[slice]

   .. py:method:: _post_process() -> None

      Abstract no-op to do additional post-processing extraction of metadata


   .. py:method:: _process() -> None

      Get slices of the strang to describe group and body components


   .. py:method:: pre_process(data: str, *, strict: bool = False) -> str
      :classmethod:


      run before str.__new__ is called, so can do early modification of the string
      Filters out extraneous duplicated separators


 
 
   
