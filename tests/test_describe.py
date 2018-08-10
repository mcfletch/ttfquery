from __future__ import print_function
from ttfquery import describe, findsystem
import pytest
import sys, glob, unittest

class TestDescribe(unittest.TestCase):
    def test_describe_system_fonts(self):
        for fontfile in list(findsystem.findFonts())[:100]:
            try:
                font = describe.openFont(fontfile)
            except Exception as err:
                err.args += ('Error opening font', font)
                raise 
            else:
                short = describe.shortName( font )
                assert short, "Null name for font %s"%(fontfile,)
                family = describe.family( font )
                assert len(family)==2, family
                modifiers = describe.modifiers( font )
                assert describe.weightName(modifiers[0])
