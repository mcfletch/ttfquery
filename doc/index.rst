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

Rendering Glyphs for a Font
---------------------------

TTFQuery mostly works using a precomputed metadata cache that lets you search
for fonts by name. This registry/cache is an instance of :class:`ttfquery.ttffiles.Registry`
and it is mostly useful in that it provides fast access to the font metadata
if you are going to be accessing it many times.

For instance, if you wanted to use the `Ubuntu` font on your platform, you would 
do something like this:

.. doctest:

  >>> from ttfquery import scriptregistry, describe
  >>> registry = scriptregistry.get_registry()
  >>> registry.matchName('Ubuntu')
  [u'Ubuntu Mono', u'Ubuntu Condensed', u'Ubuntu']
  >>> registry.fonts.get('Ubuntu')
  {(300, 1): [u'Ubuntu Light Italic'], (300, 0): [u'Ubuntu Light'], (500, 1): [u'Ubuntu Medium Italic'], (500, 0): [u'Ubuntu Medium'], (400, 1): [u'Ubuntu Italic'], (400, 0): [u'Ubuntu'], (700, 1): [u'Ubuntu Bold Italic'], (700, 0): [u'Ubuntu Bold']}
  >>> metadata = registry.specificFonts['Ubuntu']
  FontMetadata(file_name=u'/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf', modifiers=(400, 0), specific_name=u'Ubuntu', font_name=u'Ubuntu', family=('ANY', 'ANY'))
  >>> font = describe.openFont(metadata.file_name)

At this point, we have a FontTools-TTX font instance for the given `Ubuntu` font.
We can now use the :mod:`glyphquery` module to introspect the font and look for the 
appropriate glyphs for rendering a given character:

.. doctest::

  >>> from ttfquery import glyphquery
  >>> name = glyphquery.glyphName(font,'a')

.. note::

  :func:`glyphquery.glyphName` will actually report a placeholder when the 
  font has no glyph for the character, so you'll get an empty box in most fonts.

The final step is to ask the :mod:`ttfquery.glyph` module to render the glyph 
name into a series of outlines/contours that we can pass to our rendering
engine:

.. doctest::

  >>> from ttfquery import glyph
  >>> shape = glyph.Glyph(name)
  >>> shape.compile(font)
  >>> print(shape.contours)
  >>> print(shape.outlines)


Installation
------------

TTFQuery itself installs into a virtualenv with no difficulties. Installation
into a virtualenv is as follows::

  pip install ttfquery

The package requirements are:

.. literalinclude:: ../requirements.txt

You can check out the current `bzr`_ source code like so:

.. code-block:: bash

    $ bzr branch lp:ttfquery
    $ cd ttfquery 
    $ python setup.py develop

You can run the test suite in the checkout by doing:

.. code-block:: bash

    $ tox

.. _`PyPI Page`: http://pypi.python.org/pypi/TTFQuery
.. _`bzr`: http://bazaar.canonical.com/

Command Line Tools
------------------

.. note::

  The arguments and operation of the command line tools changed in the 
  1.x => 2.0 release, as they were updated to use modern argparse operations
  and to use the "script registry" for all of the operations.

Most of the command-line tools in TTFQuery are intended primarily as sample 
code for how one would use the library.  That is, they are not really intended 
to be used directly by end-users.

The :mod:`ttfquery.ttffiles` script can be used to create or modify a "registry" 
of fonts (which is normally stored in a file called ``~/.font.cache`` 
(see :mod:`ttfquery.scriptregistry`).  The first argument, if provided, is the 
filename in which to store the registry.  The second argument, if provided, is 
the path to the font-files you would like to recursively add to the registry.

.. code-block:: python

  from ttfquery import scriptregistry
  registry = scriptregistry.get_registry()

.. program-output:: ttffiles --help
  :prompt:

The :mod:`ttfquery.ttfgroups` script will scan your registry for font-files and 
print out a summary of font groups.  The groups are separated by a dashed line,
with ('Family','Group') then a listing of individual Fonts.  Note that an 
individual Font may have many Font Faces (bold, italic, etceteras):

.. program-output:: ttfgroups
  :prompt:
  :ellipsis: 30

.. program-output:: ttfgroups --help
  :prompt:

The :mod:`ttfquery.ttffamily` script will query the :class:`ttfquery.ttffiles.Registry` of font 
groups to find fonts which belong to a given family (for example, the ``SYMBOL``
family above):

.. program-output:: ttffamily SERIF-OLD
  :prompt:

.. program-output:: ttffamily --help
  :prompt:

The :mod:`ttfquery.ttfmetadata` script can be used to try to find a particular 
font and print out various metadata about the font.  Note that the individual 
Font Faces may have multiple scales (400, 700), and that each Font will often 
have multiple Font Faces (as seen below):

.. program-output:: ttfmetadata 'Ubuntu'
  :prompt:
  :ellipsis: 30

.. program-output:: ttfmetadata --help
  :prompt:

License
-------

TTFQuery is released under the simplified BSD license:

.. literalinclude:: ../license.txt

Library Reference
-----------------

.. toctree::
   :maxdepth: 2
   
   ttfquery
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

