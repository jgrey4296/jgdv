 

 
.. _jgdv.mixins.path_manip:
   
    
======================
jgdv.mixins.path_manip
======================

   
.. py:module:: jgdv.mixins.path_manip

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.mixins.path_manip.PathManip_m
    jgdv.mixins.path_manip.Walker_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.mixins.path_manip.PathManip_m:
   
.. py:class:: PathManip_m
   
    
   A Mixin for common path manipulations

   
   .. py:method:: _build_roots(spec, state, roots: jgdv.Maybe[list[str | jgdv.structs.dkey.DKey]]) -> list[pathlib.Path]

      convert roots from keys to paths


   .. py:method:: _calc_path_parts(fpath: pathlib.Path, roots: list[pathlib.Path]) -> dict

      take a path, and get a dict of bits which aren't methods of Path
      if no roots are provided use cwd


   .. py:method:: _find_parent_marker(fpath, marker=None) -> jgdv.Maybe[pathlib.Path]

      Go up the parent list to find a marker file, return the dir its in


   .. py:method:: _get_relative(fpath, roots: jgdv.Maybe[list[pathlib.Path]] = None) -> pathlib.Path

      Get relative path of fpath.
      if no roots are provided, default to using cwd


   .. py:method:: _normalize(path: pathlib.Path, root=None, symlinks: bool = False) -> pathlib.Path

      a basic path normalization
      expands user, and resolves the location to be absolute


   .. py:method:: _shadow_path(rpath: pathlib.Path, shadow_root: pathlib.Path) -> pathlib.Path
      :abstractmethod:


      take a relative path, apply it onto a root to create a shadowed location


 
 
 

.. _jgdv.mixins.path_manip.Walker_m:
   
.. py:class:: Walker_m
   
    
   A Mixin for walking directories,
   written for py<3.12

   
   .. py:method:: walk_all(roots, exts, rec=False, fn=None) -> Generator[dict]

      walk all available targets,
      and generate unique names for them


   .. py:method:: walk_target_deep(target, exts, fn) -> Generator[pathlib.Path]

   .. py:method:: walk_target_shallow(target, exts, fn)

   .. py:attribute:: control_e

 
 
   
