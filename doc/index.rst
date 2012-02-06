TTFQuery: Find and Extract Information from TTF Files
=====================================================

TTFQuery builds on the `FontTools-TTX`_ package to allow the Python
programmer to accomplish a number of tasks:

 * query the system to find installed fonts
 * retrieve metadata about any TTF font file
    * this includes the glyph outlines (shape) of individual code-points,
      which allows for rendering the glyphs in 3D (such as is done in 
      `OpenGLContext`_)
 * lookup/find fonts by:
    * abstract family type
    * proper font name
 * build simple metadata registries for run-time font matching
 
.. _`FontTools-TTX`: http://sourceforge.net/projects/fonttools/
.. _`OpenGLContext`: http://pyopengl.sourceforge.net/context

Installation
------------

TTFQuery itself installs into a virtualenv with no difficulties, but its 
dependency (FontTools-TTX) does not currently install via PIP.  Installation
into a virtualenv is as follows:

.. literalinclude:: ../requirements.txt

Command Line Tools
------------------

Most of the command-line tools in TTFQuery are intended primarily as sample 
code for how one would use the library.  That is, they are not really intended 
to be used directly by end-users.

Library Reference:

.. toctree::
   :maxdepth: 2
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

