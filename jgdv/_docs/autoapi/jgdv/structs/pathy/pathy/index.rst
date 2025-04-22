 

 
.. _jgdv.structs.pathy.pathy:
   
    
========================
jgdv.structs.pathy.pathy
========================

   
.. py:module:: jgdv.structs.pathy.pathy

.. autoapi-nested-parse::

   Subclasses of pathlib.Path for working with type safe:
   - Abstract paths that will be expanded
   - Directories,
   - Files

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.pathy.pathy.Pathy
    jgdv.structs.pathy.pathy.PathyDir
    jgdv.structs.pathy.pathy.PathyFile
    jgdv.structs.pathy.pathy.PathyPure
    jgdv.structs.pathy.pathy.PathyReal
    jgdv.structs.pathy.pathy.WildPathy
    jgdv.structs.pathy.pathy._PathyExpand_m
    jgdv.structs.pathy.pathy._PathyTime_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.pathy.pathy.Pathy:
   
.. py:class:: Pathy(*paths: str | pathlib.Path, key=None, **kwargs)
   
   Bases: :py:obj:`jgdv.mixins.annotate.SubRegistry_m` 
     
   The Main Accessor to Pathy.
   You don't build Pathy's directly eg: Pathy("a/loc/test.txt"),
   but using Subtypes: Pathy[File]("a/loc/test.txt")

   The subtypes are: Pure, Real, File, Dir, Wild
   They are class attrs of Pathy, and in the pathy module.

   Also: Pathy.cwd() and Pathy.home()

   
   .. py:method:: cwd() -> Pathy[jgdv.structs.pathy._interface.Real]
      :staticmethod:


   .. py:method:: home() -> Pathy[jgdv.structs.pathy._interface.Real]
      :staticmethod:


   .. py:attribute:: Dir

   .. py:attribute:: File

   .. py:attribute:: Pure

   .. py:attribute:: Real

   .. py:attribute:: Wild

   .. py:attribute:: _key
      :value: None


   .. py:attribute:: _meta

   .. py:attribute:: _registry
      :type:  ClassVar[dict[type, pathlib.PurePath | pathlib.Path]]

 
 
 

.. _jgdv.structs.pathy.pathy.PathyDir:
   
.. py:class:: PathyDir(*args)
   
   Bases: :py:obj:`Pathy`\ [\ :py:obj:`jgdv.structs.pathy._interface.Dir`\ ], :py:obj:`PathyReal` 
     
   A Pathy for Directories, not files

   TODO disable:
   open, read_bytes/text, write_bytes/text

   
 
 
 

.. _jgdv.structs.pathy.pathy.PathyFile:
   
.. py:class:: PathyFile(*args)
   
   Bases: :py:obj:`Pathy`\ [\ :py:obj:`jgdv.structs.pathy._interface.File`\ ], :py:obj:`PathyReal` 
     
   A Pathy for an existing File

   TODO disable:
   iterdir
   rglob

   
   .. py:method:: glob(*args, **kwargs)
      :abstractmethod:


      Iterate over this subtree and yield all existing files (of any
      kind, including directories) matching the given relative pattern.


   .. py:method:: mkdir(*args)

      Create a new directory at this given path.


   .. py:method:: walk(*args, **kwargs)
      :abstractmethod:


      Walk the directory tree from this directory, similar to os.walk().


 
 
 

.. _jgdv.structs.pathy.pathy.PathyPure:
   
.. py:class:: PathyPure(*args)
   
   Bases: :py:obj:`Pathy`\ [\ :py:obj:`jgdv.structs.pathy._interface.Pure`\ ], :py:obj:`pathlib.PurePath` 
     
   A Pure Pathy, subclass of pathlib.PurePath with extra functionality

   
   .. py:method:: format(*args, **kwargs) -> Self

   .. py:method:: with_segments(*segments) -> Self

      Construct a new path object from any number of path-like objects.
      Subclasses may override this method to customize how new path objects
      are created from methods like `iterdir()`.


   .. py:method:: with_suffix(suffix)

      Return a new path with the file suffix changed.  If the path
      has no suffix, add given suffix.  If the given suffix is an empty
      string, remove the suffix from the path.


 
 
 

.. _jgdv.structs.pathy.pathy.PathyReal:
   
.. py:class:: PathyReal(*args)
   
   Bases: :py:obj:`Pathy`\ [\ :py:obj:`jgdv.structs.pathy._interface.Real`\ ], :py:obj:`PathyPure`, :py:obj:`pathlib.Path` 
     
   The Pathy equivalent of pathlib.Path

   
 
 
 

.. _jgdv.structs.pathy.pathy.WildPathy:
   
.. py:class:: WildPathy(*args)
   
   Bases: :py:obj:`Pathy`\ [\ :py:obj:`jgdv.structs.pathy._interface.Wild`\ ], :py:obj:`PathyPure` 
     
   A Pure Pathy that represents a location with wildcards and keys in it.

   ::

       Can handle wildcards (?), globs (* and **), and keys ({}) in it.
       eg: a/path/*/?.txt

   Converts to a List of PathReal's by calling 'expand'

   
   .. py:method:: glob(pattern, *, case_sensitive=None, recurse_symlinks=True)

   .. py:method:: keys() -> set[str]
      :abstractmethod:


   .. py:method:: rglob(pattern, *, case_sensitive=None, recurse_symlinks=True)

      Recursively yield all existing files (of any kind, including
      directories) matching the given relative pattern, anywhere in
      this subtree.


   .. py:method:: walk_dirs(*, d_skip=None, depth=None) -> iter[Pathy[dir]]

      Walk the directory tree, to a certain depth.

      > d_skip: lambda x: -> bool. True skip

      returns an iterator of the available paths


   .. py:method:: walk_files(*, d_skip=None, f_skip=None, depth=None) -> iter[PathyFile]

      Walk a Path, returning applicable files

      | filters directories using fn. lambda x -> bool. True skips
      | filters file using f_skip(lambda x: bool), True ignores


   .. py:method:: with_segments(*segments) -> Self

      Construct a new path object from any number of path-like objects.
      Subclasses may override this method to customize how new path objects
      are created from methods like `iterdir()`.


 
 
 

.. jgdv.structs.pathy.pathy._PathyExpand_m:
   
.. py:class:: _PathyExpand_m
   
    
   Mixin for normalizing the Paths

   
   .. py:method:: normalize(*, root: jgdv.Maybe[pathlib.Path] = None, symlinks: bool = False) -> pathlib.Path

      a basic path normalization
      expands user, and resolves the location to be absolute


 
 
 

.. jgdv.structs.pathy.pathy._PathyTime_m:
   
.. py:class:: _PathyTime_m
   
    
   Mixin for getting time created and modified, and comparing two files

   
   .. py:method:: _newer_than(time: jgdv.DateTime, *, tolerance: jgdv.TimeDelta = None) -> bool

      True if self.time_modified() < time,
      with a tolerance because some file systems have lower resolution


   .. py:method:: time_created() -> jgdv.DateTime

   .. py:method:: time_modified() -> jgdv.DateTime

 
 
   
