from __future__ import print_function
from ttfquery import ttffiles, ttfgroups, ttfmetadata, ttffamily
import pytest
import os, sys, glob, unittest, tempfile, shutil

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp(prefix='ttfquery-',suffix='-tests')
        self.registry = os.path.join(self.workdir,'fonts.cache')
        class fakeoptions:
            directories = []
            registry = self.registry
        self.options = fakeoptions
        self.registry = ttffiles.registry_for_options(self.options)
    def tearDown(self):
        shutil.rmtree(self.workdir)
    def test_registry_setup(self):
        registry = self.registry
        assert registry.fonts, "No fonts loaded"
        assert registry.families, "No families extracted"
        assert registry.specificFonts, "No final/specific font classes registered"
        assert registry.files, "No files registered/added"
        assert registry.shortFiles, "No short filenames registered"
        assert not registry.DIRTY, "Registry was just saved, should be clean"

        font = None
        for name in ('Arial','Helvetica','SANS'):
            try:
                font = registry.matchName(name)
            except KeyError:
                pass
            if font:
                break 
        if not font:
            raise RuntimeError("Unable to find any of Arial/Helvetica/SANS")
        
    def test_ttfgroups(self):
        registry = self.registry
        table = ttfgroups.buildTable(registry)
        ttfgroups.run_report(table)

        parser = ttfgroups.get_options()
        assert 'font-groups' in parser.description, parser.description

    def test_ttfmetadata(self):
        registry = self.registry
        for name in registry.fonts.keys():
            ttfmetadata.find_match(name,registry)

        parser = ttfmetadata.get_options()
        assert 'Query/search' in parser.description, parser.description

    def test_ttffamily(self):
        registry = self.registry
        for family,subfams in registry.families.items():
            ttffamily.search(registry,family)
            for subfam in subfams.keys():
                ttffamily.search(registry,family,subfam)
        