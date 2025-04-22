 

 
.. _jgdv.structs.dkey.decorator:
   
    
===========================
jgdv.structs.dkey.decorator
===========================

   
.. py:module:: jgdv.structs.dkey.decorator

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.structs.dkey.decorator.Signature

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.structs.dkey.decorator.DKeyExpansionDecorator
    jgdv.structs.dkey.decorator.DKeyMetaDecorator
    jgdv.structs.dkey.decorator.DKeyed
    jgdv.structs.dkey.decorator.DKeyedMeta
    jgdv.structs.dkey.decorator.DKeyedRetrieval
           
 
      
 
Module Contents
===============

 
.. py:data:: Signature
   :type:  TypeAlias
   :value: inspect.Signature


 
 

.. _jgdv.structs.dkey.decorator.DKeyExpansionDecorator:
   
.. py:class:: DKeyExpansionDecorator(keys: list[jgdv.structs.dkey.core.meta.DKey], ignores: jgdv.Maybe[list[str]] = None, **kwargs)
   
   Bases: :py:obj:`jgdv.decorators.DataDec` 
     
   Utility class for idempotently decorating actions with auto-expanded keys


   
   .. py:method:: _validate_sig_h(sig: Signature, form: jgdv.decorators.DForm_e, args: jgdv.Maybe[list[jgdv.structs.dkey.core.meta.DKey]] = None) -> None

   .. py:method:: _wrap_fn_h(fn: jgdv.Func[DKeyExpansionDecorator._wrap_fn_h.In, DKeyExpansionDecorator._wrap_fn_h.Out]) -> jgdv.decorators.Decorated[jgdv.Func[DKeyExpansionDecorator._wrap_fn_h.In, DKeyExpansionDecorator._wrap_fn_h.Out]]

      override this to add a decorator to a function


   .. py:method:: _wrap_method_h(meth: jgdv.Method[DKeyExpansionDecorator._wrap_method_h.In, DKeyExpansionDecorator._wrap_method_h.Out]) -> jgdv.decorators.Decorated[jgdv.Method[DKeyExpansionDecorator._wrap_method_h.In, DKeyExpansionDecorator._wrap_method_h.Out]]

      Override this to add a decoration function to method


   .. py:attribute:: _param_ignores
      :type:  tuple[str, Ellipsis]

 
 
 

.. _jgdv.structs.dkey.decorator.DKeyMetaDecorator:
   
.. py:class:: DKeyMetaDecorator(*args, **kwargs)
   
   Bases: :py:obj:`jgdv.decorators.MetaDec` 
     
   A Meta decorator that registers keys for input and output
   verification

   
 
 
 

.. _jgdv.structs.dkey.decorator.DKeyed:
   
.. py:class:: DKeyed
   
    
   Decorators for actions

   It registers arguments on an action and extracts them from the spec and state automatically.

   provides: expands/paths/types/requires/returns/args/kwargs/redirects
   The kwarg 'hint' takes a dict and passes the contents to the relevant expansion method as kwargs

   arguments are added to the tail of the action args, in order of the decorators.
   the name of the expansion is expected to be the name of the action parameter,
   with a "_" prepended if the name would conflict with a keyword., or with "_ex" as a suffix
   eg: @DKeyed.paths("from") -> def __call__(self, spec, state, _from):...
   or: @DKeyed.paths("from") -> def __call__(self, spec, state, from_ex):...

   
   .. py:attribute:: _decoration_builder
      :type:  ClassVar[type]

   .. py:attribute:: _extensions
      :type:  ClassVar[set[type]]

 
 
 

.. _jgdv.structs.dkey.decorator.DKeyedMeta:
   
.. py:class:: DKeyedMeta
   
   Bases: :py:obj:`DKeyed` 
     
   Mixin for decorators that declare meta information,
   but doesnt modify the behaviour

   
   .. py:method:: requires(*args, **kwargs) -> DKeyMetaDecorator
      :classmethod:


      mark an action as requiring certain keys to in the state, but aren't expanded


   .. py:method:: returns(*args, **kwargs) -> DKeyMetaDecorator
      :classmethod:


      mark an action as needing to return certain keys


 
 
 

.. _jgdv.structs.dkey.decorator.DKeyedRetrieval:
   
.. py:class:: DKeyedRetrieval
   
   Bases: :py:obj:`jgdv.decorators.DecoratorAccessor_m`, :py:obj:`DKeyed` 
     
   Mixin for decorators which modify the calling behaviour of the decoration target



   
   .. py:method:: args(fn) -> jgdv.Decorator
      :classmethod:


      mark an action as using spec.args


   .. py:method:: expands(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


      mark an action as using expanded string keys


   .. py:method:: formats(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


   .. py:method:: kwargs(fn) -> jgdv.Decorator
      :classmethod:


      mark an action as using all kwargs


   .. py:method:: paths(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


      mark an action as using expanded path keys


   .. py:method:: postbox(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


   .. py:method:: redirects(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


      mark an action as using redirection keys


   .. py:method:: references(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


      mark keys to use as to_coderef imports


   .. py:method:: toggles(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


   .. py:method:: types(*args, **kwargs) -> jgdv.Decorator
      :classmethod:


      mark an action as using raw type keys


   .. py:attribute:: _decoration_builder
      :type:  ClassVar[type]

 
 
   
