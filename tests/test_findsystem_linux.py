from __future__ import print_function
from ttfquery import findsystem
import pytest
import sys, glob, unittest
pytestmark = pytest.mark.skipif(
    not sys.platform.startswith('linux'), 
    reason='Linux tests'
)

class TestLinux(unittest.TestCase):
    def test_font_directory(self):
        """Validate that at least one font directory can be found"""
        directories = findsystem.linuxFontDirectories()
        assert directories, "No font directories were found, *something* should be there"
    def test_fonts_from_registry(self):
        fonts = findsystem.findFonts()
        assert fonts, "No fonts were found in our default font-search paths"
    