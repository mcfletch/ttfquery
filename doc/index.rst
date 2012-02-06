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

You can also download the package manually from the Project's `PyPI Page`_,
unpacking and running::

    python setup.py install 

from the unpacked source directory.

You can check out the current `bzr`_ source code like so:

.. code-block:: bash

    $ bzr branch lp:ttfquery
    $ cd ttfquery 
    $ python setup.py develop

.. _`PyPI Page`: http://pypi.python.org/pypi/TTFQuery
.. _`bzr`: http://bazaar.canonical.com/

Command Line Tools
------------------

Most of the command-line tools in TTFQuery are intended primarily as sample 
code for how one would use the library.  That is, they are not really intended 
to be used directly by end-users.

The :mod:`ttfquery.ttffiles` script can be used to create or modify a "registry" of fonts (which 
is normally stored in a file called ``~/.font.cache`` 
(see :mod:`ttfquery._scriptregistry`).  The first argument, if provided, is the 
filename in which to store the registry.  The second argument, if provided, is 
the path to the font-files you would like to recursively add to the registry.

.. code-block:: bash

    (test-install)mcfletch@raistlin:~/pylive/ttfquery/doc$ ttffiles 
    INFO:ttfquery.ttffiles:Failure scanning /home/mcfletch/.fonts/frestysb.ttf
    INFO:ttfquery.ttffiles:1304 fonts available
    (test-install)mcfletch@raistlin:~/pylive/ttfquery/doc$

The :mod:`ttfquery.ttfgroups` script will scan your registry for font-files and 
print out a summary of font groups.  The groups are separated by a dashed line,
with ('Family','Group') then a listing of individual Fonts.  Note that an 
individual Font may have many Font Faces (bold, italic, etceteras):

.. code-block:: bash

    (test-install)mcfletch@raistlin:~/pylive/ttfquery/doc$ ttfgroups 
    WARNING:ttfquery.ttfgroups:Failed reading file '/home/mcfletch/.fonts/monalren.ttf' (code 1):
    ...
    _________________________
    ('ANY', 'ANY')
    Alefbet                          -- 400
    Alexei Copperplate               -- 400
    AlgerianBasD                     -- 400
    ...
    _________________________
    ('SYMBOL', 'MIXED-SERIF')
    SymbolProp BT                    -- 400
    INFO:ttfquery.ttfgroups:Scan took 0.42 seconds CPU time

The :mod:`ttfquery.ttffamily` script will query the :class:`ttfquery.ttffiles.Registry` of font 
groups to find fonts which belong to a given family (for example, the ``SYMBOL``
family above):

.. code-block:: bash

    (test-install)mcfletch@raistlin:~/pylive/ttfquery/doc$ ttffamily 'SYMBOL'
    F SymbolProp BT
      /home/mcfletch/.fonts/symbpron.ttf
    F HehenHebTBol
      /home/mcfletch/.fonts/hehenb.ttf
    F Webdings
      /usr/share/fonts/truetype/msttcorefonts/Webdings.ttf
    F GaramondNo4CyrTCYMed
      /home/mcfletch/.fonts/gar4cyrm.ttf
    F GaramondNo4CyrTCYLig
      /home/mcfletch/.fonts/gar4cyrl.ttf
      /home/mcfletch/.fonts/gar4cyli.ttf
    F NimbusRomDGR
      /home/mcfletch/.fonts/nimbusn.ttf
      /home/mcfletch/.fonts/nimbusi.ttf
      /home/mcfletch/.fonts/nimbusb.ttf
      /home/mcfletch/.fonts/nimbusbi.ttf
    F MT Extra
      /home/mcfletch/.fonts/mtextra.ttf
    F ZapfDingbats BT
      /home/mcfletch/.fonts/zafdingn.ttf
    (test-install)mcfletch@raistlin:~/pylive/ttfquery/doc$

The :mod:`ttfquery.ttfmetadata` script can be used to try to find a particular 
font and print out various metadata about the font.  Note that the individual 
Font Faces may have multiple scales (400, 700), and that each Font will often 
have multiple Font Faces (as seen below):

.. code-block:: bash

    (test-install)mcfletch@raistlin:~/pylive/ttfquery/doc$ ttfmetadata Bodoni
    Font: BauerBodni BT
        Specific Name: Bauer Bodoni BT
        File: /home/mcfletch/.fonts/baubodn.ttf
        Modifiers: (400, 0)
        Family Name: SERIF, ITALIAN
        Specific Name: Bauer Bodoni Bold BT
        File: /home/mcfletch/.fonts/baubodb.ttf
        Modifiers: (700, 0)
        Family Name: SERIF, ITALIAN
    ...
    Font: BauerBodni BdCn BT
        Specific Name: Bauer Bodoni Bold Condensed BT
        File: /home/mcfletch/.fonts/baubodbc.ttf
        Modifiers: (400, 0)
        Family Name: SERIF, ITALIAN

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

