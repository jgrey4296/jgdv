 

 
.. _jgdv.structs.locator._interface:
   
    
===============================
jgdv.structs.locator._interface
===============================

   
.. py:module:: jgdv.structs.locator._interface

       
 

   
 

 

 
   
        

 
 
   
Enums
-----

.. autoapisummary::

   jgdv.structs.locator._interface.LocationMeta_e
   jgdv.structs.locator._interface.WildCard_e

           

 
 

 
 

Protocols
---------

.. autoapisummary::

   jgdv.structs.locator._interface.Location_p
   jgdv.structs.locator._interface.Locator_p

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.locator._interface.Location_d
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.locator._interface.LocationMeta_e:
   
.. py:class:: LocationMeta_e
   
   Bases: :py:obj:`enum.StrEnum` 
     
   Available metadata attachable to a location

   
   .. py:attribute:: abstract
      :value: 'abstract'


   .. py:attribute:: artifact
      :value: 'artifact'


   .. py:attribute:: clean
      :value: 'clean'


   .. py:attribute:: default

   .. py:attribute:: dir

   .. py:attribute:: directory
      :value: 'directory'


   .. py:attribute:: earlycwd
      :value: 'earlycwd'


   .. py:attribute:: expand
      :value: 'expand'


   .. py:attribute:: file
      :value: 'file'


   .. py:attribute:: loc

   .. py:attribute:: location
      :value: 'location'


   .. py:attribute:: partial
      :value: 'partial'


   .. py:attribute:: protect
      :value: 'protect'


   .. py:attribute:: remote
      :value: 'remote'


 
 
 

.. _jgdv.structs.locator._interface.WildCard_e:
   
.. py:class:: WildCard_e
   
   Bases: :py:obj:`enum.StrEnum` 
     
   Ways a path can have a wildcard.

   
   .. py:attribute:: glob
      :value: '*'


   .. py:attribute:: key
      :value: '{'


   .. py:attribute:: rec_glob
      :value: '**'


   .. py:attribute:: select
      :value: '?'


 
 
 

.. _jgdv.structs.locator._interface.Location_p:
   
.. py:class:: Location_p
   
   Bases: :py:obj:`Protocol` 
     
   Something which describes a file system location,
   with a possible identifier, and metadata

   
   .. py:method:: keys() -> set[str]

 
 
 

.. _jgdv.structs.locator._interface.Locator_p:
   
.. py:class:: Locator_p
   
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

   
 
 
 

.. _jgdv.structs.locator._interface.Location_d:
   
.. py:class:: Location_d
   
    
   
   .. py:attribute:: key
      :type:  jgdv.Maybe[str | jgdv.structs.dkey.Key_p]

   .. py:attribute:: meta
      :type:  enum.EnumMeta

   .. py:attribute:: path
      :type:  pathlib.Path

 
 
   
