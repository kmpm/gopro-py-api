import unittest
import json
from os import path

from goprocam.schema import SchemaParser, schema_compare

THIS_FOLDER = path.dirname(path.realpath(__file__))
DOC_FOLDER = path.join(THIS_FOLDER, '..', 'doc')


def open_file(filename):
    with open(filename) as f:
        data = json.load(f)
    return data


class TestSchema(unittest.TestCase):

    def test_hd4(self):
        data = open_file(path.join(DOC_FOLDER, 'HD4_02_05_00_00.json'))
        p = SchemaParser.parse(data)
        self.assertEqual(p.schema_version, 2)
        self.assertEqual(p.version, 4.0)
        self.assertIsInstance(p.version, float)
        self.assertIsInstance(p.schema_version, int)
        self.assertEqual(len(p.commands.keys()), 64)
        self.assertEqual(len(p.modes.keys()), 6)

    def test_hd7(self):
        data = open_file(path.join(DOC_FOLDER, 'HD7_01_01_51_00.json'))
        p = SchemaParser.parse(data)
        self.assertEqual(p.schema_version, 4, 'expected schema_version=4')
        self.assertEqual(p.version, 2.0, 'expected version=2.0')
        self.assertIsInstance(p.version, float)
        self.assertIsInstance(p.schema_version, int)
        self.assertEqual(len(p.commands.keys()), 88)
        self.assertEqual(len(p.modes.keys()), 7)

    def test_hd4_hd7_comparison(self):
        hd7 = SchemaParser.parse(open_file(path.join(DOC_FOLDER, 'HD7_01_01_51_00.json')))
        hd4 = SchemaParser.parse(open_file(path.join(DOC_FOLDER, 'HD4_02_05_00_00.json')))
        schema_compare(hd4, hd7, 'HD4', 'HD7')


if __name__ == '__main__':
    unittest.main()
