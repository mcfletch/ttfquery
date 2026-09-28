"""Fonts built in memory, with the metrics and the cmap sub-tables under test

A test that requires a particular number back from a font needs a font whose
numbers are known, and a machine's installed fonts are not that. These build one
to order, so a test says the same thing on every machine and no font file has to
be shipped with the package.
"""
from io import BytesIO

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

from ttfquery import describe

#: A single closed contour, as ttfquery reports one: ((x, y), flag) per point,
#: every point on the curve.
SQUARE = (((100, 0), 1), ((100, 600), 1), ((500, 600), 1), ((500, 0), 1))


def built_font(
    advances, upem=1000, ascender=800, descender=-200, lineGap=100,
    glyphs=None,
):
    """A font held in memory whose metrics are exactly the ones given

    advances -- mapping of character to the advance width, in font units, to
        give that character's glyph in the horizontal metrics.
    glyphs -- mapping of character to the contour to draw for it, as
        ((x, y), onCurve) points; a character not named here gets `SQUARE`, so
        a glyph that compiles to nothing is ttfquery's doing rather than the
        font's.

    The placeholder glyph `.notdef` is left empty, as a font's usually is.
    """
    names = {char: glyphNameFor(char) for char in advances}
    builder = FontBuilder(upem, isTTF=True)
    builder.setupGlyphOrder(['.notdef'] + sorted(names.values()))
    builder.setupCharacterMap({ord(char): name for char, name in names.items()})

    outlines = {'.notdef': TTGlyphPen(None).glyph()}
    for char, name in names.items():
        points = (glyphs or {}).get(char, SQUARE)
        pen = TTGlyphPen(None)
        pen.moveTo(points[0][0])
        for point, _onCurve in points[1:]:
            pen.lineTo(point)
        pen.closePath()
        outlines[name] = pen.glyph()
    builder.setupGlyf(outlines)

    builder.setupHorizontalMetrics(
        dict(
            {'.notdef': (upem // 2, 0)},
            **{names[char]: (advance, 100) for char, advance in advances.items()}
        )
    )
    builder.setupHorizontalHeader(ascent=ascender, descent=descender, lineGap=lineGap)
    builder.setupNameTable({'familyName': 'TTFQuery Built', 'styleName': 'Regular'})
    builder.setupOS2(
        sTypoAscender=ascender, sTypoDescender=descender, sTypoLineGap=lineGap,
    )
    builder.setupPost()

    stream = BytesIO()
    builder.save(stream)
    stream.seek(0)
    return stream


def glyphNameFor(char):
    """The name `built_font` gives the glyph it draws for `char`"""
    return 'glyph%04X' % (ord(char),)


def built_open(*arguments, **named):
    """A font built by `built_font`, opened the way a caller opens one

    tables -- the tables to take back out of the font once it is open, for a
        font that has not got what the format requires. Taken out here rather
        than left out of the file, because a file without them is one fontTools
        will not write.
    fields -- the OS/2 table fields to take out, for a table too short to carry
        the typographic metrics.
    """
    tables = named.pop('tables', ())
    fields = named.pop('fields', ())
    font = describe.openFont(built_font(*arguments, **named))
    for tag in tables:
        del font[tag]
        if tag == 'glyf':
            # loca indexes the outlines and means nothing without them
            del font['loca']
    for field in fields:
        delattr(font['OS/2'], field)
    return font


def withSubtables(font, mapping):
    """Give an open font exactly these cmap sub-tables

    mapping -- (platformID, platEncID) to the {code point: glyph name} that
        sub-table holds, in the order the font is to carry them.

    Each sub-table can map the same code point to a different glyph, which is
    how a test says which sub-table a lookup read.
    """
    tables = []
    for (platformID, platEncID), cmap in mapping.items():
        subTable = CmapSubtable.newSubtable(4)
        subTable.platformID = platformID
        subTable.platEncID = platEncID
        # 0 is the only language for a Unicode or Windows sub-table, and the
        # `language-neutral` value for a Macintosh one.
        subTable.language = 0
        subTable.cmap = dict(cmap)
        tables.append(subTable)
    font['cmap'].tables = tables
    return font
