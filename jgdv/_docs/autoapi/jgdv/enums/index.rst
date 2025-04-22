 

 
.. _jgdv.enums:
   
    
==========
jgdv.enums
==========

   
.. py:module:: jgdv.enums

.. autoapi-nested-parse::

   Some Enum's I Keep writing

       
 

   
 

 

 
   
        

 
 
   
Enums
-----

.. autoapisummary::

   jgdv.enums.ActionResult_e
   jgdv.enums.CurrentState_e
   jgdv.enums.LoopControl_e
   jgdv.enums.TaskPolicyEnum

           

 
 

           
   
             
  
           
 
  
           
 
      
 
Package Contents
================

 
 

.. _jgdv.enums.ActionResult_e:
   
.. py:class:: ActionResult_e(*args, **kwds)
   
   Bases: :py:obj:`enum.Enum` 
     
   Enums for how a task can describe its response

   
   .. py:attribute:: FAIL

   .. py:attribute:: HALT

   .. py:attribute:: SKIP

   .. py:attribute:: SUCCEED

 
 
 

.. _jgdv.enums.CurrentState_e:
   
.. py:class:: CurrentState_e(*args, **kwds)
   
   Bases: :py:obj:`enum.Enum` 
     
   Enumeration of the different states a task can be in.

   
   .. py:attribute:: ARTIFACT

   .. py:attribute:: DECLARED

   .. py:attribute:: DEFINED

   .. py:attribute:: EXISTS

   .. py:attribute:: FAILED

   .. py:attribute:: HALTED

   .. py:attribute:: INIT

   .. py:attribute:: READY

   .. py:attribute:: RUNNING

   .. py:attribute:: SUCCESS

   .. py:attribute:: TEARDOWN

   .. py:attribute:: WAIT

 
 
 

.. _jgdv.enums.LoopControl_e:
   
.. py:class:: LoopControl_e(*args, **kwds)
   
   Bases: :py:obj:`enum.Enum` 
     
     Describes how to continue an accumulating loop.
     (like walking a a tree)

   yesAnd     : is a result, and try others.
   yes        : is a result, don't try others, Finish.
   noBut      : not a result, try others.
   no         : not a result, don't try others, Finish.

   
   .. py:property:: loop_no_set
      :classmethod:


   .. py:property:: loop_yes_set
      :classmethod:


   .. py:attribute:: no

   .. py:attribute:: noBut

   .. py:attribute:: yes

   .. py:attribute:: yesAnd

 
 
 

.. _jgdv.enums.TaskPolicyEnum:
   
.. py:class:: TaskPolicyEnum(*args, **kwds)
   
   Bases: :py:obj:`enum.Flag` 
     
   Combinable Policy Types:
   breaker  : fails fast
   bulkhead : limits extent of problem and continues
   retry    : trys to do the action again to see if its resolved
   timeout  : waits then fails
   cache    : reuses old results
   fallback : uses defined alternatives
   cleanup  : uses defined cleanup actions
   debug    : triggers pdb
   pretend  : pretend everything went fine
   accept   : accept the failure

   breaker will overrule bulkhead

   
   .. py:attribute:: ACCEPT

   .. py:attribute:: BREAKER

   .. py:attribute:: BULKHEAD

   .. py:attribute:: CACHE

   .. py:attribute:: CLEANUP

   .. py:attribute:: DEBUG

   .. py:attribute:: FALLBACK

   .. py:attribute:: PRETEND

   .. py:attribute:: RETRY

   .. py:attribute:: TIMEOUT

 
 
   
