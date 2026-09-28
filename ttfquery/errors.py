"""The errors ttfquery raises about a font file

A font file is data from outside the program: it can be truncated, it can be
missing tables the format requires, and it can hold metrics that no text can be
laid out with. A caller working through the fonts a machine has needs to tell
"this font is no good, take the next one" apart from a defect in its own code,
so every such fault raises one of these rather than whichever `KeyError` or
`AttributeError` the malformed part happened to produce.

Both subclass `ValueError`, so a caller already catching that around a font it
opened keeps catching these.
"""


class FontError(ValueError):
    """A font ttfquery cannot read, and the reason it cannot"""


class UnusableFont(FontError):
    """A font that has no text layout in it, with every reason it has none

    reasons -- what was found in the file, one sentence each
    file_name -- the file they were read from, where the caller named one
    """

    def __init__(self, reasons, file_name=''):
        self.reasons = list(reasons)
        self.file_name = file_name
        super().__init__(
            '%s: %s' % (file_name or 'font', '; '.join(self.reasons))
        )
