 

 
.. _jgdv.mixins.zipper:
   
    
==================
jgdv.mixins.zipper
==================

   
.. py:module:: jgdv.mixins.zipper

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.mixins.zipper.Zipper_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.mixins.zipper.Zipper_m:
   
.. py:class:: Zipper_m
   
    
   Add methods for manipulating zip files.
   Can set a self.zip_root path, where added files with be relative to

   
   .. py:method:: _zip_get_compression_settings() -> tuple[int, int]

   .. py:method:: zip_add_paths(fpath: pathlib.Path, *args: pathlib.Path)

      Add specific files to the zip.
        Will Create the zip if it doesn't exist


   .. py:method:: zip_add_str(fpath: pathlib.Path, fname: str, text: str)

      add a string of text to a zip file as a new file


   .. py:method:: zip_contains(zip: pathlib.Path, *names: str | pathlib.Path) -> bool

      test that a zip file contains multiple filenames


   .. py:method:: zip_create(fpath: pathlib.Path)

      Create a new zipfile. will overwrite an existing zip if 'zip_overwrite' is set


   .. py:method:: zip_get_contents(fpath: pathlib.Path) -> list[str]

   .. py:method:: zip_globs(fpath: pathlib.Path, *globs: str, ignore_dots=False)

      Add files chosen by globs to the zip, relative to the cwd


   .. py:method:: zip_set_root(fpath: pathlib.Path)

      set the filesystem that acts as the root for paths to be added to the zip file


   .. py:method:: zip_test(*zips: pathlib.Path)

      Test the validity of zip files


   .. py:method:: zip_unzip_concat(fpath: pathlib.Path, *zips: pathlib.Path, member=None, header=b'\n\n#------\n\n', footer=b'\n\n#------\n\n')

      Unzip a member file in a multiple zip files,
      append their text contents into a single file


   .. py:method:: zip_unzip_to(fpath: pathlib.Path, *zips: pathlib.Path, fn=None)

      extract everything or everything that returns true from fn, from all zips given
      into subdirs of fpath


   .. py:attribute:: _zip_compress_level
      :type:  int
      :value: 4


   .. py:attribute:: _zip_compression
      :type:  str
      :value: 'ZIP_DEFLATED'


   .. py:attribute:: zip_name
      :type:  str
      :value: 'default'


   .. py:attribute:: zip_overwrite
      :type:  bool
      :value: False


   .. py:attribute:: zip_root
      :type:  jgdv.Maybe[pathlib.Path]
      :value: None


 
 
   
