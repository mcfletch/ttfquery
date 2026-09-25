from __future__ import print_function
from ttfquery import ttffiles, describe, glyphquery, glyph
import os
import unittest
import tempfile
import shutil

class TestGlyphQuery(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp(prefix='ttfquery-',suffix='-tests')
        self.registry = os.path.join(self.workdir,'fonts.cache')
        class fakeoptions:
            directories = ()
            registry = self.registry
        self.options = fakeoptions
        self.registry = ttffiles.registry_for_options(self.options)
    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_has_a_glyph(self):
        has,total = 0,0
        for _name,metadata in self.registry.specificFonts.items():
            font = describe.openFont(metadata.file_name)
            glyphquery.charHeight(font)
            glyphquery.lineHeight(font)
            glyphquery.charDescent(font)
            if glyphquery.hasGlyph(font,'a'):
                glyphName = glyphquery.explicitGlyph(font,'a')
                if glyphName:
                    glyphquery.width(font,glyphName)
                    has += 1

                    shape = glyph.Glyph(glyphName)
                    shape.compile(font)
                    assert shape.contours, "No contours generated"
                    assert shape.outlines, "No outlines generated"
                    assert shape.width, "Width of `a` character was null"
                    assert shape.height, "Width of `a` character was null"

            else:
                glyphName = glyphquery.glyphName(font,'a')
                assert glyphName, """Didn't get a placeholder for the 'a' character"""
                glyphquery.width(font,glyphName)
            total += 1
        assert total, "No specific fonts on this system?"
        assert has/float(total) > .2, "More than 4/5 of fonts on this system are missing a glyph for `a`? %s/%s"%(has,total)

