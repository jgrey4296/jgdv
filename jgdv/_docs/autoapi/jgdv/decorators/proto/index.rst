 

 
.. _jgdv.decorators.proto:
   
    
=====================
jgdv.decorators.proto
=====================

   
.. py:module:: jgdv.decorators.proto

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.decorators.proto.CheckProtocols
    jgdv.decorators.proto.Proto
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.decorators.proto.CheckProtocols:
   
.. py:class:: CheckProtocols
   
    
   A Class Decorator to ensure a class has no abc.abstractmethod's
   or unimplemented protocol members

   pass additional protocols when making the decorator, eg::

       @CheckProtocol(Proto1_p, Proto2_p, AbsClass...)
       class MyClass:
       pass


   
   .. py:method:: get_protos() -> set[Protocol]

      Get the protocols of a type from its mro and annotations


   .. py:method:: test_method(name: str) -> bool

      return True if the named method is abstract still


   .. py:method:: test_protocol(cls) -> list[str]

      Returns a list of methods which are defined in the protocol,
      no where else in the mro.

      ie: they are unimplemented protocol requirements

      Can handle type aliases, so long as they actually point to a protocol.
      | eg: type proto_alias = MyProtocol_p
      | where issubclass(MyProtocol_p, Protocol)


   .. py:method:: validate_protocols(*, protos: jgdv.Maybe[list[Protocol]]) -> type

 
 
 

.. _jgdv.decorators.proto.Proto:
   
.. py:class:: Proto(*protos: Protocol, check=True)
   
   Bases: :py:obj:`jgdv.decorators.core.MonotonicDec` 
     
   Decorator to explicitly annotate a class as an implementer of a set of protocols.

   Protocols are annotated into cls._jgdv_protos : set[Protocol]::

       class ClsName(Supers*, P1, P1..., **kwargs):...

   becomes::

       @Protocols(P1, P2,...)
       class ClsName(Supers): ...

   Protocol *definition* remains the usual way::

       class Proto1(Protocol): ...

       class ExtProto(Proto1, Protocol): ...


   
   .. py:method:: _build_annotations_h(target: jgdv.decorators._interface.Decorable, current: list) -> jgdv.Maybe[list]

      Given a list of the current annotation list,
      return its replacement


   .. py:method:: _validate_target_h(target: jgdv.decorators._interface.Decorable, form: jgdv.decorators._interface.DForm_e, args: jgdv.Maybe[list] = None) -> None

      Abstract class for specialization.
      Given the original target, throw an error here if it isn't 'correct' in some way


   .. py:method:: _wrap_class_h(cls: type) -> jgdv.Maybe[type]

      Override this to decorate a class


   .. py:method:: get(cls: type) -> list[Protocol]
      :staticmethod:


      Get a List of protocols the class is annotated with


   .. py:method:: validate_protocols(cls: type, *protos: Protocol)
      :staticmethod:


   .. py:attribute:: _check
      :type:  bool
      :value: True


   .. py:attribute:: _name_mod
      :value: 'P'


   .. py:attribute:: _protos
      :type:  list
      :value: []


   .. py:attribute:: needs_args
      :value: True


 
 
   
