 

 
.. _jgdv._abstract.pydantic_proto:
   
    
=============================
jgdv._abstract.pydantic_proto
=============================

   
.. py:module:: jgdv._abstract.pydantic_proto

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv._abstract.pydantic_proto.ProtocolModelMeta
           
 
      
 
Module Contents
===============

 
 

.. _jgdv._abstract.pydantic_proto.ProtocolModelMeta:
   
.. py:class:: ProtocolModelMeta(*args, **kwargs)
   
   Bases: :py:obj:`ProtoMeta`, :py:obj:`PydanticMeta` 
     
   Use as the metaclass for pydantic models which are explicit Protocol implementers

   eg:

   class Example(BaseModel, ExampleProtocol, metaclass=ProtocolModelMeta):...


   
 
 
   
