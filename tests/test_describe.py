from __future__ import print_function
from types import SimpleNamespace
import unittest

from fontTools import ttLib
import pytest

from ttfquery import describe, findsystem, glyphquery

from builtfonts import built_open, glyphNameFor, withSubtables

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


class TestTheEncodingIsAUnicodeOne:
    """Which cmap sub-table a character is looked up in.

    A character reaches the sub-table as `ord(char)`, a Unicode code point, so
    the sub-table that answers about the character asked for is a Unicode one.
    A Macintosh or symbol sub-table numbers its characters its own way and
    answers with whichever glyph it keeps at that number, which is a different
    character and, in the fonts where it bites, a different glyph.
    """

    def a_font(self, *encodings, holds=None):
        """A font carrying these cmap sub-tables, in this order

        holds -- (platformID, platEncID) to the character whose glyph that
            sub-table is to keep at code point 97, where it is meant to
            disagree with the others.  Every sub-table holds `a`'s glyph there
            by default, so which sub-table a lookup read shows up in the glyph
            name it answers with.
        """
        holds = holds or {}
        font = built_open({'a': 500, 'b': 500, 'c': 500, 'd': 500})
        return withSubtables(font, {
            encoding: {ord('a'): glyphNameFor(holds.get(encoding, 'a'))}
            for encoding in encodings
        })

    def test_a_unicode_subtable_wins_over_a_macintosh_one(self):
        font = self.a_font((1, 0), (3, 1))
        assert describe.guessEncoding(font) == (3, 1)

    def test_the_order_in_the_file_does_not_decide(self):
        """A font that carries its Macintosh sub-table first is read the same"""
        assert describe.guessEncoding(self.a_font((3, 1), (1, 0))) == \
            describe.guessEncoding(self.a_font((1, 0), (3, 1)))

    def test_a_symbol_subtable_is_not_a_unicode_one(self):
        """Encoding 0 on platform 3 is the symbol range, not the BMP"""
        font = self.a_font((3, 0), (0, 3))
        assert describe.guessEncoding(font) == (0, 3)

    def test_the_whole_repertoire_is_preferred_to_the_bmp(self):
        font = self.a_font((3, 1), (3, 10))
        assert describe.guessEncoding(font) == (3, 10)
        font = self.a_font((0, 3), (0, 4))
        assert describe.guessEncoding(font) == (0, 4)

    def test_every_preference_is_a_unicode_encoding(self):
        for encoding in describe.UNICODE_ENCODINGS:
            assert encoding[0] in (0, 3), encoding
            if encoding[0] == 3:
                assert encoding[1] in (1, 10), encoding

    def test_each_preference_is_chosen_over_a_macintosh_subtable(self):
        for encoding in describe.UNICODE_ENCODINGS:
            font = self.a_font((1, 0), encoding)
            assert describe.guessEncoding(font) == encoding, encoding

    def test_a_font_with_no_unicode_subtable_answers_with_what_it_has(self):
        """A symbol font keeps its glyphs at code points of its own"""
        font = self.a_font((3, 0), (1, 0))
        assert describe.guessEncoding(font) == (3, 0)

    def test_the_glyph_read_is_the_one_the_unicode_subtable_names(self):
        """The reading this preference exists for

        The two sub-tables disagree about what lives at 97: the Macintosh one
        answers with another character's glyph, and the Unicode one with `a`.
        """
        font = self.a_font((1, 0), (3, 1), holds={(1, 0): 'd'})
        assert glyphquery.explicitGlyph(font, 'a') == glyphNameFor('a')
        assert glyphquery.width(font, glyphquery.explicitGlyph(font, 'a')) == 500

    def test_an_encoding_the_caller_names_is_used_as_given(self):
        """A caller who names a sub-table gets that sub-table"""
        font = self.a_font((1, 0), (3, 1), holds={(1, 0): 'd'})
        assert describe.guessEncoding(font, (1, 0)) == (1, 0)
        assert glyphquery.explicitGlyph(font, 'a', (1, 0)) == glyphNameFor('d')

    def test_a_platform_the_caller_names_is_searched(self):
        font = self.a_font((1, 0), (3, 1))
        assert describe.guessEncoding(font, 3) == (3, 1)
        assert describe.guessEncoding(font, (1,)) == (1, 0)

    def test_an_encoding_the_font_has_not_got_says_so(self):
        font = self.a_font((3, 1))
        for given, wanted in (((1, 0), 'does not appear'), (1, 'platformID==1')):
            try:
                describe.guessEncoding(font, given)
            except ValueError as err:
                assert wanted in str(err), err
            else:
                raise AssertionError('%r was accepted' % (given,))

    def test_a_font_with_no_subtables_at_all_says_so(self):
        font = withSubtables(built_open({'a': 500}), {})
        try:
            describe.guessEncoding(font)
        except ValueError as err:
            assert 'no encoding tables' in str(err), err
        else:
            raise AssertionError('a font with no cmap sub-table was accepted')
