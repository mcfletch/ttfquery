from __future__ import print_function
from types import SimpleNamespace
import unittest

from fontTools import ttLib
import pytest

from ttfquery import describe, findsystem

class TestDescribe(unittest.TestCase):
    def test_describe_system_fonts(self):
        for fontfile in list(findsystem.findFonts())[:100]:
            try:
                font = describe.openFont(fontfile)
            except Exception as err:
                err.args += ('Error opening font', fontfile)
                raise
            else:
                short = describe.shortName( font )
                assert short, "Null name for font %s"%(fontfile,)
                family = describe.family( font )
                assert len(family)==2, family
                modifiers = describe.modifiers( font )
                assert describe.weightName(modifiers[0])


def a_named_font(name, family):
    """A stand-in font whose name table holds `name` and `family` records."""
    records = [
        SimpleNamespace(nameID=describe.FONT_SPECIFIER_NAME_ID, string=name),
        SimpleNamespace(nameID=describe.FONT_SPECIFIER_FAMILY_ID, string=family),
    ]
    return {'name': SimpleNamespace(names=records)}


class TestTheNameIsText:
    """`shortName` answers what the font calls itself, as text.

    A name record is bytes in one of two encodings, and answering those bytes
    put `b'Open Sans'` into every message that named a font and left the font
    registry decoding what this had just encoded.
    """

    def a_font(self):
        for path in findsystem.findFonts():
            try:
                return describe.openFont(path)
            except (OSError, ttLib.TTLibError):
                continue
        return None

    def test_both_halves_are_strings(self):
        font = self.a_font()
        if font is None:
            pytest.skip('no readable font on this machine')
        name, family = describe.shortName(font)
        assert isinstance(name, str), repr(name)
        assert isinstance(family, str), repr(family)

    def test_a_two_byte_record_is_read_as_utf_16(self):
        font = a_named_font(
            'Ångstrom Bold'.encode('utf-16-be'), 'Ångstrom'.encode('utf-16-be'),
        )
        assert describe.shortName(font) == ('Ångstrom Bold', 'Ångstrom')

    def test_a_single_byte_record_is_read_as_latin_1(self):
        font = a_named_font(b'Open Sans Bold', b'Open Sans')
        assert describe.shortName(font) == ('Open Sans Bold', 'Open Sans')

    def test_text_is_left_as_it_is(self):
        font = a_named_font('Open Sans Bold', 'Open Sans')
        assert describe.shortName(font) == ('Open Sans Bold', 'Open Sans')
