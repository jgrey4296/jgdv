 

 
.. _jgdv.structs.chainguard.proxies.failure:
   
    
=======================================
jgdv.structs.chainguard.proxies.failure
=======================================

   
.. py:module:: jgdv.structs.chainguard.proxies.failure

.. autoapi-nested-parse::

   A Proxy for ChainGuard,
     which allows you to use the default attribute access
     (data.a.b.c)
     even when there might not be an `a.b.c` path in the data.

     Thus:
     data.on_fail(default_value).a.b.c()

     Note: To distinguish between not giving a default value,
     and giving a default value of `None`,
     wrap the default value in a tuple: (None,)

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.chainguard.proxies.failure.GuardFailureProxy
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.chainguard.proxies.failure.GuardFailureProxy:
   
.. py:class:: GuardFailureProxy(data: jgdv.structs.chainguard._base.GuardBase, types: Any = None, index: jgdv.Maybe[list[str]] = None, fallback: jgdv.structs.chainguard._base.TomlTypes | Never = Never)
   
   Bases: :py:obj:`jgdv.structs.chainguard.proxies.base.GuardProxy` 
     
   A Wrapper for guarded access to toml values.
   you get the value by calling it.
   Until then, it tracks attribute access,
   and reports that to GuardBase when called.
   It also can type check its value and the value retrieved from the toml data

   
   .. py:method:: _inject(val: tuple[Any] = Never, attr: jgdv.Maybe[str] = None, clear: bool = False) -> jgdv.structs.chainguard.proxies.base.GuardProxy

 
 
   
