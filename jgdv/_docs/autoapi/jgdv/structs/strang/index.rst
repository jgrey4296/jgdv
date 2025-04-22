 

 
.. _jgdv.structs.strang:
   
    
===================
jgdv.structs.strang
===================

   
.. py:module:: jgdv.structs.strang

.. autoapi-nested-parse::

   Strang, a Structured String class.

   Strangs are str's, and can be used as str's.
   But they validate their format, and allow access to sub parts. eg::

       v = Strang("group::body.name")
       v[0:] == "group"
       v[1:] == "body.name"
       v[1:0] == "body"
       v[1:1] == "name"

   There is also a specialized strang CodeReference.
   for easily importing code::

       v = CodeReference("fn::jgdv.identity_fn")
       assert(callable(v()))
       assert(v() == jgdv.identity_fn)

       
 

Submodules
----------
   
.. toctree::
   :maxdepth: 1

   /_docs/autoapi/jgdv/structs/strang/_interface/index
   /_docs/autoapi/jgdv/structs/strang/_mixins/index
   /_docs/autoapi/jgdv/structs/strang/code_ref/index
   /_docs/autoapi/jgdv/structs/strang/errors/index
   /_docs/autoapi/jgdv/structs/strang/strang/index

   
 

 
      
 
   
