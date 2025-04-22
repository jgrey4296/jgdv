 

 
.. _jgdv._abstract.types:
   
    
====================
jgdv._abstract.types
====================

   
.. py:module:: jgdv._abstract.types

.. autoapi-nested-parse::

   Types that help add clarity

   Provides a number of type aliases and shorthands.
   Such as `Weak[T]` for a weakref, `Stack[T]`, `Queue[T]` etc for lists,
   and `Maybe[T]`, `Result[T, E]`, `Either[L, R]`.

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv._abstract.types.AbsPath
   jgdv._abstract.types.CHECKTYPE
   jgdv._abstract.types.Char
   jgdv._abstract.types.Ctor
   jgdv._abstract.types.DateTime
   jgdv._abstract.types.Decorator
   jgdv._abstract.types.Depth
   jgdv._abstract.types.DictItems
   jgdv._abstract.types.DictKeys
   jgdv._abstract.types.DictVals
   jgdv._abstract.types.E_
   jgdv._abstract.types.Either
   jgdv._abstract.types.Fifo
   jgdv._abstract.types.FmtKey
   jgdv._abstract.types.FmtSpec
   jgdv._abstract.types.FmtStr
   jgdv._abstract.types.Frame
   jgdv._abstract.types.Func
   jgdv._abstract.types.Ident
   jgdv._abstract.types.Lambda
   jgdv._abstract.types.Lifo
   jgdv._abstract.types.M_
   jgdv._abstract.types.Maybe
   jgdv._abstract.types.Method
   jgdv._abstract.types.Module
   jgdv._abstract.types.Mut
   jgdv._abstract.types.NoMut
   jgdv._abstract.types.Queue
   jgdv._abstract.types.R_
   jgdv._abstract.types.RelPath
   jgdv._abstract.types.Result
   jgdv._abstract.types.Rx
   jgdv._abstract.types.RxMatch
   jgdv._abstract.types.RxStr
   jgdv._abstract.types.Seconds
   jgdv._abstract.types.Stack
   jgdv._abstract.types.SubOf
   jgdv._abstract.types.TimeDelta
   jgdv._abstract.types.Traceback
   jgdv._abstract.types.Url
   jgdv._abstract.types.VList
   jgdv._abstract.types.Vector
   jgdv._abstract.types.VerSpecStr
   jgdv._abstract.types.VerStr
   jgdv._abstract.types.Weak

        

           

 
 

           
   
             
  
           
 
  
           
 
      
 
Module Contents
===============

 
.. py:data:: AbsPath
   :type:  TypeAlias
   :value: Annotated[pl.Path, lambda x: x.is_absolute()]


 
.. py:data:: CHECKTYPE
   :type:  TypeAlias
   :value: Maybe[type | types.GenericAlias | types.UnionType]


 
.. py:data:: Char
   :type:  TypeAlias
   :value: Annotated[str, lambda x: len(x) == 1]


 
.. py:data:: Ctor
   :type:  TypeAlias
   :value: type[T] | Callable[[*Any], T]


 
.. py:data:: DateTime
   :type:  TypeAlias
   :value: datetime.datetime


 
.. py:data:: Decorator
   :type:  TypeAlias
   :value: Callable[[F], F]


 
.. py:data:: Depth
   :type:  TypeAlias
   :value: Annotated[int, lambda x: 0 <= x]


 
.. py:data:: DictItems
   :type:  TypeAlias
   :value: ItemsView


 
.. py:data:: DictKeys
   :type:  TypeAlias
   :value: KeysView


 
.. py:data:: DictVals
   :type:  TypeAlias
   :value: ValuesView


 
.. py:data:: E_
   :type:  TypeAlias
   :value: Either[L, R]


 
.. py:data:: Either
   :type:  TypeAlias
   :value: L | R


 
.. py:data:: Fifo
   :type:  TypeAlias
   :value: list[T]


 
.. py:data:: FmtKey
   :type:  TypeAlias
   :value: str


 
.. py:data:: FmtSpec
   :type:  TypeAlias
   :value: Annotated[str, None]


 
.. py:data:: FmtStr
   :type:  TypeAlias
   :value: Annotated[str, None]


 
.. py:data:: Frame
   :type:  TypeAlias
   :value: types.FrameType


 
.. py:data:: Func
   :type:  TypeAlias
   :value: Callable[I, O]


 
.. py:data:: Ident
   :type:  TypeAlias
   :value: Annotated[str, UUID]


 
.. py:data:: Lambda
   :type:  TypeAlias
   :value: types.LambdaType[I, O]


 
.. py:data:: Lifo
   :type:  TypeAlias
   :value: list[T]


 
.. py:data:: M_
   :type:  TypeAlias
   :value: Maybe[T]


 
.. py:data:: Maybe
   :type:  TypeAlias
   :value: T | None


 
.. py:data:: Method
   :type:  TypeAlias
   :value: types.MethodType[I, O]


 
.. py:data:: Module
   :type:  TypeAlias
   :value: types.ModuleType


 
.. py:data:: Mut
   :type:  TypeAlias
   :value: Annotated[T, 'Mutable']


 
.. py:data:: NoMut
   :type:  TypeAlias
   :value: Annotated[T, 'Immutable']


 
.. py:data:: Queue
   :type:  TypeAlias
   :value: deque[T]


 
.. py:data:: R_
   :type:  TypeAlias
   :value: Result[T, E]


 
.. py:data:: RelPath
   :type:  TypeAlias
   :value: Annotated[pl.Path, lambda x: not x.is_absolute()]


 
.. py:data:: Result
   :type:  TypeAlias
   :value: T | E


 
.. py:data:: Rx
   :type:  TypeAlias
   :value: Pattern


 
.. py:data:: RxMatch
   :type:  TypeAlias
   :value: Match


 
.. py:data:: RxStr
   :type:  TypeAlias
   :value: Annotated[str, Pattern]


 
.. py:data:: Seconds
   :type:  TypeAlias
   :value: Annotated[int, lambda x: 0 <= x]


 
.. py:data:: Stack
   :type:  TypeAlias
   :value: list[T]


 
.. py:data:: SubOf
   :type:  TypeAlias
   :value: TypeGuard[T]


 
.. py:data:: TimeDelta
   :type:  TypeAlias
   :value: datetime.timedelta


 
.. py:data:: Traceback
   :type:  TypeAlias
   :value: types.TracebackType


 
.. py:data:: Url
   :type:  TypeAlias
   :value: Annotated[str, 'url']


 
.. py:data:: VList
   :type:  TypeAlias
   :value: T | list[T]


 
.. py:data:: Vector
   :type:  TypeAlias
   :value: list[T]


 
.. py:data:: VerSpecStr
   :type:  TypeAlias
   :value: Annotated[str, SpecifierSet]


 
.. py:data:: VerStr
   :type:  TypeAlias
   :value: Annotated[str, Version]


 
.. py:data:: Weak
   :type:  TypeAlias
   :value: ref[T]


 
   
