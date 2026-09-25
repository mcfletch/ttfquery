from __future__ import print_function
from ttfquery import ttffiles, ttfgroups, ttfmetadata, ttffamily
import os
import unittest
import tempfile
import shutil
import logging

import pytest

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp(prefix='ttfquery-',suffix='-tests')
        self.registry = os.path.join(self.workdir,'fonts.cache')
        class fakeoptions:
            directories = ()
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


class TestAFontThatCannotBeRead:
    """`scan` reports a file it cannot read, and carries on."""

    def scan_a_broken_font(self, tmp_path, **named):
        (tmp_path / 'broken.ttf').write_bytes(b'not a font')
        return ttffiles.Registry().scan([str(tmp_path)], **named)

    def test_the_file_is_returned_as_failed(self, tmp_path):
        new, failed = self.scan_a_broken_font(tmp_path)
        assert new == []
        assert failed == [str(tmp_path / 'broken.ttf')]

    def test_the_log_names_the_error(self, tmp_path, caplog):
        caplog.set_level(logging.INFO, logger=ttffiles.log.name)
        self.scan_a_broken_font(tmp_path)
        [record] = caplog.records
        assert record.levelno == logging.INFO
        assert 'broken.ttf' in record.getMessage()
        assert 'Not a TrueType or OpenType font' in record.getMessage()

    def test_print_errors_logs_the_traceback(self, tmp_path, caplog):
        caplog.set_level(logging.INFO, logger=ttffiles.log.name)
        self.scan_a_broken_font(tmp_path, printErrors=1)
        [record] = caplog.records
        assert record.levelno == logging.WARNING
        assert 'broken.ttf' in record.getMessage()
        assert record.exc_info is not None


class TestAByteName:
    """`matchName` reads a byte name as UTF-8, or as Latin-1 where it is not."""

    def test_utf_8(self):
        with pytest.raises(KeyError, match='Café'):
            ttffiles.Registry().matchName('Café'.encode('utf-8'))

    def test_latin_1(self):
        with pytest.raises(KeyError, match='Café'):
            ttffiles.Registry().matchName('Café'.encode('latin-1'))
