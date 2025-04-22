 

 
.. _jgdv.structs.chainguard:
   
    
=======================
jgdv.structs.chainguard
=======================

   
.. py:module:: jgdv.structs.chainguard

.. autoapi-nested-parse::

   Utility classes for attribute based access to loaded toml data ::

       # Simplifies:
       data['blah']['awe']['awg']
       # to:
       data.blah.awe.awg

       # Also allows guarded access:

       result = data.on_fail('fallback').somewhere.along.this.doesnt.exist()
       result == "fallback" or data.somewhere.along.this.doesnt.exist


   The underlying Python access model (simplified)::

       object.__getattribute(self, name):
           try:
               return self.__dict__[name]
           except AttributeError:
               return self.__getattr__(name)

   So by looking up values in ChainGuard.__table and handling missing values,
   we can skip dict style key access

       
 

Submodules
----------
   
.. toctree::
   :maxdepth: 1

   /_docs/autoapi/jgdv/structs/chainguard/_base/index
   /_docs/autoapi/jgdv/structs/chainguard/_interface/index
   /_docs/autoapi/jgdv/structs/chainguard/chainguard/index
   /_docs/autoapi/jgdv/structs/chainguard/errors/index
   /_docs/autoapi/jgdv/structs/chainguard/mixins/index
   /_docs/autoapi/jgdv/structs/chainguard/proxies/index

   
 

 
      
 
   
