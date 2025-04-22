 

 
.. _jgdv.logging.config:
   
    
===================
jgdv.logging.config
===================

   
.. py:module:: jgdv.logging.config

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.config.JGDVLogConfig
    jgdv.logging.config.PrintCapture_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.logging.config.JGDVLogConfig:
   
.. py:class:: JGDVLogConfig(*, subprinters: jgdv.Maybe[list[str]] = None, style: jgdv.Maybe[str] = None)
   
    
   Utility class to setup [stdout, stderr, file] logging.

   Also creates a 'printer' logger, so instead of using `print`,
   tasks can notify the user using the printer,
   which also includes the notifications into the general log trace

   The Printer has a number of children, which can be controlled
   to customise verbosity.

   Standard _printer children::
     action_exec, action_group, artifact, cmd, fail, header, help, queue,
     report, skip, sleep, success, task, task_header, task_loop, task_state,
     track



   
   .. py:method:: _install_logger_override() -> None

   .. py:method:: _register_new_names() -> None

   .. py:method:: _setup_logging_extra(config: jgdv.structs.chainguard.ChainGuard) -> None

      read the doot config logging section
      setting up each entry other than stream, file, printer, and subprinters


   .. py:method:: _setup_print_children(config: jgdv.structs.chainguard.ChainGuard) -> None

   .. py:method:: activate_spec(spec: jgdv.logging.logger_spec.LoggerSpec, *, override: bool = False) -> None

      Add a spec to the registry and activate it


   .. py:method:: set_level(level: int | str) -> None

      Set the active logging level


   .. py:method:: setup(config: jgdv.structs.chainguard.ChainGuard, *, force: bool = False) -> None

      a setup that uses config values


   .. py:method:: subprinter(*names, prefix: jgdv.Maybe[str] = None) -> jgdv.logging._interface.Logger

      Get a subprinter of the printer logger.
      The First name needs to be a registered subprinter.
      Additional names are unconstrained


   .. py:attribute:: _initial_spec
      :type:  jgdv.logging.logger_spec.LoggerSpec

   .. py:attribute:: _printer_children
      :type:  list

   .. py:attribute:: _printer_initial_spec
      :type:  jgdv.logging.logger_spec.LoggerSpec

   .. py:attribute:: _registry
      :type:  list

   .. py:attribute:: is_setup
      :type:  bool

   .. py:attribute:: levels
      :type:  ClassVar[enum.IntEnum]

   .. py:attribute:: logger_cls
      :type:  ClassVar[type[jgdv.logging._interface.Logger]]

   .. py:attribute:: root
      :type:  jgdv.logging._interface.Logger

 
 
 

.. _jgdv.logging.config.PrintCapture_m:
   
.. py:class:: PrintCapture_m
   
    
   Mixin for redirecting builtins.print to a file

   
   .. py:method:: capture_printing_to_file(path: str | pathlib.Path = API.default_print_file, *, disable_warning: bool = False) -> None

      Modifies builtins.print to also print to a file

      Setup a file handler for a separate logger,
      to keep a trace of anything printed.
      Strips colour print command codes out of any string
      printed strings are logged at DEBUG level


   .. py:method:: remove_print_capture() -> None

      removes a previously advised builtins.print


   .. py:attribute:: original_print
      :type:  jgdv.Maybe[collections.abc.Callable]

 
 
   
