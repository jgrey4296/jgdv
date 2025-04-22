 

 
.. _jgdv.cli._interface:
   
    
===================
jgdv.cli._interface
===================

   
.. py:module:: jgdv.cli._interface

       
 

   
 

 

 
   
        

           

 
 

 
 

Protocols
---------

.. autoapisummary::

   jgdv.cli._interface.ArgParser_p
   jgdv.cli._interface.CLIParamProvider_p
   jgdv.cli._interface.ParamSource_p
   jgdv.cli._interface.ParamStruct_p

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli._interface.ParseResult_d
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli._interface.ArgParser_p:
   
.. py:class:: ArgParser_p
   
   Bases: :py:obj:`Protocol` 
     
   A Single standard process point for turning the list of passed in args,
   into a dict, into a chainguard,
   along the way it determines the cmds and tasks that have been chosne

   
   .. py:method:: _has_no_more_args_cond() -> bool
      :abstractmethod:


   .. py:method:: _parse_fail_cond() -> bool
      :abstractmethod:


 
 
 

.. _jgdv.cli._interface.CLIParamProvider_p:
   
.. py:class:: CLIParamProvider_p
   
   Bases: :py:obj:`Protocol` 
     
   Things that can provide parameter specs for CLI parsing

   
   .. py:method:: param_specs() -> list[ParamStruct_p]
      :classmethod:


      make class parameter specs


 
 
 

.. _jgdv.cli._interface.ParamSource_p:
   
.. py:class:: ParamSource_p
   
   Bases: :py:obj:`Protocol` 
     
   Base class for protocol classes.

   Protocol classes are defined as::

       class Proto(Protocol):
           def meth(self) -> int:
               ...

   Such classes are primarily used with static type checkers that recognize
   structural subtyping (static duck-typing).

   For example::

       class C:
           def meth(self) -> int:
               return 0

       def func(x: Proto) -> int:
           return x.meth()

       func(C())  # Passes static type check

   See PEP 544 for details. Protocol classes decorated with
   @typing.runtime_checkable act as simple-minded runtime protocols that check
   only the presence of given attributes, ignoring their type signatures.
   Protocol classes can be generic, they are defined as::

       class GenProto[T](Protocol):
           def meth(self) -> T:
               ...

   
   .. py:property:: name
      :type: str

      :abstractmethod:


   .. py:property:: param_specs
      :type: list[ParamStruct_p]

      :abstractmethod:


 
 
 

.. _jgdv.cli._interface.ParamStruct_p:
   
.. py:class:: ParamStruct_p
   
   Bases: :py:obj:`Protocol` 
     
   Base class for CLI param specs, for type matching
   when 'consume' is given a list of strs,
   it can match on the args,
   and return an updated diction and a list of values it didn't consume


   
   .. py:method:: consume(args: list[str], *, offset: int = 0) -> jgdv.Maybe[tuple[dict, int]]

   .. py:attribute:: key_func
      :type:  collections.abc.Callable

 
 
 

.. _jgdv.cli._interface.ParseResult_d:
   
.. py:class:: ParseResult_d
   
    
   
   .. py:method:: to_dict() -> dict

   .. py:attribute:: args
      :type:  dict

   .. py:attribute:: name
      :type:  str

   .. py:attribute:: non_default
      :type:  set[str]

 
 
   
