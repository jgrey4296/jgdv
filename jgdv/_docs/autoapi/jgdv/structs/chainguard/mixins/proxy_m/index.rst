 

 
.. _jgdv.structs.chainguard.mixins.proxy_m:
   
    
======================================
jgdv.structs.chainguard.mixins.proxy_m
======================================

   
.. py:module:: jgdv.structs.chainguard.mixins.proxy_m

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.chainguard.mixins.proxy_m.GuardProxyEntry_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.structs.chainguard.mixins.proxy_m.GuardProxyEntry_m:
   
.. py:class:: GuardProxyEntry_m
   
    
   A Mixin to add to GuardBase.
   enables handling a number of conditions when accessing values in the underlying data.
   eg:
   tg.on_fail(2, int).a.value() # either get a.value, or 2. whichever returns has to be an int.

   
   .. py:method:: all_of(fallback: Any, types: jgdv.Maybe[Any] = None) -> jgdv.structs.chainguard.proxies.base.GuardProxy
      :abstractmethod:


   .. py:method:: first_of(fallback: Any, types: jgdv.Maybe[Any] = None) -> jgdv.structs.chainguard.proxies.base.GuardProxy
      :abstractmethod:


      get the first non-None value from a index path, even across arrays of tables
      so instead of: data.a.b.c[0].d
      just:          data.first_of().a.b.c.d()


   .. py:method:: flatten_on(fallback: Any) -> jgdv.structs.chainguard.proxies.base.GuardProxy
      :abstractmethod:


      combine all dicts at the call site to form a single dict


   .. py:method:: match_on(**kwargs: tuple[str, Any]) -> jgdv.structs.chainguard.proxies.base.GuardProxy
      :abstractmethod:


   .. py:method:: on_fail(fallback: Any, types: jgdv.Maybe[Any] = None, *, non_root=False) -> jgdv.structs.chainguard.proxies.failure.GuardFailureProxy

      use a fallback value in an access chain,
      eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

      *without* throwing a GuardedAccessError


 
 
   
