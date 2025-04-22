 

 
.. _jgdv.cli.param_spec.core:
   
    
========================
jgdv.cli.param_spec.core
========================

   
.. py:module:: jgdv.cli.param_spec.core

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.param_spec.core.ChoiceParam
    jgdv.cli.param_spec.core.ConstrainedParam
    jgdv.cli.param_spec.core.EntryParam
    jgdv.cli.param_spec.core.ImplicitParam
    jgdv.cli.param_spec.core.KeyParam
    jgdv.cli.param_spec.core.LiteralParam
    jgdv.cli.param_spec.core.RepeatToggleParam
    jgdv.cli.param_spec.core.RepeatableParam
    jgdv.cli.param_spec.core.ToggleParam
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.param_spec.core.ChoiceParam:
   
.. py:class:: ChoiceParam(name, choices: list[str], **kwargs)
   
   Bases: :py:obj:`LiteralParam` 
     
   TODO A param that must be from a choice of literals
   eg: ChoiceParam([blah, bloo, blee]) : blah | bloo | blee


   
   .. py:method:: matches_head(val) -> bool

      test to see if a cli argument matches this param

      Will match anything if self.positional
      Matchs {self.prefix}{self.name} if not an assignment
      Matches {self.prefix}{self.name}{separator} if an assignment


   .. py:attribute:: _choices

 
 
 

.. _jgdv.cli.param_spec.core.ConstrainedParam:
   
.. py:class:: ConstrainedParam(/, **data: Any)
   
   Bases: :py:obj:`jgdv.cli.param_spec._base.ParamSpecBase` 
     
   TODO a type of parameter which is constrained in the values it can take, beyond just type.

   eg: {name:amount, constraints={min=0, max=10}}

   
   .. py:attribute:: constraints
      :type:  list[Any]
      :value: []


 
 
 

.. _jgdv.cli.param_spec.core.EntryParam:
   
.. py:class:: EntryParam(/, **data: Any)
   
   Bases: :py:obj:`LiteralParam` 
     
   TODO a parameter that if it matches,
   returns list of more params to parse

   
 
 
 

.. _jgdv.cli.param_spec.core.ImplicitParam:
   
.. py:class:: ImplicitParam(/, **data: Any)
   
   Bases: :py:obj:`jgdv.cli.param_spec._base.ParamSpecBase` 
     
   A Parameter that is implicit, so doesn't give a help description unless
   forced to

   
   .. py:method:: help_str()

 
 
 

.. _jgdv.cli.param_spec.core.KeyParam:
   
.. py:class:: KeyParam(/, **data: Any)
   
   Bases: :py:obj:`jgdv.cli.param_spec._base.ParamSpecBase` 
     
   TODO a param that is specified by a prefix key
   eg: -key val

   
   .. py:method:: matches_head(val) -> bool

   .. py:method:: next_value(args: list) -> tuple[list, int]

      get the value for a -key val


   .. py:attribute:: type_
      :type:  pydantic.InstanceOf[type]
      :value: None


 
 
 

.. _jgdv.cli.param_spec.core.LiteralParam:
   
.. py:class:: LiteralParam(/, **data: Any)
   
   Bases: :py:obj:`ToggleParam` 
     
   Match on a Literal Parameter.
   For command/subcmd names etc

   
   .. py:method:: matches_head(val) -> bool

      test to see if a cli argument matches this param

      Will match anything if self.positional
      Matchs {self.prefix}{self.name} if not an assignment
      Matches {self.prefix}{self.name}{separator} if an assignment


   .. py:attribute:: prefix
      :type:  str
      :value: ''


 
 
 

.. _jgdv.cli.param_spec.core.RepeatToggleParam:
   
.. py:class:: RepeatToggleParam(/, **data: Any)
   
   Bases: :py:obj:`ToggleParam` 
     
   TODO A repeatable toggle
   eg: -verbose -verbose -verbose

   
 
 
 

.. _jgdv.cli.param_spec.core.RepeatableParam:
   
.. py:class:: RepeatableParam(/, **data: Any)
   
   Bases: :py:obj:`KeyParam` 
     
   TODO a repeatable key param
   -key val -key val2 -key val3

   
   .. py:method:: next_value(args: list) -> tuple[str, list, int]

      Get as many values as match
      eg: args[-test, 2, -test, 3, -test, 5, -nottest, 6]
      ->  [2,3,5], [-nottest, 6]


   .. py:attribute:: type_
      :type:  pydantic.InstanceOf[type]
      :value: None


 
 
 

.. _jgdv.cli.param_spec.core.ToggleParam:
   
.. py:class:: ToggleParam(/, **data: Any)
   
   Bases: :py:obj:`jgdv.cli.param_spec._base.ParamSpecBase` 
     
   A bool of -param or -not-param

   
   .. py:method:: next_value(args: list) -> tuple[str, list, int]

 
 
   
