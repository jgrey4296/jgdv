 

 
.. _jgdv.logging.logger_spec:
   
    
========================
jgdv.logging.logger_spec
========================

   
.. py:module:: jgdv.logging.logger_spec

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.logger_spec.HandlerBuilder_m
    jgdv.logging.logger_spec.LoggerSpec
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.logging.logger_spec.HandlerBuilder_m:
   
.. py:class:: HandlerBuilder_m
   
    
   Loggerspec Mixin for building handlers

   
   .. py:method:: _build_errorhandler() -> jgdv.logging._interface.Handler

   .. py:method:: _build_filehandler(path: pathlib.Path) -> jgdv.logging._interface.Handler

   .. py:method:: _build_filters() -> list[collections.abc.Callable]

   .. py:method:: _build_formatter(handler: jgdv.logging._interface.Handler) -> jgdv.logging._interface.Formatter

   .. py:method:: _build_rotatinghandler(path: pathlib.Path) -> jgdv.logging._interface.Handler

   .. py:method:: _build_streamhandler() -> jgdv.logging._interface.Handler

   .. py:method:: _discriminate_handler(target: jgdv.Maybe[str | pathlib.Path]) -> tuple[jgdv.Maybe[jgdv.logging._interface.Handler], jgdv.Maybe[jgdv.logging._interface.Formatter]]

 
 
 

.. _jgdv.logging.logger_spec.LoggerSpec:
   
.. py:class:: LoggerSpec(/, **data: Any)
   
   Bases: :py:obj:`HandlerBuilder_m`, :py:obj:`pydantic.BaseModel` 
     
   A Spec for toml defined logging control.
   Allows user to name a logger, set its level, format,
   filters, colour, and what (cli arg) verbosity it activates on,
   and what file it logs to.

   When 'apply' is called, it gets the logger,
   and sets any relevant settings on it.

   
   .. py:method:: _validate_format(val: str) -> str

   .. py:method:: _validate_level(val: str | int) -> int

   .. py:method:: _validate_style(val: str) -> str

   .. py:method:: _validate_target(val: list | str | pathlib.Path) -> list[str | pathlib.Path]

   .. py:method:: apply(*, onto: jgdv.Maybe[jgdv.logging._interface.Logger] = None) -> jgdv.logging._interface.Logger

      Apply this spec (and nested specs) to the relevant logger


   .. py:method:: build(data: bool | list | dict, **kwargs: Any) -> LoggerSpec
      :staticmethod:


      Build a single spec, or multiple logger specs targeting the same logger


   .. py:method:: clear() -> None

      Clear the handlers for the logger referenced


   .. py:method:: fullname() -> str

   .. py:method:: get() -> jgdv.logging._interface.Logger

   .. py:method:: logfile() -> pathlib.Path

   .. py:method:: set_level(level: int | str) -> None

   .. py:attribute:: RootName
      :type:  ClassVar[str]
      :value: 'root'


   .. py:attribute:: _applied
      :type:  bool
      :value: False


   .. py:attribute:: _logger
      :type:  jgdv.Maybe[jgdv.logging._interface.Logger]
      :value: None


   .. py:attribute:: allow
      :type:  list[str]
      :value: []


   .. py:attribute:: base
      :type:  jgdv.Maybe[str]
      :value: None


   .. py:attribute:: clear_handlers
      :type:  bool
      :value: False


   .. py:attribute:: colour
      :type:  bool | str
      :value: False


   .. py:attribute:: disabled
      :type:  bool
      :value: False


   .. py:attribute:: filename_fmt
      :type:  str
      :value: '%Y-%m-%d::%H:%M.log'


   .. py:attribute:: filter
      :type:  list[str]
      :value: []


   .. py:attribute:: format
      :type:  str
      :value: '{levelname:<8} : {message}'


   .. py:attribute:: level
      :type:  str | int

   .. py:attribute:: levels
      :type:  ClassVar[type[enum.IntEnum]]

   .. py:attribute:: name
      :type:  str

   .. py:attribute:: nested
      :type:  list[LoggerSpec]
      :value: []


   .. py:attribute:: prefix
      :type:  jgdv.Maybe[str]
      :value: None


   .. py:attribute:: propagate
      :type:  bool
      :value: False


   .. py:attribute:: style
      :type:  str
      :value: '{'


   .. py:attribute:: target
      :type:  list[str | pathlib.Path]
      :value: []


   .. py:attribute:: verbosity
      :type:  int
      :value: 0


 
 
   
