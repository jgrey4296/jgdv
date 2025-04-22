 

 
.. _jgdv.files.bookmarks.bookmark:
   
    
=============================
jgdv.files.bookmarks.bookmark
=============================

   
.. py:module:: jgdv.files.bookmarks.bookmark

       
 

   
 

 

 
   
 
   
Type Aliases
------------

.. autoapisummary::
   
   jgdv.files.bookmarks.bookmark.UrlParseResult

        

           

 
 

           
   
             
  
           
 
  
 
 
  

   
Classes
-------


.. autoapisummary::

    jgdv.files.bookmarks.bookmark.Bookmark
           
 
      
 
Module Contents
===============

 
.. py:data:: UrlParseResult
   :type:  TypeAlias
   :value: urllib.parse.ParseResult


 
 

.. _jgdv.files.bookmarks.bookmark.Bookmark:
   
.. py:class:: Bookmark(/, **data: Any)
   
   Bases: :py:obj:`pydantic.BaseModel` 
     
   Usage docs: https://docs.pydantic.dev/2.10/concepts/models/

   A base class for creating Pydantic models.

   .. attribute:: __class_vars__

      The names of the class variables defined on the model.

   .. attribute:: __private_attributes__

      Metadata about the private attributes of the model.

   .. attribute:: __signature__

      The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

   .. attribute:: __pydantic_complete__

      Whether model building is completed, or if there are still undefined fields.

   .. attribute:: __pydantic_core_schema__

      The core schema of the model.

   .. attribute:: __pydantic_custom_init__

      Whether the model has a custom `__init__` function.

   .. attribute:: __pydantic_decorators__

      Metadata containing the decorators defined on the model.
      This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

   .. attribute:: __pydantic_generic_metadata__

      Metadata for generic models; contains data used for a similar purpose to
      __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

   .. attribute:: __pydantic_parent_namespace__

      Parent namespace of the model, used for automatic rebuilding of models.

   .. attribute:: __pydantic_post_init__

      The name of the post-init method for the model, if defined.

   .. attribute:: __pydantic_root_model__

      Whether the model is a [`RootModel`][pydantic.root_model.RootModel].

   .. attribute:: __pydantic_serializer__

      The `pydantic-core` `SchemaSerializer` used to dump instances of the model.

   .. attribute:: __pydantic_validator__

      The `pydantic-core` `SchemaValidator` used to validate instances of the model.

   .. attribute:: __pydantic_fields__

      A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.

   .. attribute:: __pydantic_computed_fields__

      A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

   .. attribute:: __pydantic_extra__

      A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
      is set to `'allow'`.

   .. attribute:: __pydantic_fields_set__

      The names of fields explicitly set during instantiation.

   .. attribute:: __pydantic_private__

      Values of private attributes set on the model instance.

   
   .. py:method:: _validate_tags(val)

   .. py:method:: build(line: str, sep=None)
      :staticmethod:


      Build a bookmark from a line of a bookmark file


   .. py:method:: clean(subs)

      run tag substitutions on all tags in the bookmark


   .. py:method:: merge(other) -> Self

      Merge two bookmarks' tags together,
      creating a new bookmark


   .. py:attribute:: _tag_norm_re
      :type:  ClassVar[jgdv.Rx]

   .. py:attribute:: _tag_sep
      :type:  ClassVar[str]
      :value: ' : '


   .. py:attribute:: name
      :type:  str
      :value: 'No Name'


   .. py:attribute:: tags
      :type:  set[str]

   .. py:attribute:: url
      :type:  str

   .. py:property:: url_comps
      :type: UrlParseResult


 
 
   
