 

 
.. _jgdv.cli.param_spec._mixins:
   
    
===========================
jgdv.cli.param_spec._mixins
===========================

   
.. py:module:: jgdv.cli.param_spec._mixins

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.param_spec._mixins._ConsumerArg_m
    jgdv.cli.param_spec._mixins._DefaultsBuilder_m
    jgdv.cli.param_spec._mixins._ParamNameParser_m
           
 
      
 
Module Contents
===============

 
 

.. jgdv.cli.param_spec._mixins._ConsumerArg_m:
   
.. py:class:: _ConsumerArg_m
   
    
   Mixin for CLI arg consumption

   
   .. py:method:: _match_on_end(val) -> bool

   .. py:method:: _split_assignment(val) -> list[str]

   .. py:method:: coerce_types(key, value) -> dict

      process the parsed values


   .. py:method:: consume(args: list[str], *, offset: int = 0) -> jgdv.Maybe[tuple[dict, int]]

      Given a list of args, possibly add a value to the data.
      operates on both the args list
      return maybe(newdata, amount_consumed)

      handles:
      ["--arg=val"],
      ["-arg", "val"],
      ["val"],     (if positional=True)
      ["-arg"],    (if type=bool)
      ["-no-arg"], (if type=bool)


   .. py:method:: matches_head(val) -> bool

      test to see if a cli argument matches this param

      Will match anything if self.positional
      Matchs {self.prefix}{self.name} if not an assignment
      Matches {self.prefix}{self.name}{separator} if an assignment


   .. py:method:: next_value(args: list) -> tuple[str, list, int]

 
 
 

.. jgdv.cli.param_spec._mixins._DefaultsBuilder_m:
   
.. py:class:: _DefaultsBuilder_m
   
    
   
   .. py:method:: build_defaults(params: list[jgdv.cli._interface.ParamStruct_p]) -> dict
      :staticmethod:


   .. py:method:: check_insists(params: list[Self], data: dict) -> None
      :staticmethod:


   .. py:method:: default_tuple() -> tuple[str, Any]

   .. py:property:: default_value

 
 
 

.. jgdv.cli.param_spec._mixins._ParamNameParser_m:
   
.. py:class:: _ParamNameParser_m
   
    
   Parses a name into its component parts.

   eg: --blah= -> {prefix:--, name:blah, assign:None}


   
   .. py:method:: _parse_name(name: str) -> jgdv.Maybe[dict]
      :staticmethod:


 
 
   
