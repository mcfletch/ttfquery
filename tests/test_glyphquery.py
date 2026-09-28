"""What glyphquery and glyph read from a font, and which fonts they refuse

`TestGlyphQuery` sweeps the fonts this machine has and requires of each what
ttfquery is responsible for: that the font opens, that a character resolves to a
glyph name, that the metrics read without raising, and that the glyph compiles to
an outline. `TestBuiltFonts` reads fonts built in memory, with the metrics chosen
here, and requires the exact numbers back. `TestUnusableFonts` builds fonts that
no text can be laid out with and requires that they are named as such and kept
out of a registry, and the classes after it that a font whose tables or outlines
contradict the format is refused with a reason rather than by whatever error the
malformed part happens to raise.

The split is where the numbers come from. A font's own metrics are not ours to
require: a glyph may carry an advance width of 0, whether because it is a mark
meant to sit over its neighbour or because the font was built that way, and
either way the width to report is the one the font holds. What the sweep can
insist on is what ttfquery decides, which is what a built font is for.
"""
from io import BytesIO
import os
import shutil
import tempfile
import unittest

from fontTools.ttLib.tables._g_l_y_f import GlyphComponent

from ttfquery import ttffiles, describe, glyphquery, glyph
from ttfquery.errors import FontError, UnusableFont

from builtfonts import SQUARE, built_font, built_open


def check_font(font, char, name):
    """What ttfquery must answer for `char` in `font`, whatever the font holds

    Returns the reasons it did not, each naming `name`, so a sweep reports every
    font rather than stopping at the first one that has something to say, along
    with whether the font had a glyph of its own for the character and the
    compiled glyph where it had one.

    The advance width and the line height are the font's own numbers, and are
    checked for being numbers rather than for being any particular value;
    `TestBuiltFonts` checks the values against a font whose metrics are known.
    """
    problems = []

    def require(condition, message):
        if not condition:
            problems.append('%s: %s' % (name, message))
        return condition

    glyphquery.charHeight(font)
    glyphquery.charDescent(font)
    height = glyphquery.lineHeight(font)
    require(isinstance(height, int), 'line height %r is not an integer' % (height,))

    explicit = glyphquery.hasGlyph(font, char)
    if explicit:
        glyphName = glyphquery.explicitGlyph(font, char)
    else:
        glyphName = glyphquery.glyphName(font, char)
    if not require(glyphName, 'no glyph name for %r' % (char,)):
        return problems, explicit, None

    width = glyphquery.width(font, glyphName)
    require(isinstance(width, int), 'advance width %r is not an integer' % (width,))
    require(width >= 0, 'advance width %r is negative' % (width,))

    if not explicit:
        # A font without the character has nothing of its own to draw for it,
        # and the placeholder is whatever the font keeps at .notdef.
        return problems, explicit, None

    shape = glyph.Glyph(glyphName)
    shape.compile(font)
    require(shape.width == width, 'compiled width %r is not %r' % (shape.width, width))
    require(shape.height == height, 'compiled height %r is not %r' % (shape.height, height))
    require(
        len(shape.outlines) == len(shape.contours),
        'compiled %s contours to %s outlines' % (len(shape.contours), len(shape.outlines)),
    )
    return problems, explicit, shape


class TestGlyphQuery(unittest.TestCase):
    """The fonts this machine has, each read the way a caller reads one"""

    def setUp(self):
        self.workdir = tempfile.mkdtemp(prefix='ttfquery-', suffix='-tests')
        self.registry = os.path.join(self.workdir, 'fonts.cache')

        class fakeoptions:
            directories = ()
            registry = self.registry
        self.options = fakeoptions
        self.registry = ttffiles.registry_for_options(self.options)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_has_a_glyph(self):
        problems, has, total, drawn = [], 0, 0, 0
        for _name, metadata in self.registry.specificFonts.items():
            font = describe.openFont(metadata.file_name)
            found, explicit, shape = check_font(font, 'a', metadata.file_name)
            problems.extend(found)
            has += bool(explicit)
            total += 1
            if shape is not None and shape.contours:
                drawn += 1
        assert not problems, '\n'.join(problems)
        assert total, "No specific fonts on this system?"
        assert has / float(total) > .2, \
            "More than 4/5 of fonts on this system are missing a glyph for `a`? %s/%s" % (has, total)
        assert drawn / float(has) > .5, \
            "Fewer than half the `a` glyphs on this system compiled to an outline? %s/%s" % (drawn, has)

    def test_every_registered_font_is_usable(self):
        """The registry holds only fonts text can be laid out with

        A font directory is full of whatever anyone has installed, so the
        registry's job is to leave out what cannot be used rather than to hand
        it on and let each caller trip over it.
        """
        unusable = []
        for _name, metadata in self.registry.specificFonts.items():
            font = describe.openFont(metadata.file_name)
            reasons = glyphquery.unusable(font)
            if reasons:
                unusable.append('%s: %s' % (metadata.file_name, '; '.join(reasons)))
        assert not unusable, '\n'.join(unusable)


class TestBuiltFonts:
    """Fonts whose metrics are known, so the numbers read back can be required

    Each font is built here rather than shipped, which keeps the metrics under
    test in the test and calls for no font file to be redistributed.
    """

    def test_the_advance_width_is_the_fonts_own(self):
        font = built_open({'a': 0, 'b': 600, 'c': 1})
        for char, advance in (('a', 0), ('b', 600), ('c', 1)):
            glyphName = glyphquery.explicitGlyph(font, char)
            assert glyphquery.width(font, glyphName) == advance, char

    def test_a_zero_advance_glyph_still_compiles(self):
        """A glyph the font gives no width to has its outline all the same

        A glyph with an advance width of 0 leaves the pen where it was, which is
        how a combining mark draws over its neighbour, and its outline is there
        to read like any other.
        """
        font = built_open({'a': 0})
        glyphName = glyphquery.explicitGlyph(font, 'a')
        shape = glyph.Glyph(glyphName)
        shape.compile(font)
        assert shape.width == 0, shape.width
        assert shape.height == 1100, shape.height
        assert len(shape.contours) == 1, shape.contours
        assert len(shape.outlines) == 1, shape.outlines
        assert shape.outlines[0], 'the square compiled to no points'

    def test_a_zero_advance_font_meets_what_the_sweep_requires(self):
        """A font of zero-advance letters is read, not failed

        What the sweep requires of a font is what ttfquery decides about it, so
        a font whose letters carry no advance width passes it: the width read
        back is the font's own, and reporting it is the answer.
        """
        font = built_open({'a': 0})
        problems, explicit, shape = check_font(font, 'a', 'built')
        assert not problems, '\n'.join(problems)
        assert explicit
        assert shape.width == 0, shape.width
        assert shape.contours

    def test_the_line_height_adds_the_line_gap(self):
        font = built_open({'a': 500}, ascender=750, descender=-250, lineGap=50)
        assert glyphquery.charHeight(font) == 1000
        assert glyphquery.charDescent(font) == -250
        assert glyphquery.lineHeight(font) == 1050

    def test_a_character_the_font_lacks_falls_back(self):
        font = built_open({'a': 500})
        assert not glyphquery.hasGlyph(font, 'z')
        assert glyphquery.explicitGlyph(font, 'z') is None
        name = glyphquery.glyphName(font, 'z', warnOnFailure=0)
        assert name == '.notdef', name
        assert glyphquery.width(font, name) == 500

    def test_an_unknown_glyph_name_says_which(self):
        font = built_open({'a': 500})
        try:
            glyphquery.width(font, 'nonesuch')
        except ValueError as err:
            assert 'nonesuch' in str(err), err
        else:
            raise AssertionError('width of an absent glyph name did not raise')


class TestUnusableFonts:
    """A font no text can be laid out with is named as such and left out"""

    def test_a_usable_font_has_no_reasons(self):
        assert glyphquery.unusable(built_open({'a': 500, 'b': 500})) == []

    def test_letters_without_advances_cannot_be_laid_out(self):
        """The failure a font of zero-advance letters is rejected for

        Every glyph in such a font draws at the pen position of the one before
        it, so a line of it stacks in one place; `Code Of Life BRK` is one, and
        FreeType and HarfBuzz read its advances as 0 the same way.
        """
        advances = {char: 0 for char in 'abcdefghij'}
        advances['k'] = 500
        reasons = glyphquery.unusable(built_open(advances))
        assert len(reasons) == 1, reasons
        assert 'advance width of 0' in reasons[0], reasons
        assert '10 of the 11' in reasons[0], reasons

    def test_a_few_zero_advance_glyphs_are_no_reason(self):
        """A font is not rejected for the marks in it

        A glyph with no advance width is how a font draws a mark over the
        character before it, so it takes most of the letters being such glyphs
        before a font has no line of text in it.
        """
        advances = {char: 500 for char in 'abcdefghij'}
        advances['k'] = 0
        assert glyphquery.unusable(built_open(advances)) == []

    def test_a_font_with_no_outlines_is_rejected(self):
        """A CFF/OpenType font, whose outlines this package does not read"""
        reasons = glyphquery.unusable(built_open({'a': 500}, tables=('glyf',)))
        assert len(reasons) == 1, reasons
        assert 'glyf' in reasons[0], reasons

    def test_a_font_without_typographic_metrics_is_rejected(self):
        reasons = glyphquery.unusable(built_open({'a': 500}, tables=('OS/2',)))
        assert reasons == ['has no OS/2 table'], reasons

    def test_an_os2_table_without_the_typographic_metrics_is_rejected(self):
        """An OS/2 table too short to carry them states no line height"""
        reasons = glyphquery.unusable(
            built_open({'a': 500}, fields=('sTypoAscender', 'sTypoLineGap'))
        )
        assert len(reasons) == 1, reasons
        assert 'sTypoAscender, sTypoLineGap' in reasons[0], reasons

    def test_a_zero_em_square_is_rejected(self):
        """Nothing scaled by the em square can be scaled by 0"""
        font = built_open({'a': 500})
        font['head'].unitsPerEm = 0
        reasons = glyphquery.unusable(font)
        assert len(reasons) == 1, reasons
        assert 'em square' in reasons[0], reasons

    def test_characters_with_no_height_are_rejected(self):
        font = built_open({'a': 500}, ascender=0, descender=0)
        reasons = glyphquery.unusable(font)
        assert len(reasons) == 1, reasons
        assert 'no height' in reasons[0], reasons

    def test_the_registry_leaves_an_unusable_font_out(self):
        """A scan registers what it can use and reports what it cannot"""
        workdir = tempfile.mkdtemp(prefix='ttfquery-', suffix='-unusable')
        try:
            usable = os.path.join(workdir, 'usable.ttf')
            with open(usable, 'wb') as file:
                file.write(built_font({char: 500 for char in 'abcdef'}).read())
            broken = os.path.join(workdir, 'broken.ttf')
            with open(broken, 'wb') as file:
                file.write(built_font({char: 0 for char in 'abcdef'}).read())

            registry = ttffiles.Registry()
            new, failed = registry.scan([workdir], force=1)
            assert new == [usable], new
            assert failed == [broken], failed
            assert len(registry.specificFonts) == 1, registry.specificFonts
        finally:
            shutil.rmtree(workdir)

    def test_registering_one_directly_says_why(self):
        workdir = tempfile.mkdtemp(prefix='ttfquery-', suffix='-unusable')
        try:
            broken = os.path.join(workdir, 'broken.ttf')
            with open(broken, 'wb') as file:
                file.write(built_font({char: 0 for char in 'abcdef'}).read())
            registry = ttffiles.Registry()
            try:
                registry.register(broken)
            except UnusableFont as err:
                assert err.file_name == broken, err.file_name
                assert err.reasons, err
                assert broken in str(err), err
            else:
                raise AssertionError('an unusable font registered anyway')
            assert not registry.specificFonts, registry.specificFonts
            assert not registry.files, registry.files
        finally:
            shutil.rmtree(workdir)

    def test_a_truncated_font_is_rejected_rather_than_raising(self):
        """A file cut short is a font to leave alone, not an error to handle

        `unusable` is the question a caller asks in order to skip such a font,
        so it answers with the reason the file could not be read.
        """
        whole = built_font({char: 500 for char in 'abcdef'}).read()
        font = describe.openFont(BytesIO(whole[:len(whole) // 3]))
        reasons = glyphquery.unusable(font)
        assert len(reasons) == 1, reasons
        assert 'cannot be read' in reasons[0], reasons

    def test_a_file_that_is_not_a_font_says_so_when_opened(self):
        for blob in (b'', b'not a font at all' * 20):
            try:
                describe.openFont(BytesIO(blob))
            except FontError as err:
                assert 'not a font file' in str(err), err
            else:
                raise AssertionError('%r opened as a font' % (blob[:20],))

    def test_a_scan_over_damaged_files_keeps_the_good_one(self):
        """One unreadable file among a machine's fonts is not the end of a scan"""
        workdir = tempfile.mkdtemp(prefix='ttfquery-', suffix='-damaged')
        try:
            whole = built_font({char: 500 for char in 'abcdef'}).read()
            files = {
                'usable.ttf': whole,
                'truncated.ttf': whole[:len(whole) // 3],
                'garbage.ttf': b'not a font at all' * 20,
                'empty.ttf': b'',
            }
            for name, blob in files.items():
                with open(os.path.join(workdir, name), 'wb') as file:
                    file.write(blob)

            registry = ttffiles.Registry()
            new, failed = registry.scan([workdir], force=1)
            assert new == [os.path.join(workdir, 'usable.ttf')], new
            assert sorted(os.path.basename(path) for path in failed) == \
                ['empty.ttf', 'garbage.ttf', 'truncated.ttf'], failed
        finally:
            shutil.rmtree(workdir)

    def test_an_unusable_font_is_still_a_value_error(self):
        """`UnusableFont` is a `ValueError`, which is what callers caught"""
        assert issubclass(UnusableFont, FontError)
        assert issubclass(FontError, ValueError)


class TestMissingTables:
    """A query about a font that has not got the table it reads"""

    def test_the_metrics_say_which_table_is_absent(self):
        font = built_open({'a': 500}, tables=('OS/2',))
        for call in (glyphquery.charHeight, glyphquery.charDescent, glyphquery.lineHeight):
            try:
                call(font)
            except FontError as err:
                assert 'OS/2' in str(err), err
            else:
                raise AssertionError('%s answered without an OS/2 table' % (call.__name__,))

    def test_an_outline_says_which_table_is_absent(self):
        font = built_open({'a': 500}, tables=('glyf',))
        shape = glyph.Glyph('glyph0061')
        try:
            shape.compile(font)
        except FontError as err:
            assert 'glyf' in str(err), err
        else:
            raise AssertionError('a glyph compiled without a glyf table')

    def test_an_outline_name_the_font_lacks_says_so(self):
        font = built_open({'a': 500})
        shape = glyph.Glyph('nonesuch')
        try:
            shape.compile(font)
        except FontError as err:
            assert 'nonesuch' in str(err), err
        else:
            raise AssertionError('a glyph compiled from a name the font lacks')


class TestOutlineDecomposition:
    """What `decomposeOutline` makes of the points a contour holds"""

    def test_a_square_keeps_its_corners(self):
        points = glyph.decomposeOutline(list(SQUARE) + [SQUARE[0]])
        for ((x, y), _flag) in SQUARE:
            assert (x, y) in points, ((x, y), points)

    def test_the_overlap_flag_does_not_make_a_point_off_curve(self):
        """Bit 6 says the contours may overlap, not where the point is

        fontTools hands on the flag bits for overlapping contours and for cubic
        control points alongside the on-curve bit, so a point is read a bit at a
        time.
        """
        overlapping = [((x, y), flag | 0x40) for ((x, y), flag) in SQUARE]
        assert glyph.decomposeOutline(overlapping + overlapping[:1]) == \
            glyph.decomposeOutline(list(SQUARE) + [SQUARE[0]])

    def test_a_cubic_outline_is_refused(self):
        """Only quadratic segments are read, so a cubic one is not guessed at"""
        cubic = list(SQUARE) + [((300, 800), glyph.FLAG_CUBIC)]
        try:
            glyph.decomposeOutline(cubic)
        except FontError as err:
            assert 'cubic' in str(err), err
        else:
            raise AssertionError('a cubic outline was decomposed as quadratic')

    def test_a_contour_that_cannot_start_on_the_curve_is_refused(self):
        """A contour whose points are all off-curve has no segment to read"""
        floating = [((100, 0), 0), ((200, 0), 0), ((150, 100), 1)]
        try:
            glyph.decomposeOutline(floating)
        except FontError as err:
            assert 'off-curve' in str(err), err
        else:
            raise AssertionError('a contour starting off-curve was decomposed')

    def test_too_few_points_is_no_outline(self):
        assert glyph.decomposeOutline([((0, 0), 1), ((1, 1), 1)]) == ()


class TestCompositeGlyphs:
    """A composite glyph that refers to itself is refused, not followed"""

    def test_a_glyph_that_includes_itself_is_refused(self):
        font = built_open({'a': 500})
        entry = font['glyf']['glyph0061']
        entry.expand(font['glyf'])
        component = GlyphComponent()
        component.glyphName = 'glyph0061'
        component.x = component.y = 0
        component.flags = 0
        entry.components = [component]
        entry.numberOfContours = -1

        shape = glyph.Glyph('glyph0061')
        try:
            shape.compile(font)
        except FontError as err:
            assert 'includes itself' in str(err), err
        else:
            raise AssertionError('a self-referencing composite was followed')
