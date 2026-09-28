"""Representation of a single glyph including contour extraction"""
from ttfquery import glyphquery
from ttfquery.errors import FontError
import numpy

#: The point flags a TrueType outline carries that bear on its shape. Bit 0
#: says the point is on the curve; bit 7 says an off-curve point is the control
#: point of a cubic rather than a quadratic segment. The other bits fontTools
#: hands on -- 0x40, that the glyph's contours may overlap -- say nothing about
#: where the point is, so a flag is read a bit at a time rather than compared
#: to 1.
FLAG_ON_CURVE = 0x01
FLAG_CUBIC = 0x80

class Glyph( object):
    """Object encapsulating metadata regarding a particular glyph"""
    def __init__(self, glyphName ):
        """Initialize the glyph object

        glyphName -- font's glyphName for this glyph, see
            glyphquery.glyphName() for extracting the
            appropriate name from character and encoding.
        """
        self.glyphName = glyphName
    def compile( self, font, steps = 3 ):
        """Compile the glyph to a set of poly-line outlines

        Fills in, all in the font's own units:

        contours -- the glyph's contours as the font holds them, each a list of
            ((x, y), flag) points
        outlines -- one poly-line per contour, with `steps` line segments
            standing in for each quadratic curve
        width -- the advance width, how far the pen moves before the next glyph
            is drawn.  0 for a glyph that draws over the one before it.
        height -- the font's base-line to base-line height

        Raises :class:`ttfquery.errors.FontError` where the font's outlines
        cannot be read: a glyph name it has no entry for, a composite glyph that
        includes itself, cubic control points, or a contour whose flags
        contradict the format.
        """
        self.contours = self.calculateContours( font )
        self.outlines = [
            decomposeOutline(contour,steps)
            for contour in self.contours
        ]
        self.width = glyphquery.width( font, self.glyphName )
        self.height = glyphquery.lineHeight( font )

    def calculateContours( self, font ):
        """Given a character, determine contours to draw

        returns a list of contours, with each contour
        being a list of ((x,y),flag) elements.  There may
        be only a single contour.
        """
        glyf = glyphquery.fontTable( font, 'glyf' )
        charglyf = self._glyphEntry( glyf, self.glyphName )
        return self._calculateContours(
            charglyf, glyf, font, ( self.glyphName, )
        )
    def _glyphEntry( self, glyf, glyphName ):
        """The glyf table's entry for glyphName, or a FontError naming it

        A name the table has no entry for is a font whose tables disagree with
        one another: the character map or a composite glyph points at a glyph
        the outlines do not hold.
        """
        try:
            return glyf[glyphName]
        except KeyError as err:
            raise FontError(
                """Font's glyf table has no outline named %r"""% (glyphName,)
            ) from err
    def _calculateContours( self, charglyf, glyf, font, within=() ):
        """Create expanded contour data-set from TTF charglyph entry

        This is called recursively for composite glyphs.

        charglyph -- glyf table's entry for the target character
        glyf -- the glyf table (used for recursive calls)
        within -- the names of the composites this one is a component of, which
            a font whose composites refer to each other in a circle would
            otherwise walk around forever
        """
        charglyf.expand( font ) # XXX is this extraneous?
        contours = []
        if charglyf.numberOfContours == 0:
            # does not display at all, for instance, space
            pass
        elif charglyf.isComposite():
            # composed out of other items...
            for component in charglyf.components:
                if component.glyphName in within:
                    raise FontError(
                        """Font's composite glyph %r includes itself, through %s"""% (
                            component.glyphName,
                            ' -> '.join( within ),
                        )
                    )
                subContours = self._calculateContours(
                    self._glyphEntry( glyf, component.glyphName ),
                    glyf,
                    font,
                    within + (component.glyphName,),
                )
                dx,dy = component.getComponentInfo()[1][-2:]
                # XXX we're ignoring the scaling/shearing/etceteras transformation
                # matrix which is given by component.getComponentInfo()[1][:4]
                subContours = [
                    [((x+dx,y+dy),f) for ((x,y),f) in subContour]
                    for subContour in subContours
                ]
                contours.extend(
                    subContours
                )
        else:
            flags = charglyf.flags
            coordinates = charglyf.coordinates
            # We need to convert from the "end point" representation
            # to a distinct contour representation, requires slicing
            # each contour out of the list and then closing it
            last = 0
            for e in charglyf.endPtsOfContours:
                set = zip(
                    list(coordinates[last:e+1])+list(coordinates[last:last+1]),
                    list(flags[last:e+1])+list(flags[last:last+1])
                )
                contours.append( list(set) )
                last = e+1
            if coordinates[last:]:
                contours.append( list(zip(
                    list(coordinates[last:])+list(coordinates[last:last+1]),
                    list(flags[last:])+list(flags[last:])
                ) ))
        return contours

def decomposeOutline( contour, steps=3 ):
    """Decompose a single TrueType contour to a line-loop

    In essence, this is the "interpretation" of the font
    as geometric primitives.  I only support line and
    quadratic (conic) segments, which should support most
    TrueType fonts as far as I know.

    The process consists of first scanning for any multi-
    off-curve control-point runs.  For each pair of such
    control points, we insert a new on-curve control point.

    Once we have the "expanded" control point array we
    scan through looking for each segment which includes
    an off-curve control point.  These should only be
    bracketed by on-curve control points.  For each
    found segment, we call our integrateQuadratic method
    to produce a set of points interpolating between the
    end points as affected by the middle control point.

    All other control points merely generate a single
    line-segment between the endpoints.
    """
    # contours must be closed, but they can start with
    # (and even end with) items not on the contour...
    # so if we do, we need to create a new point to serve
    # as the midway...
    if len(contour)<3:
        return ()
    if any( record[-1] & FLAG_CUBIC for record in contour ):
        raise FontError(
            """Outline has cubic control points, which only quadratic segments are read here"""
        )
    set = contour[:]
    def on( record ):
        """Is this record on the contour?

        record = ((Ax,Ay),Af)
        """
        return bool( record[-1] & FLAG_ON_CURVE )

    def merge( first, second):
        """Merge two off-point records into an on-point record"""
        ((Ax,Ay),Af) = first
        ((Bx,By),Bf) = second
        return (((Ax+Bx)/2.0),((Ay+By))/2.0),1
    # create an expanded set so that all adjacent
    # off-curve items have an on-curve item added
    # in between them
    last = contour[-1]
    expanded = []
    for item in set:
        if (not on(item)) and (not on(last)):
            expanded.append( merge(last, item))
        expanded.append( item )
        last = item
    result = []
    while expanded:
        # The expansion above puts an on-curve point between every pair of
        # off-curve ones, so each step starts on the curve and reads either
        # [on, on] or [on, off, on].  A contour that does not is one whose
        # flags the font holds wrongly, not a case to interpret.
        if not on(expanded[0]):
            raise FontError(
                """Outline point %r is off-curve where the contour must start on it"""% (
                    expanded[0],
                )
            )
        if len(expanded)>1:
            if on(expanded[1]):
                # line segment from 0 to 1
                result.append( expanded[0][0] )
                #result.append( expanded[1][0] )
                del expanded[:1]
            else:
                if len(expanded) == 2:                          #KH
                    result.append( expanded[1][0] )         #KH
                    del expanded[:1]
                    break
                if not on(expanded[2]):
                    raise FontError(
                        """Outline has the off-curve points %r and %r in a row after expansion"""% (
                            expanded[1], expanded[2],
                        )
                    )
                points = integrateQuadratic( expanded[:3], steps = steps )
                result.extend( points )
                del expanded[:2]
        else:
            result.append( expanded[0][0] )
            del expanded[:1]
    result.append( result[-1] )
    return result
def integrateQuadratic( points, steps=3 ):
    """Get points on curve for quadratic w/ end points A and C

    Basis Equations are taken from here:
        http://www.truetype.demon.co.uk/ttoutln.htm

    This is a very crude approach to the integration,
    everything is coded directly in Python, with no
    attempts to speed up the process.

    XXX Should eventually provide adaptive steps so that
        the angle between the elements can determine how
        many steps are used.
    """
    step = 1.0/steps
    ((Ax,Ay),_),((Bx,By),_),((Cx,Cy),_) = points
    result = [(Ax,Ay)]
    ### XXX This is dangerous, in certain cases floating point error
    ## can wind up creating a new point at 1.0-(some tiny number) if step
    ## is sliaghtly less than precisely 1.0/steps
    for t in numpy.arange( step, 1.0, step ):
        invT = 1.0-t
        px = (invT*invT * Ax) + (2*t*invT*Bx) + (t*t*Cx)
        py = (invT*invT * Ay) + (2*t*invT*By) + (t*t*Cy)
        result.append( (px,py) )
    # the end-point will be added by the next segment...
    #result.append( (Cx,Cy) )
    return result
