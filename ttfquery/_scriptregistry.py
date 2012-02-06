from ttfquery import ttffiles
import os, sys

### more robust registry-file location by John Hunter...
if os.environ.has_key('HOME'):
    registryFile = os.path.join( os.environ['HOME'], ".font.cache")
else:
	# OpenGLContext uses the Application Data directory for win32,
	# should consider porting that code here...
	registryFile = os.path.join( os.path.split(__file__)[0], "font.cache")

# make sure we can write to the registryFile
if not os.path.exists(registryFile):
    try: fh = file(registryFile, 'w')
    except IOError:
        print >>sys.stderr, 'Could not open registry file %r for writing' % registryFile
        raise
    else:
        fh.close()
        os.remove(registryFile)

def _getRegistry():
	if os.path.isfile( registryFile ):
		registry = ttffiles.load( registryFile )
	else:
		registry = ttffiles.Registry()
		sys.stderr.write( """Scanning for system fonts...\n""" )
		new,failed = registry.scan( printErrors = 1, force = 0)
		sys.stderr.write( """Scan complete. Saving to %r\n"""%(registryFile,) )
		registry.save(registryFile)
	return registry
registry = _getRegistry()
