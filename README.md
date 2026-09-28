# TTFQuery

FontTools-based package for querying system fonts

TTFQuery builds on the FontTools package to allow the Python programmer to accomplish a number of tasks:

* query the system to find installed fonts
* retrieve metadata about any TTF font file (even those not yet installed)
    * abstract family type
    * proper font name
    * glyph outlines
* build simple metadata registries for run-time font matching, holding the
  fonts text can be laid out with and reporting the files that cannot

With these functionalities, it is possible to readily create OpenGL solid-text
rendering libraries which can accept abstract font-family names as font
specifiers and deliver platform-specific TTF files to match those libraries.

TTFQuery doesn't provide rendering services, but a sample implementation can be
found in the OpenGLContext project, from which TTFQuery was refactored.
