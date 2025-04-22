 

 
.. _jgdv.structs.locator.location:
   
    
=============================
jgdv.structs.locator.location
=============================

   
.. py:module:: jgdv.structs.locator.location

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.locator.location.Location
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.locator.location.Location:
   
.. py:class:: Location(*args, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.locator._interface.Location_d`, :py:obj:`jgdv.structs.strang.Strang` 
     
   A Location is an abstraction higher than a path.

   ie: a path, with metadata.

   Doesn't expand on its own, requires a JGDVLocator store

   It is a Strang subclass, of the form "{meta}+::a/path/location". eg::

       file/clean::.temp/docs/blah.rst

   TODO use annotations to require certain metaflags.
   eg::

       ProtectedLoc = Location['protect']
       Cleanable    = Location['clean']
       FileLoc      = Location['file']

   TODO add an ExpandedLoc subclass that holds the expanded path,
   and removes the need for much of PathManip_m?

   TODO add a ShadowLoc subclass using annotations
   eg::

       BackupTo  = ShadowLoc[root='/vols/BackupSD']
       a_loc     = BackupTo('file::a/b/c.mp3')
       a_loc.path_pair() -> ('/vols/BackupSD/a/b/c.mp3', '~/a/b/c.mp3')


   
   .. py:method:: _post_process() -> None

      go through body elements, and parse UUIDs, markers, param
      setting self._body_meta and self._mark_idx


   .. py:method:: check_wildcards(other: Location) -> bool

   .. py:method:: ext(*, last: bool = False) -> jgdv.Maybe[str | tuple[Location, str]]

      return the ext, or a tuple of how it is a wildcard.
      returns nothing if theres no extension,
      returns all suffixes if there are multiple, or just the last if last=True


   .. py:method:: is_concrete() -> bool

   .. py:method:: pre_process(data: str | pathlib.Path, *, strict: bool = False) -> Any
      :classmethod:


   .. py:attribute:: _body_types
      :type:  ClassVar[Any]

   .. py:attribute:: _group_meta

   .. py:attribute:: _separator
      :type:  ClassVar[str]
      :value: '::>'


   .. py:attribute:: _subseparator
      :type:  ClassVar[str]
      :value: '/'


   .. py:attribute:: bmark_e

   .. py:property:: body_parent
      :type: list[Location]


   .. py:attribute:: gmark_e

   .. py:property:: keys
      :abstractmethod:


   .. py:property:: path
      :type: pathlib.Path


   .. py:property:: stem
      :type: jgdv.Maybe[str | tuple[Location, str]]


      Return the stem, or a tuple describing how it is a wildcard

 
 
   
