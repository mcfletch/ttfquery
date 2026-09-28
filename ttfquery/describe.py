"""Extract meta-data from a font-file to describe the font"""
import logging

from fontTools import ttLib

from ttfquery.errors import FontError

unicode = str
long = int
log = logging.getLogger(__name__)


def openFont(filename):
    """Get a new font object

    filename -- the path to a font file, or an open binary file

    A file that is not a font raises :class:`ttfquery.errors.FontError`, so that
    a caller working through a directory of files can tell one it cannot use
    from a fault of its own. A path that cannot be opened raises the `OSError`
    of opening it, which is about the path rather than about any font.

    The font is read as fontTools reads one, a table at a time as they are
    asked for, so damage further into the file is found by the query that reads
    that part. :func:`ttfquery.glyphquery.unusable` reads the tables a query
    needs and reports such a font rather than raising.
    """
    if isinstance(filename, (bytes, unicode)):
        filename = open(filename, "rb")
    try:
        return ttLib.TTFont(filename)
    except ttLib.TTLibError as err:
        raise FontError(
            """%s is not a font file that can be read: %s"""% (
                getattr(filename, 'name', 'The font'), err,
            )
        ) from err


FONT_SPECIFIER_NAME_ID = 4
FONT_SPECIFIER_FAMILY_ID = 1


def _recordText(value):
    """A name record as text, whichever way the font stored it.

    A record is bytes in one of two encodings and the font does not say which:
    UTF-16BE where it carries the NUL bytes of one, and a single-byte encoding
    otherwise -- Latin-1, which is what the Macintosh Roman a name table names
    agrees with for the characters a font name uses.
    """
    if not isinstance(value, bytes):
        return value
    return (value.decode("utf-16-be") if b"\000" in value
            else value.decode("latin-1"))


def shortName(font):
    """The font's own name and its family's, as text

    ``('Open Sans Bold Italic', 'Open Sans')`` -- what the font calls itself,
    and the family it belongs to.
    """
    name = ""
    family = ""
    for record in font["name"].names:
        if record.nameID == FONT_SPECIFIER_NAME_ID and not name:
            name = _recordText(record.string)
        elif record.nameID == FONT_SPECIFIER_FAMILY_ID and not family:
            family = _recordText(record.string)
        if name and family:
            break
    return name, family


FAMILY_NAMES = {
    0: ("ANY", {}),
    1: (
        "SERIF-OLD",
        {
            0: "ANY",
            1: "ROUNDED-LEGIBILITY",
            2: "GARALDE",
            3: "VENETIAN",
            4: "VENETIAN-MODIFIED",
            5: "DUTCH-MODERN",
            6: "DUTCH-TRADITIONAL",
            7: "CONTEMPORARY",
            8: "CALLIGRAPHIC",
            15: "MISCELLANEOUS",
        },
    ),
    2: (
        "SERIF-TRANSITIONAL",
        {
            0: "ANY",
            1: "DIRECT-LINE",
            2: "SCRIPT",
            15: "MISCELLANEOUS",
        },
    ),
    3: (
        "SERIF",
        {
            0: "ANY",
            1: "ITALIAN",
            2: "SCRIPT",
            15: "MISCELLANEOUS",
        },
    ),
    4: (
        "SERIF-CLARENDON",
        {
            0: "ANY",
            1: "CLARENDON",
            2: "MODERN",
            3: "TRADITIONAL",
            4: "NEWSPAPER",
            5: "STUB-SERIF",
            6: "MONOTYPE",
            7: "TYPEWRITER",
            15: "MISCELLANEOUS",
        },
    ),
    5: (
        "SERIF-SLAB",
        {
            0: "ANY",
            1: "MONOTONE",
            2: "HUMANIST",
            3: "GEOMETRIC",
            4: "SWISS",
            5: "TYPEWRITER",
            15: "MISCELLANEOUS",
        },
    ),
    7: (
        "SERIF-FREEFORM",
        {
            0: "ANY",
            1: "MODERN",
            15: "MISCELLANEOUS",
        },
    ),
    8: (
        "SANS",
        {
            0: "ANY",
            1: "GOTHIC-NEO-GROTESQUE-IBM",
            2: "HUMANIST",
            3: "ROUND-GEOMETRIC-LOW-X",
            4: "ROUND-GEOMETRIC-HIGH-X",
            5: "GOTHIC-NEO-GROTESQUE",
            6: "GOTHIC-NEO-GROTESQUE-MODIFIED",
            9: "GOTHIC-TYPEWRITER",
            10: "MATRIX",
            15: "MISCELLANEOUS",
        },
    ),
    9: (
        "ORNAMENTAL",
        {
            0: "ANY",
            1: "ENGRAVER",
            2: "BLACK-LETTER",
            3: "DECORATIVE",
            4: "THREE-DIMENSIONAL",
            15: "MISCELLANEOUS",
        },
    ),
    10: (
        "SCRIPT",
        {
            0: "ANY",
            1: "UNCIAL",
            2: "BRUSH-JOINED",
            3: "FORMAL-JOINED",
            4: "MONOTONE-JOINED",
            5: "CALLIGRAPHIC",
            6: "BRUSH-UNJOINED",
            7: "FORMAL-UNJOINED",
            8: "MONOTONE-UNJOINED",
            15: "MISCELLANEOUS",
        },
    ),
    12: (
        "SYMBOL",
        {
            0: "ANY",
            3: "MIXED-SERIF",
            6: "OLDSTYLE-SERIF",
            7: "NEO-GROTESQUE-SANS",
            15: "MISCELLANEOUS",
        },
    ),
}

WEIGHT_NAMES = {
    "thin": 100,
    "extralight": 200,
    "ultralight": 200,
    "light": 300,
    "normal": 400,
    "regular": 400,
    "plain": 400,
    "medium": 500,
    "semibold": 600,
    "demibold": 600,
    "bold": 700,
    "extrabold": 800,
    "ultrabold": 800,
    "black": 900,
    "heavy": 900,
}
#: Every name for each weight, so a number reads back as the words a font
#: might have used for it.
WEIGHT_NUMBERS: dict[int, list[str]] = {}
for key, value in WEIGHT_NAMES.items():
    WEIGHT_NUMBERS.setdefault(value, []).append(key)


def weightNumber(name):
    """Convert a string-name to a weight number compatible with this module"""
    if isinstance(name, (bytes, unicode)):
        name = name.lower()
        name = name.replace("-", "").replace(" ", "")
        if name and name[-1] == "+":
            name = name[:-1]
            adjust = 50
        elif name and name[-1] == "-":
            name = name[:-1]
            adjust = -50
        else:
            adjust = 0
        return WEIGHT_NAMES[name] + adjust
    else:
        return int(name) or 400  # for cases where number isn't properly specified


def weightName(number):
    """Convert integer number to a human-readable weight-name"""
    number = int(number) or 400
    if number in WEIGHT_NUMBERS:
        return WEIGHT_NUMBERS[number]
    name = "thin-"
    for x in range(100, 1000, 100):
        if number >= x:
            name = WEIGHT_NUMBERS[x][0] + "+"
    return name


def family(font):
    """Get the family (and sub-family) for a font"""
    HIBYTE = 65280
    LOBYTE = 255
    familyID = (font["OS/2"].sFamilyClass & HIBYTE) >> 8
    subFamilyID = font["OS/2"].sFamilyClass & LOBYTE
    return familyNames(familyID, subFamilyID)


def familyNames(familyID, subFamilyID=0):
    """Convert family integers to human-readable names"""
    familyName, subFamilies = FAMILY_NAMES.get(familyID, ("RESERVED", None))
    if familyName == "RESERVED":
        log.warning("Font has invalid (reserved) familyID: %s", familyID)
    if subFamilies:
        subFamily = subFamilies.get(subFamilyID, "RESERVED")
    else:
        subFamily = "ANY"
    return (familyName, subFamily)


def modifiers(font):
    """Get weight and italic modifiers for a font

    weight is taken from the OS/2 usWeightClass field
    italic is taken from either OS/2 fsSelection or
    head macStyle, if either indicates italics we
    report italics
    """
    return (
        # weight as an integer
        font["OS/2"].usWeightClass,
        (font["OS/2"].fsSelection & 1 or font["head"].macStyle & 2),  # italic
    )


#: The cmap sub-tables whose code points are Unicode code points, the most
#: capable first. Platform 0 is Unicode throughout, where encodings 4 and 6
#: carry the whole repertoire and 0 to 3 stop at the Basic Multilingual Plane;
#: on platform 3, Windows, encoding 10 carries the whole repertoire and 1 the
#: BMP. Anything else -- a Macintosh script code, or the symbol encoding (3, 0)
#: -- numbers its characters its own way.
UNICODE_ENCODINGS = (
    (3, 10),
    (0, 6),
    (0, 4),
    (3, 1),
    (0, 3),
    (0, 2),
    (0, 1),
    (0, 0),
)


def guessEncoding(font, given=None):
    """The cmap sub-table to look characters up in, as (platformID, platEncID)

    given -- which sub-table to use, where the caller knows:

        a two-tuple  that sub-table, and a ValueError where the font has not
                     got it
        an integer   the font's first sub-table of that platform, and a
                     ValueError where it has none
        None         the font's most capable Unicode sub-table, in the order of
                     `UNICODE_ENCODINGS`.  A font with none of them answers
                     with the first sub-table it has, which is the whole of
                     what it offers -- a symbol font keeps its glyphs at code
                     points of its own.

    A character reaches the sub-table as `ord(char)`, which is a Unicode code
    point, so a Unicode sub-table is the one that answers about the character
    asked for: any other numbers its characters its own way, and answers with
    whichever glyph it happens to keep at that number.
    """
    if isinstance(given, tuple) and given:
        if len(given) == 2:
            log.debug("Checking for explicitly required encoding %r", given)
            if not font["cmap"].getcmap(*given):
                raise ValueError(
                    """The specified font encoding %r does not appear to be available within the font %r. Available encodings: %s"""
                    % (
                        given,
                        shortName(font),
                        [
                            (table.platformID, table.platEncID)
                            for table in font["cmap"].tables
                        ],
                    )
                )
            return given
        elif len(given) > 2:
            raise TypeError(
                """Encoding must be None, a two-tuple, or an integer, got %r"""
                % (given,)
            )
        else:
            # treat as a single integer, regardless of number of integer's
            given = given[0]
    if isinstance(given, (int, long)):
        for table in font["cmap"].tables:
            if table.platformID == given:
                return (table.platformID, table.platEncID)
        raise ValueError(
            """Could not find encoding with specified platformID==%s within the font %r. Available encodings: %s"""
            % (
                given,
                shortName(font),
                [(table.platformID, table.platEncID) for table in font["cmap"].tables],
            )
        )
    available = [
        (table.platformID, table.platEncID) for table in font["cmap"].tables
    ]
    for encoding in UNICODE_ENCODINGS:
        if encoding in available:
            return encoding
    if available:
        log.debug(
            "%r has no Unicode cmap sub-table, reading characters from its %r "
            "sub-table. Available: %s",
            shortName(font), available[0], available,
        )
        return available[0]
    raise ValueError(
        """There are no encoding tables within the font %r, likely a corrupt font-file"""
        % (shortName(font),)
    )
