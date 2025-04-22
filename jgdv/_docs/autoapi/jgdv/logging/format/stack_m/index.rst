 

 
.. _jgdv.logging.format.stack_m:
   
    
===========================
jgdv.logging.format.stack_m
===========================

   
.. py:module:: jgdv.logging.format.stack_m

       
 

   
 

 

 
   
        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.logging.format.stack_m.StackFormatter_m
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.logging.format.stack_m.StackFormatter_m:
   
.. py:class:: StackFormatter_m
   
    
   A Mixin Error formatter, adapted from stackprinter's docs
   Compactly Formats the error stack trace, without src.


   
   .. py:method:: formatException(exc_info)

   .. py:method:: formatStack(stack_info)

   .. py:attribute:: indent_str
      :type:  ClassVar[str]
      :value: '  |  '


   .. py:attribute:: source_height
      :type:  ClassVar[int]
      :value: 10


   .. py:attribute:: source_lines
      :type:  ClassVar[int | str]
      :value: 0


   .. py:attribute:: suppress
      :type:  ClassVar[list[jgdv.RxStr]]
      :value: ['.*pydantic.*', '<frozen importlib._bootstrap>']


   .. py:attribute:: use_stackprinter
      :type:  bool
      :value: True


 
 
   
