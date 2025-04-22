 

 
.. _jgdv.logging._interface:
   
    
=======================
jgdv.logging._interface
=======================

   
.. py:module:: jgdv.logging._interface

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.logging._interface.Formatter
   jgdv.logging._interface.Handler
   jgdv.logging._interface.Logger

        

 
 
   
Enums
-----

.. autoapisummary::

   jgdv.logging._interface.LogLevel_e

           

 
 

 
 

Protocols
---------

.. autoapisummary::

   jgdv.logging._interface.LogConfig_p

           
   
             
  
           
 
  
           
 
      
 
Module Contents
===============

 
.. py:data:: Formatter
   :type:  TypeAlias
   :value: logmod.Formatter


 
.. py:data:: Handler
   :type:  TypeAlias
   :value: logmod.Handler


 
.. py:data:: Logger
   :type:  TypeAlias
   :value: logmod.Logger


 
 

.. _jgdv.logging._interface.LogLevel_e:
   
.. py:class:: LogLevel_e
   
   Bases: :py:obj:`enum.IntEnum` 
     
   My Preferred Loglevel names

   
   .. py:attribute:: bootstrap
      :value: 0


   .. py:attribute:: detail
      :value: 10


   .. py:attribute:: error
      :value: 40


   .. py:attribute:: trace
      :value: 20


   .. py:attribute:: user
      :value: 30


 
 
 

.. _jgdv.logging._interface.LogConfig_p:
   
.. py:class:: LogConfig_p
   
   Bases: :py:obj:`Protocol` 
     
   TODO

   
   .. py:method:: set_level(level: int | str) -> None

   .. py:method:: setup(config: jgdv.structs.chainguard.ChainGuard) -> None

   .. py:method:: subprinter(*names: str) -> Logger

 
 
   
