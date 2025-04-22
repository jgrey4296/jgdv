 

 
.. _jgdv.debugging.malloc_tool:
   
    
==========================
jgdv.debugging.malloc_tool
==========================

   
.. py:module:: jgdv.debugging.malloc_tool

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.debugging.malloc_tool.Snapshot

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.debugging.malloc_tool.MallocTool
           
 
      
 
Module Contents
===============

 
.. py:data:: Snapshot
   :type:  TypeAlias
   :value: tracemalloc.Snapshot


 
 

.. _jgdv.debugging.malloc_tool.MallocTool:
   
.. py:class:: MallocTool(*, num_frames: int = 5, logger: jgdv.Maybe[Logger] = None, level: int = API.DEFAULT_LOG_LEVEL)
   
    
   see https://docs.python.org/3/library/tracemalloc.html

   example::

       with MallocTool(2) as dm:
           dm.whitelist(__file__)
           dm.blacklist("*tracemalloc.py", all_frames=False)
           val = 2
           dm.snapshot("simple")
           vals = [random.random() for x in range(1000)]
           dm.current()
           dm.snapshot("list")
           vals = None
           dm.current()
           dm.snapshot("cleared")

       dm.compare("simple", "list")
       dm.compare("list", "cleared")
       dm.compare("list", "simple")
       dm.inspect("list")


   
   .. py:method:: _log(msg: str, *args: Any, prefix: str = API.DEFAULT_PREFIX) -> None

   .. py:method:: _print_diff(stat: Difference) -> None

      Print a Trace memory comparison


   .. py:method:: _print_stat(stat: Statistic | Difference) -> None

      Print a Traced memory snapshot


   .. py:method:: blacklist(file_pat: str, *, lineno: jgdv.Maybe[int] = None, all_frames: bool = True) -> None

   .. py:method:: compare(val1: int | str, val2: int | str, *, type: str = API.DEFAULT_REPORT) -> None

   .. py:method:: current(val: jgdv.Maybe = None) -> None

   .. py:method:: file_matches(name: str | pathlib.Path, pat: str) -> bool

   .. py:method:: get_snapshot(val: int | str) -> Snapshot

   .. py:method:: inspect(val: Any, *, type: str = API.DEFAULT_REPORT) -> None

   .. py:method:: snapshot(*, name: jgdv.Maybe[str] = None) -> None

   .. py:method:: whitelist(file_pat: str, lineno: jgdv.Maybe[int] = None, *, all_frames: bool = True) -> None

   .. py:attribute:: _log_level
      :type:  int

   .. py:attribute:: _logger
      :type:  jgdv.Maybe[Logger]

   .. py:attribute:: filters
      :type:  list[Filter]

   .. py:attribute:: named_snapshots
      :type:  dict[str, Snapshot]

   .. py:attribute:: num_frames
      :type:  int

   .. py:attribute:: snapshots
      :type:  list[Snapshot]

   .. py:attribute:: started
      :type:  bool

 
 
   
