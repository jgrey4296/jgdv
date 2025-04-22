 

 
.. _jgdv.cli.errors:
   
    
===============
jgdv.cli.errors
===============

   
.. py:module:: jgdv.cli.errors

       
 

   
 

 

 
   
        

           

 
 

           
   
 

Exceptions
----------

.. autoapisummary::

   jgdv.cli.errors.ArgParseError
   jgdv.cli.errors.CmdParseError
   jgdv.cli.errors.HeadParseError
   jgdv.cli.errors.ParseError
   jgdv.cli.errors.SubCmdParseError

             
  
           
 
  
           
 
      
 
Module Contents
===============

 
 

.. _jgdv.cli.errors.ArgParseError:
   
.. py:exception:: ArgParseError
   
   Bases: :py:obj:`ParseError` 
     
   For when a head/cmd/subcmds arguments are bad

   
 
 
 

.. _jgdv.cli.errors.CmdParseError:
   
.. py:exception:: CmdParseError
   
   Bases: :py:obj:`ParseError` 
     
   For when parsing the command section fails

   
 
 
 

.. _jgdv.cli.errors.HeadParseError:
   
.. py:exception:: HeadParseError
   
   Bases: :py:obj:`ParseError` 
     
   For When an error occurs parsing the head

   
 
 
 

.. _jgdv.cli.errors.ParseError:
   
.. py:exception:: ParseError
   
   Bases: :py:obj:`jgdv.errors.JGDVError` 
     
   A Base Error Class for JGDV CLI Arg Parsing

   
 
 
 

.. _jgdv.cli.errors.SubCmdParseError:
   
.. py:exception:: SubCmdParseError
   
   Bases: :py:obj:`ParseError` 
     
   For when the subcmd section fails

   
 
 
   
