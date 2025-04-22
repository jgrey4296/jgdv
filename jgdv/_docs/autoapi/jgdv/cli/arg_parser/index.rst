 

 
.. _jgdv.cli.arg_parser:
   
    
===================
jgdv.cli.arg_parser
===================

   
.. py:module:: jgdv.cli.arg_parser

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.arg_parser.CLIParser
    jgdv.cli.arg_parser.ParseMachine
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.arg_parser.CLIParser:
   
.. py:class:: CLIParser
   
    
   # {prog} {args} {cmd} {cmd_args}
   # {prog} {args} [{task} {tasks_args}] - implicit do cmd


   
   .. py:method:: _cleanup() -> None

   .. py:method:: _has_no_more_args_cond()

   .. py:method:: _parse_cmd()

      consume arguments for the command being run


   .. py:method:: _parse_extra()

   .. py:method:: _parse_fail_cond() -> bool

   .. py:method:: _parse_head()

      consume arguments for doot actual


   .. py:method:: _parse_params(res: jgdv.cli._interface.ParseResult_d, params: list[jgdv.cli.param_spec.ParamSpec]) -> None

   .. py:method:: _parse_params_unordered(res: jgdv.cli._interface.ParseResult_d, params: list[jgdv.cli.param_spec.ParamSpec])

   .. py:method:: _parse_separator() -> bool

   .. py:method:: _parse_subcmd()

      consume arguments for tasks


   .. py:method:: _setup(args: list[str], head_specs: list, cmds: list[jgdv.cli._interface.ParamSource_p], subcmds: list[tuple[str, jgdv.cli._interface.ParamSource_p]])

      Parses the list of arguments against available registered parameter head_specs, cmds, and tasks.


   .. py:method:: all_args_consumed_val()

   .. py:method:: help_flagged()

   .. py:method:: report() -> jgdv.Maybe[dict]

      Take the parsed results and return a nested dict


   .. py:attribute:: _cmd_specs
      :type:  dict[str, list[jgdv.cli.param_spec.ParamSpec]]

   .. py:attribute:: _force_help
      :type:  bool
      :value: False


   .. py:attribute:: _head_specs
      :type:  list[jgdv.cli.param_spec.ParamSpec]
      :value: []


   .. py:attribute:: _initial_args
      :type:  list[str]
      :value: []


   .. py:attribute:: _remaining_args
      :type:  list[str]
      :value: []


   .. py:attribute:: _subcmd_specs
      :type:  dict[str, tuple[str, list[jgdv.cli.param_spec.ParamSpec]]]

   .. py:attribute:: cmd_result
      :type:  jgdv.Maybe[jgdv.cli._interface.ParseResult_d]
      :value: None


   .. py:attribute:: extra_results
      :type:  jgdv.cli._interface.ParseResult_d

   .. py:attribute:: head_result
      :type:  jgdv.Maybe[jgdv.cli._interface.ParseResult_d]
      :value: None


   .. py:attribute:: subcmd_results
      :type:  list[jgdv.cli._interface.ParseResult_d]
      :value: []


 
 
 

.. _jgdv.cli.arg_parser.ParseMachine:
   
.. py:class:: ParseMachine(**kwargs)
   
   Bases: :py:obj:`jgdv.cli.parse_machine_base.ParseMachineBase` 
     
   Implemented Parse State Machine

   __call__ with:
   args       : list[str]       -- the cli args to parse (ie: from sys.argv)
   head_specs : list[ParamSpec] -- specs of the top level program
   cmds       : list[ParamSource_p] -- commands that can provide their parameters
   subcmds    : dict[str, list[ParamSource_p]] -- a mapping from commands -> subcommands that can provide parameters

   A cli call will be of the form:
   {proghead} {prog args} {cmd} {cmd args}* [{subcmd} {subcmdargs} [-- {subcmd} {subcmdargs}]* ]? (--help)?

   eg:
   doot -v list -by-group a b c --help
   doot run basic::task -quick --value=2 --help

   Will raise a jgdv.cli.errors.ParseError on failure

   
 
 
   
