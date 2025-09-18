.. -*- mode: ReST -*-

.. _files:

=====
Files
=====

.. contents:: Contents


:ref:`Files<jgdv.files>` provides some readers and writers for file formats.
Currently those are:

1. :class:`BookmarkCollection <jgdv.files.bookmarks.collection.BookmarkCollection>` format, and
2. :class:`TagFile <jgdv.files.tags.tag_file.TagFile>` file format for working with tags,
3. :class:`SubstitutionFile <jgdv.files.tags.sub_file.SubstitutionFile>` for substituting tags with other tags.


---------
Bookmarks
---------

``BookmarkCollection`` provides a simple means of creating files in the format of:

.. container:: highlight 
               
    .. productionlist:: BookmarkCollection
        BookmarkCollection  : [`Bookmark` "\n"]+
        Bookmark            : `Url` [":" `Tag`]+
        Tag                 : [a-zA-Z0-9._]+


For Example::

    http://www.techdirt.com/articles/20070503/012939.shtml : tech_dirt
    https://www.ribbonfarm.com/2010/09/21/the-seven-dimensions-of-positioning/ : economics : finance : positioning : venkatesh_rao
    https://www.rockpapershotgun.com/2011/07/26/hands-on-horror-mod-grey/ : horror : mod : rock_paper_shotgun
    https://www.rockpapershotgun.com/2012/07/30/age-old-question-pegi-ratings-are-now-uk-law/ : PEGI : UK : age_ratings : game : law : rock_paper_shotgun
    https://www.rockpapershotgun.com/2012/07/30/man-with-a-moody-camera-paranormal/ : horror : rock_paper_shotgun


That is, each line is a bookmark, followed by colon-delimited tags of that
bookmark.
This is then read in using ``BookmarkCollection``:

.. include:: __examples/bookmark_ex.py
   :code: python


----
Tags
----

``TagFile``'s are very simple:

.. container:: highlight

   .. productionlist:: TagFile
       TagFile   : [`TagEntry` "\n"]+
       TagEntry  : `Tag` ":" `Count`
       Tag       : [a-zA-Z0-9._]+
       Count     : [0-9]+
      
Thus:
  
::
   
  AAAI      : 21
  AAF       : 1
  AAIDE     : 1
  AAIHS     : 2
  AALAADIN  : 1
  

ie: They are lists of a tag, then the count of that tag in whatever dataset
these tags are of.

-------------
Substitutions
-------------

Substitutions are just ``TagFile``'s, with one extension to the syntax:

.. container:: highlight

   .. productionlist::
      SubstitutionFile  : [`SubEntry` "\n"]+
      SubEntry          : `Tag` ":" `Count` [":" `Replacement`]+
      Replacement       : `Tag`
      Tag               : [a-zA-Z0-9._]+
      Count             : [0-9]+

      
This allows mispellings to be corrected easily:

::
   
  AAAIb  : 1 : AAAI
  AAAI   : 21
  
