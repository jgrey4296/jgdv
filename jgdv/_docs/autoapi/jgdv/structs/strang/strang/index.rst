 

 
.. _jgdv.structs.strang.strang:
   
    
==========================
jgdv.structs.strang.strang
==========================

   
.. py:module:: jgdv.structs.strang.strang

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.structs.strang.strang.BodyMark
   jgdv.structs.strang.strang.GroupMark

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.strang.strang.Strang
    jgdv.structs.strang.strang.StrangBuilder_m
    jgdv.structs.strang.strang.StrangMeta
           
 
      
 
Module Contents
===============

 
.. py:data:: BodyMark
   :type:  TypeAlias
   :value: type[enum.StrEnum]


 
.. py:data:: GroupMark
   :type:  TypeAlias
   :value: type[enum.StrEnum] | type[int]


 
 

.. _jgdv.structs.strang.strang.Strang:
   
.. py:class:: Strang(*_: Any, **kwargs: Any)
   
   Bases: :py:obj:`str` 
     
   A Structured String Baseclass.

   A Normal str, but is parsed on construction to extract and validate
   certain form and metadata.

   The Form of a Strang is::

       {group}{sep}{body}
       eg: group.val::body.val

   Body objs can be marks (Strang.bmark_e), and UUID's as well as str's

   strang[x] and strang[x:y] are changed to allow structured access::

       val = Strang("a.b.c::d.e.f")
       val[0] # a.b.c
       val[1] # d.e.f


   
   .. py:method:: _post_process() -> None

      go through body elements, and parse UUIDs, markers, param
      setting self._body_meta and self._mark_idx


   .. py:method:: body(*, reject: jgdv.Maybe[collections.abc.Callable] = None, no_expansion: bool = False) -> list[str]

      Get the body, as a list of str's,
      with values filtered out if a rejection fn is used


   .. py:method:: uuid() -> jgdv.Maybe[uuid.UUID]

   .. py:attribute:: _base_slices
      :type:  tuple[jgdv.Maybe[slice], jgdv.Maybe[slice]]

   .. py:attribute:: _body
      :type:  list[slice]

   .. py:attribute:: _body_meta
      :type:  list[jgdv.Maybe[Strang]]

   .. py:attribute:: _body_types
      :type:  ClassVar[Any]

   .. py:attribute:: _group
      :type:  list[slice]

   .. py:attribute:: _group_meta
      :type:  set[str]

   .. py:attribute:: _mark_idx
      :type:  tuple[jgdv.Maybe[int], jgdv.Maybe[int]]

   .. py:attribute:: _separator
      :type:  ClassVar[str]
      :value: '::'


   .. py:attribute:: _subseparator
      :type:  ClassVar[str]
      :value: '.'


   .. py:attribute:: _typevar
      :type:  ClassVar[jgdv.Maybe[type]]
      :value: None


   .. py:property:: base
      :type: Self


   .. py:attribute:: bmark_e
      :type:  ClassVar[BodyMark]

   .. py:attribute:: gmark_e
      :type:  ClassVar[GroupMark]

   .. py:property:: group
      :type: list[str]


   .. py:attribute:: metadata
      :type:  dict

   .. py:property:: shape
      :type: tuple[int, int]


 
 
 

.. _jgdv.structs.strang.strang.StrangBuilder_m:
   
.. py:class:: StrangBuilder_m
   
    
   
   .. py:method:: build(data: str, *args: Any, **kwargs: Any) -> Strang
      :staticmethod:


      Build an appropriate Strang subclass else a Strang,
      goes from newest to oldest.

      eg: For when you might have a Location or a Name, and want to try to build both


 
 
 

.. _jgdv.structs.strang.strang.StrangMeta:
   
.. py:class:: StrangMeta
   
   Bases: :py:obj:`type`\ (\ :py:obj:`str`\ ) 
     
   A Metaclass for Strang
   It runs the pre-processsing and post-processing on the constructed str
   to turn it into a strang

   
   .. py:attribute:: _forms
      :type:  ClassVar[list[type]]
      :value: []


 
 
   
