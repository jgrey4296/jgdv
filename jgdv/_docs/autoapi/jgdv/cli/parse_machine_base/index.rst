 

 
.. _jgdv.cli.parse_machine_base:
   
    
===========================
jgdv.cli.parse_machine_base
===========================

   
.. py:module:: jgdv.cli.parse_machine_base

.. autoapi-nested-parse::

   Provdes the Main ArgParser_p Protocol,
   and the ParseMachineBase StateMachine.

   ParseMachineBase descibes the state progression to parse arguments,
   while jgdv.cli.arg_parser.CLIParser adds the specific logic to states and transitions

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.cli.parse_machine_base.ParseMachineBase
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.parse_machine_base.ParseMachineBase:
   
.. py:class:: ParseMachineBase(*, parser: jgdv.cli._interface.ArgParser_p = None)
   
   Bases: :py:obj:`statemachine.StateMachine` 
     
   Base Implementaiton of an FSM for running a CLI arg parse.
   Subclass and init with a default ArgParser_p that has bound callback for events

   
   .. py:method:: on_exit_state()

   .. py:attribute:: CheckForHelp

   .. py:attribute:: Cleanup

   .. py:attribute:: Cmd

   .. py:attribute:: End

   .. py:attribute:: Extra

   .. py:attribute:: Failed

   .. py:attribute:: Head

   .. py:attribute:: Prepare

   .. py:attribute:: ReadyToReport

   .. py:attribute:: Start

   .. py:attribute:: SubCmd

   .. py:attribute:: count
      :value: 0


   .. py:attribute:: finish

   .. py:attribute:: max_attempts
      :value: 20


   .. py:attribute:: parse

   .. py:attribute:: setup

 
 
   
