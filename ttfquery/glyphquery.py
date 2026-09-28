"""Glyph-specific queries on font-files"""
import logging
import string

from ttfquery import describe
from ttfquery.errors import FontError

log = logging.getLogger(__name__)

#: The tables every query here reads, and which a font must carry for any of
#: them to answer: the character map, the outlines and their offsets, the
#: horizontal metrics and their header, the font header, the names, and the
#: typographic metrics.
REQUIRED_TABLES = ('cmap', 'glyf', 'loca', 'hmtx', 'hhea', 'head', 'name', 'OS/2')

#: The characters a line of Latin text is laid out from, which a font that lays
#: out such text gives a glyph and an advance width of its own.
LAYOUT_SAMPLE = string.ascii_letters + string.digits

#: The share of the `LAYOUT_SAMPLE` glyphs a font maps that must carry an
#: advance width, for the font to have a line of text in it. A glyph whose
#: advance is 0 leaves the pen where it was, so the next glyph draws on top of
#: it: that is what a combining mark is for, and a font whose letters are
#: mostly such glyphs stacks a whole line in one place.
MINIMUM_ADVANCING = 0.5


def fontTable(font, tag):
    """The font's `tag` table, or a FontError saying it has none

    The format requires each of `REQUIRED_TABLES`, so a font without one is a
    font this package cannot answer about rather than a caller asking wrongly.
    """
    try:
        return font[tag]
    except KeyError as err:
        raise FontError(
            """Font has no %r table, so it cannot be queried"""% (tag,)
        ) from err


def unusable(font):
    """Why no text can be laid out with this font, or an empty list

    Reads the font's tables and no glyph outline, so it is cheap enough to ask
    of every font on a machine, which :meth:`ttfquery.ttffiles.Registry.scan`
    does of each font before it registers one.

    Each reason is a sentence about what the file holds. A font that answers
    with any of them still opens, and the queries here still report what it
    says; what it says cannot be laid out into a line of text.

    A file damaged so badly that its tables cannot be read at all answers with
    the reason it could not be read, rather than raising: this is the question a
    caller asks in order to leave such a font alone, so it is the one call here
    that reports a damaged font instead of refusing to answer about it.
    """
    try:
        return _unusable(font)
    except Exception as err:  # noqa: BLE001 a damaged table raises whatever fontTools meets in it first, and the reason is the answer either way
        return [
            'cannot be read: %s: %s' % (type(err).__name__, err)
        ]


def _unusable(font):
    """The reasons :func:`unusable` reports, reading the tables directly"""
    reasons = []
    missing = [tag for tag in REQUIRED_TABLES if tag not in font]
    if missing:
        # Nothing below can be read without them, so this is the whole answer.
        return ['has no %s table' % (', '.join(missing),)]

    if not font['cmap'].tables:
        return ['has no encoding sub-table in its cmap, so it maps no characters']

    unitsPerEm = font['head'].unitsPerEm
    if not unitsPerEm:
        reasons.append('gives its em square a size of %r' % (unitsPerEm,))

    os2 = font['OS/2']
    absent = [
        field for field in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap')
        if not hasattr(os2, field)
    ]
    if absent:
        reasons.append(
            'has an OS/2 table of version %r, which has no %s'
            % (getattr(os2, 'version', None), ', '.join(absent))
        )
    elif not charHeight(font):
        reasons.append(
            'gives its ascender and descender the same value, so its '
            'characters have no height'
        )

    metrics = font['hmtx'].metrics
    advancing = mapped = 0
    for char in LAYOUT_SAMPLE:
        glyfName = explicitGlyph(font, char)
        if glyfName is None:
            continue
        mapped += 1
        if metrics.get(glyfName, (0, 0))[0]:
            advancing += 1
    if mapped and advancing < mapped * MINIMUM_ADVANCING:
        reasons.append(
            'gives %s of the %s letters and digits it maps an advance width '
            'of 0, so they draw on top of one another'
            % (mapped - advancing, mapped)
        )
    return reasons


def hasGlyph( font, char, encoding=None ):
    """Check to see if font appears to have explicit glyph for char"""
    glyfName = explicitGlyph( font, char, encoding )
    if glyfName is None:
        return False
    return True
def explicitGlyph( font, char, encoding=None ):
    """Return glyphName or None if there is not explicit glyph for char"""
    cmap = fontTable( font, 'cmap' )
    if encoding is None:
        encoding = describe.guessEncoding( font )
    subTable = cmap.getcmap( *encoding )
    if subTable is None:
        raise FontError(
            """Font has no %r sub-table in its cmap, available: %s"""% (
                tuple(encoding),
                [(sub.platformID, sub.platEncID) for sub in cmap.tables],
            )
        )
    glyfName = subTable.cmap.get( ord(char))
    return glyfName

def glyphName( font, char, encoding=None, warnOnFailure=1 ):
    """Retrieve the glyph name for the given character

    XXX
        Not sure what the effect of the Unicode mapping
        will be given the use of ord...
    """
    glyfName = explicitGlyph( font, char, encoding )
    if glyfName is None:
        encoding = describe.guessEncoding( font )       #KH
        cmap = fontTable( font, 'cmap' )                #KH
        subTable = cmap.getcmap( *encoding )            #KH
        glyfName = subTable.cmap.get( -1)
        if glyfName is None:
            glyphOrder = fontTable( font, 'glyf' ).glyphOrder
            if not glyphOrder:
                raise FontError(
                    """Font %r has no glyphs at all"""% (
                        describe.shortName(font),
                    )
                )
            glyfName = glyphOrder[0]
            if warnOnFailure:
                log.warning(
                    """Unable to find glyph name for %r, in %r using first glyph in table (%r)""",
                    char,
                    describe.shortName(font),
                    glyfName
                )
    return glyfName

def width( font, glyphName ):
    """Retrieve the width of the giving character for given font

    The horizontal metrics table provides both the
    width and the left side bearing, we should really
    be using the left side bearing to adjust the
    character, but that's a later project.

    The width is the advance width the font itself holds, in font units, which
    is 0 for a glyph the font draws without moving the pen -- a combining mark,
    or any glyph in a font whose metrics are built wrong. :func:`unusable`
    reports a font whose letters are mostly such glyphs.
    """
    try:
        return fontTable( font, 'hmtx' ).metrics[ glyphName ][0]
    except KeyError as err:
        raise ValueError( """Couldn't find glyph for glyphName %r"""%(
            glyphName,
        )) from err

def lineHeight( font ):
    """Get the base-line to base-line height for the font

    XXX
        There is some fudging going on here as I
        workaround what appears to be a problem with the
        specification for sTypoDescender, which states
        that it should normally be a negative value, but
        winds up being positive in at least one font that
        defines points below the zero axis.

    XXX The entire OS/2 table doesn't appear in a few
        fonts (symbol fonts in particular), such as Corel's
        BeeHive and BlackLight 686.  Those raise
        :class:`ttfquery.errors.FontError`, as does a font whose OS/2 table is
        too old to carry the typographic metrics.
    """
    return charHeight(font) + _typographic( font, 'sTypoLineGap' )

def charHeight( font ):
    """Determine the general character height for the font (for scaling)"""
    ascent = _typographic( font, 'sTypoAscender' )
    descent = _typographic( font, 'sTypoDescender' )
    if descent > 0:
        descent = - descent
    return ascent - descent

def charDescent( font ):
    """Determine the general descent for the font (for scaling)"""
    return _typographic( font, 'sTypoDescender' )

def _typographic( font, field ):
    """One of the OS/2 table's typographic metrics, in font units

    Version 0 of that table, which a few old fonts still carry, has none of
    them; a font with such a table raises rather than reporting a height it
    does not state.
    """
    os2 = fontTable( font, 'OS/2' )
    try:
        return getattr( os2, field )
    except AttributeError as err:
        raise FontError(
            """Font's OS/2 table is version %r, which has no %s"""% (
                getattr( os2, 'version', None ), field,
            )
        ) from err
