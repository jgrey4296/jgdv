 

 
.. _jgdv._abstract.protocols:
   
    
========================
jgdv._abstract.protocols
========================

   
.. py:module:: jgdv._abstract.protocols

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv._abstract.protocols.ChainGuard

        

           

 
 

 
 

Protocols
---------

.. autoapisummary::

   jgdv._abstract.protocols.ActionGrouper_p
   jgdv._abstract.protocols.ArtifactStruct_p
   jgdv._abstract.protocols.Buildable_p
   jgdv._abstract.protocols.DILogger_p
   jgdv._abstract.protocols.ExecutableTask
   jgdv._abstract.protocols.Factory_p
   jgdv._abstract.protocols.FailHandler_p
   jgdv._abstract.protocols.InstantiableSpecification_p
   jgdv._abstract.protocols.Loader_p
   jgdv._abstract.protocols.Nameable_p
   jgdv._abstract.protocols.Persistent_p
   jgdv._abstract.protocols.SpecStruct_p
   jgdv._abstract.protocols.StubStruct_p
   jgdv._abstract.protocols.TomlStubber_p
   jgdv._abstract.protocols.UpToDate_p
   jgdv._abstract.protocols.Visitor_p

           
   
             
  
           
 
  
           
 
      
 
Module Contents
===============

 
.. py:data:: ChainGuard
   :type:  TypeAlias
   :value: Any


 
 

.. _jgdv._abstract.protocols.ActionGrouper_p:
   
.. py:class:: ActionGrouper_p
   
   Bases: :py:obj:`Protocol` 
     
   For things have multiple named groups of actions

   
   .. py:method:: get_group(name: str) -> jgdv._abstract.types.Maybe[list]

 
 
 

.. _jgdv._abstract.protocols.ArtifactStruct_p:
   
.. py:class:: ArtifactStruct_p
   
   Bases: :py:obj:`Protocol` 
     
   Base class for artifacts, for type matching

   
   .. py:method:: exists(*, data=None) -> bool

 
 
 

.. _jgdv._abstract.protocols.Buildable_p:
   
.. py:class:: Buildable_p
   
   Bases: :py:obj:`Protocol` 
     
   For things that need building, but don't have a separate factory
   TODO add type parameter

   
   .. py:method:: build(*args: Any) -> Self
      :staticmethod:


 
 
 

.. _jgdv._abstract.protocols.DILogger_p:
   
.. py:class:: DILogger_p
   
   Bases: :py:obj:`Protocol` 
     
   Protocol for classes with a dependency injectable logger

   
   .. py:method:: logger() -> Logger

 
 
 

.. _jgdv._abstract.protocols.ExecutableTask:
   
.. py:class:: ExecutableTask
   
   Bases: :py:obj:`Protocol` 
     
   Runners pass off to Tasks/Jobs implementing this protocol
   instead of using their default logic

   
   .. py:method:: check_entry() -> bool

      For signifiying whether to expand/execute this object


   .. py:method:: current_priority() -> int

   .. py:method:: current_status() -> enum.Enum

   .. py:method:: decrement_priority() -> None

   .. py:method:: execute() -> None

      For executing a task


   .. py:method:: execute_action() -> None

      For executing a single action


   .. py:method:: execute_action_group(group_name: str) -> enum.Enum | list

      Optional but recommended


   .. py:method:: expand() -> list

      For expanding a job into tasks


   .. py:method:: force_status(status: enum.Enum) -> None

   .. py:method:: setup() -> None

   .. py:method:: teardown() -> None

      For Cleaning up the task


 
 
 

.. _jgdv._abstract.protocols.Factory_p:
   
.. py:class:: Factory_p
   
   Bases: :py:obj:`Protocol` 
     
   Factory protocol: {type}.build

   
   .. py:method:: build(*args: Any, **kwargs: Any) -> T
      :classmethod:


 
 
 

.. _jgdv._abstract.protocols.FailHandler_p:
   
.. py:class:: FailHandler_p
   
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

   
   .. py:method:: handle_failure(err: Exception, *args: Any, **kwargs: Any) -> jgdv._abstract.types.Maybe[Any]

 
 
 

.. _jgdv._abstract.protocols.InstantiableSpecification_p:
   
.. py:class:: InstantiableSpecification_p
   
   Bases: :py:obj:`Protocol` 
     
   A Specification that can be instantiated further

   
   .. py:method:: instantiate_onto(data: jgdv._abstract.types.Maybe[Self]) -> Self

   .. py:method:: make() -> Self

 
 
 

.. _jgdv._abstract.protocols.Loader_p:
   
.. py:class:: Loader_p
   
   Bases: :py:obj:`Protocol` 
     
   The protocol for something that will load something from the system, a file, etc
   TODO add a type parameter

   
   .. py:method:: load() -> ChainGuard

   .. py:method:: setup(extra_config: ChainGuard) -> Self

 
 
 

.. _jgdv._abstract.protocols.Nameable_p:
   
.. py:class:: Nameable_p
   
   Bases: :py:obj:`Protocol` 
     
   The core protocol of something use as a name

   
 
 
 

.. _jgdv._abstract.protocols.Persistent_p:
   
.. py:class:: Persistent_p
   
   Bases: :py:obj:`Protocol` 
     
   A Protocol for persisting data

   
   .. py:method:: read(target: pathlib.Path) -> None

      Read the target file, creating a new object


   .. py:method:: write(target: pathlib.Path) -> None

      Write this object to the target path


 
 
 

.. _jgdv._abstract.protocols.SpecStruct_p:
   
.. py:class:: SpecStruct_p
   
   Bases: :py:obj:`Protocol` 
     
   Base class for specs, for type matching

   
   .. py:property:: params
      :type: dict | ChainGuard


 
 
 

.. _jgdv._abstract.protocols.StubStruct_p:
   
.. py:class:: StubStruct_p
   
   Bases: :py:obj:`Protocol` 
     
   Base class for stubs, for type matching

   
   .. py:method:: to_toml() -> str

 
 
 

.. _jgdv._abstract.protocols.TomlStubber_p:
   
.. py:class:: TomlStubber_p
   
   Bases: :py:obj:`Protocol` 
     
   Something that can be turned into toml

   
   .. py:method:: class_help() -> str
      :classmethod:


   .. py:method:: stub_class(stub: StubStruct_p) -> None
      :classmethod:


      Specialize a StubStruct_p to describe this class


   .. py:method:: stub_instance(stub: StubStruct_p) -> None

      Specialize a StubStruct_p with the settings of this specific instance


   .. py:property:: doc
      :type: list[str]


   .. py:property:: short_doc
      :type: str


      Generate Job Class 1 line help string

 
 
 

.. _jgdv._abstract.protocols.UpToDate_p:
   
.. py:class:: UpToDate_p
   
   Bases: :py:obj:`Protocol` 
     
   For things (often artifacts) which might need to have actions done if they were created too long ago

   
   .. py:method:: is_stale(*, other: Any = None) -> bool

      Query whether the task's artifacts have become stale and need to be rebuilt


 
 
 

.. _jgdv._abstract.protocols.Visitor_p:
   
.. py:class:: Visitor_p
   
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

   
   .. py:method:: visit(**kwargs: Any) -> Any

 
 
   
