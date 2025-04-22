 

 
.. _jgdv.structs.locator.locator:
   
    
============================
jgdv.structs.locator.locator
============================

   
.. py:module:: jgdv.structs.locator.locator

.. autoapi-nested-parse::

   Central store of Locations,
   which expands paths and can hook into the dkey system

   ::

       locs = JGDVLocator()
       locs.update({"blah": "ex/dir", "bloo": "file:>a/b/c.txt"})

       locs.blah            # {cwd}/ex/dir
       locs['{blah}']       # {cwd}/ex/dir
       locator['{blah}/blee']  # {cwd}/ex/dir/blee

       locator.bloo            # {cwd}/a/b/c.txt
       locator['{bloo}']       # {cwd}/a/b/c.txt
       locator['{bloo}/blee']  # Error

       locator[{blah}/{bloo}'] # {cwd}/ex/dir/a/b/c.txt

   JGDVLocator has 3 main access methods::

       JGDVLocator.get    : like dict.get
       JGDVLocator.access : Access the Location object
       JGDVLocator.expand : Expand the location(s) into a path

   Shorthands::

       Locator.KEY      # Locator.access
       Locator["{KEY}"] # Locator.expand

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.locator.locator.JGDVLocator
    jgdv.structs.locator.locator.SoftFailMultiDKey
    jgdv.structs.locator.locator._LocatorAccess_m
    jgdv.structs.locator.locator._LocatorGlobal
    jgdv.structs.locator.locator._LocatorUtil_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.locator.locator.JGDVLocator:
   
.. py:class:: JGDVLocator(root: pathlib.Path)
   
    
   A managing context for storing and converting Locations to Paths.
   key=value pairs in [[locations]] toml blocks are integrated into it.

   It expands relative paths according to cwd(),
   (or the cwd at program start if the Location has the earlycwd flag)

   Can be used as a context manager to expand from a temp different root.
   In which case the current global loc store is at JGDVLocator.Current

   Locations are of the form:
   key = "meta/vars::path/to/dir/or/file.ext"

   simple locations can be accessed as attributes.
   eg: locs.temp

   more complex locations, with expansions, are accessed as items:
   locs['{temp}/somewhere']
   will expand 'temp' (if it is a registered location)

   
   .. py:method:: _clear()

   .. py:attribute:: Current
      :type:  ClassVar[_LocatorGlobal]

   .. py:attribute:: _data
      :type:  dict[jgdv.structs.dkey.DKey | str, jgdv.structs.locator.location.Location]

   .. py:attribute:: _loc_ctx
      :type:  jgdv.Maybe[JGDVLocator]

   .. py:attribute:: _root
      :type:  pathlib.Path

   .. py:attribute:: access
      :type:  collections.abc.Callable

   .. py:attribute:: expand
      :type:  collections.abc.Callable

   .. py:attribute:: gmark_e
      :type:  ClassVar[enum.EnumMeta]

   .. py:property:: root

      the registered root location

   .. py:attribute:: update
      :type:  collections.abc.Callable

 
 
 

.. _jgdv.structs.locator.locator.SoftFailMultiDKey:
   
.. py:class:: SoftFailMultiDKey(data: str | pathlib.Path, **kwargs)
   
   Bases: :py:obj:`jgdv.structs.dkey.MultiDKey`\ [\ :py:obj:`soft.fail`\ ] 
     
   Multi keys allow 1+ explicit subkeys.

   They have additional fields:

   _subkeys  : parsed information about explicit subkeys


   
   .. py:method:: exp_pre_lookup_h(sources, opts) -> list

      Expands subkeys, to be merged into the main key


 
 
 

.. jgdv.structs.locator.locator._LocatorAccess_m:
   
.. py:class:: _LocatorAccess_m
   
    
   
   .. py:method:: _coerce_key(key: jgdv.structs.locator.location.Location | jgdv.structs.dkey.DKey | str | pathlib.Path, *, strict: bool = False) -> jgdv.structs.dkey.DKey

      Coerces a key to a MultiDKey for expansion using DKey's expansion mechanism,
      using self as the source


   .. py:method:: access(key: jgdv.structs.dkey.DKey | str) -> jgdv.Maybe[jgdv.structs.locator.location.Location]

      Access the registered Location associated with 'key'


   .. py:method:: expand(key: jgdv.structs.locator.location.Location | pathlib.Path | jgdv.structs.dkey.DKey | str, strict=True, norm=True) -> jgdv.Maybe[pathlib.Path]

      Access the locations mentioned in 'key',
      join them together, and normalize it


   .. py:method:: get(key, fallback: jgdv.Maybe[str | pathlib.Path] = None) -> jgdv.Maybe[pathlib.Path]

      Behavinng like a dict.get,
      uses Locator.access, but coerces to an unexpanded path

      raises a KeyError when fallback is None


   .. py:attribute:: _data
      :type:  dict[jgdv.structs.dkey.DKey | str, jgdv.structs.locator.location.Location]

 
 
 

.. jgdv.structs.locator.locator._LocatorGlobal:
   
.. py:class:: _LocatorGlobal
   
    
   A program global stack of locations.
   Provides the enter/exit store for JGDVLocator objects

   
   .. py:method:: peek() -> jgdv.Maybe[JGDVLocator]
      :staticmethod:


   .. py:method:: pop() -> jgdv.Maybe[JGDVLocator]
      :staticmethod:


   .. py:method:: push(locs) -> None
      :staticmethod:


   .. py:method:: stacklen() -> int
      :staticmethod:


   .. py:attribute:: _global_locs
      :type:  ClassVar[list[JGDVLocator]]
      :value: []


   .. py:attribute:: _startup_cwd
      :type:  ClassVar[pathlib.Path]

 
 
 

.. jgdv.structs.locator.locator._LocatorUtil_m:
   
.. py:class:: _LocatorUtil_m
   
    
   
   .. py:method:: metacheck(key: str | jgdv.structs.dkey.DKey, *meta: jgdv.structs.locator._interface.LocationMeta_e) -> bool

      return True if key provided has any of the metadata flags


   .. py:method:: norm(path) -> pathlib.Path

   .. py:method:: normalize(path: pathlib.Path | jgdv.structs.locator.location.Location, symlinks: bool = False) -> pathlib.Path

      Expand a path to be absolute, taking into account the set doot root.
      resolves symlinks unless symlinks=True


   .. py:method:: pre_expand() -> None

      Called after updating the Locator,
      it pre-expands any registered keys found in registered Locations


   .. py:method:: registered(*values, task='doot', strict=True) -> set

      Ensure the values passed in are registered locations,
      error with DirAbsent if they aren't


   .. py:method:: update(extra: dict | jgdv.structs.chainguard.ChainGuard | jgdv.structs.locator.location.Location | JGDVLocator, *, strict=True) -> Self

        Update the registered locations with a dict, chainguard, or other dootlocations obj.

      when strict=True (default), don't allow overwriting existing locations


   .. py:attribute:: _data
      :type:  dict[jgdv.structs.dkey.DKey | str, jgdv.structs.locator.location.Location]

 
 
   
