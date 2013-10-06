#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pynab
----------------------------------

Tests for `pynab` module.
"""

import unittest
import pprint

from pynab.server import Server
from pynab.db import db
import pynab.binaries
import pynab.releases
import pynab.parts
import pynab.categories


class TestPynab(unittest.TestCase):
    def setUp(self):
        self.server = None

    def test_connect(self):
        self.server = Server()
        self.server.connect()
        self.assertTrue(self.server)

    def test_capabilities(self):
        self.test_connect()
        print(self.server.connection.getcapabilities())

    def test_fetch_headers(self):
        self.test_connect()
        groups = ['alt.binaries.teevee', 'alt.binaries.e-book', 'alt.binaries.moovee']
        for group in groups:
            (_, _, first, last, _) = self.server.connection.group(group)
            for x in range(0, 250000, 20000):
                y = x + 20000 - 1
                parts = self.server.scan(group, last - y, last - x)
                pynab.parts.save_all(parts)

    def test_process_binaries(self):
        pynab.binaries.process()

    def test_process_releases(self):
        pynab.releases.process()

    def test_all(self):
        self.test_fetch_headers()
        self.test_process_binaries()
        self.test_process_releases()

    def test_print_binaries(self):
        pprint.pprint([b for b in db.binaries.find()])

    def test_category(self):
        releases = db.releases.find()
        for release in releases:
            group_name = db.groups.find_one({'_id': release['group_id']})['name']
            pynab.categories.determine_category(release['name'], group_name)

    def tearDown(self):
        try:
            self.server.connection.quit()
        except:
            pass


if __name__ == '__main__':
    unittest.main()