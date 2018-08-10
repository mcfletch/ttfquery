from __future__ import print_function
from ttfquery import findsystem
import pytest
import sys, glob, unittest
pytestmark = pytest.mark.skipif(not sys.platform == 'win32', reason='Win32 tests')

class TestWin32(unittest.TestCase):
    def test_font_directory(self):
        """Validate that the fonts directory windows reports is not empty"""
        dirname = findsystem.win32FontDirectory()
        assert glob.glob(os.path.join(dirname,'*.ttf')), "No .ttf files found in Win32 font directory %s"%(
            dirname,
        )
    def test_fonts_from_registry(self):
        dirname = 'c:\\should-not-exist-and-if-it-does-you-know-you-did-it'
        fontpaths = findsystem.win32InstalledFonts(dirname)
        assert fontpaths, "Did not find any registry-supplied fonts"
