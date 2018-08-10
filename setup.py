#!/usr/bin/env python
"""Installs ttfquery using distutils

Run:
    python setup.py install
to install the package from the source archive.
"""
import sys, os, string
from setuptools import setup
HERE = os.path.dirname(__file__)

def find_version( ):
    for line in open( os.path.join( HERE, 'ttfquery','__init__.py')):
        if line.strip().startswith( '__version__' ):
            return line.split('=')[1].strip().strip('"').strip("'")
    raise RuntimeError( """No __version__ = 'string' in __init__.py""" )
version = find_version()

if __name__ == "__main__":

    ### Now the actual set up call
    setup (
        name = "TTFQuery",
        version = version,
        description = "FontTools-based package for querying system fonts",
        author = "Mike C. Fletcher",
        author_email = "mcfletch@users.sourceforge.net",
        url = "http://ttfquery.sourceforge.net/",
        license = "BSD-style, see license.txt for details",

        package_dir = {
            'ttfquery':'ttfquery',
        },
        packages = [
            'ttfquery', 
        ],
	install_requires = ['fonttools','numpy'],
        classifiers= [
            """License :: OSI Approved :: BSD License""",
            """Programming Language :: Python""",
            """Topic :: Software Development :: Libraries :: Python Modules""",
            """Intended Audience :: Developers""",
            """Operating System :: OS Independent""",
            """Topic :: Multimedia :: Graphics""",
        ],
        keywords= 'fonttools,ttf,truetype,outline,font,curve,system fonts',
        long_description= """FontTools-based package for querying system fonts

TTFQuery builds on the FontTools package to allow the Python programmer to accomplish a number of tasks:

    * query the system to find installed fonts
    * retrieve metadata about any TTF font file (even those not yet
      installed)
          o abstract family type
          o proper font name
          o glyph outlines
    * build simple metadata registries for run-time font matching

With these functionalities, it is possible to readily
create OpenGL solid-text rendering libraries which
can accept abstract font-family names as font specifiers
and deliver platform-specific TTF files to match those libraries.

TTFQuery doesn't provide rendering services, but a sample
implementation can be found in the OpenGLContext project, from
which TTFQuery was refactored.
""",
        platforms= ['Any'],
        entry_points={
            'console_scripts': [
                'ttffiles=ttfquery.ttffiles:main',
                'ttffamily=ttfquery.ttffamily:main',
                'ttfgroups=ttfquery.ttfgroups:main',
                'ttfmetadata=ttfquery.ttfmetadata:main',
            ]
        }
    )
    
