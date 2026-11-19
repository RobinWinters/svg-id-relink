from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import svg_id_relink as cli

FIX = Path(__file__).parent / 'fixtures'


class SvgTests(unittest.TestCase):
    def rewrite(self, name):
        return cli.rewrite((FIX / name).read_bytes())

    def test_duplicates_unique(self):
        data, report = self.rewrite('duplicate.svg')
        root = ET.fromstring(data)
        ids = [e.get('id') for e in root.iter() if e.get('id')]
        self.assertEqual(ids, ['relink-1', 'relink-2', 'relink-3'])
        self.assertIn('2,paint,relink-2', report)
        self.assertEqual(root.find('{*}rect').get('fill'), 'url(#relink-1)')

    def test_url_and_href(self):
        data, _ = self.rewrite('references.svg')
        root = ET.fromstring(data)
        self.assertEqual(root.find('{*}g').get('clip-path'), "url('#relink-1')")
        self.assertEqual(root.find('{*}use').get('href'), '#relink-2')

    def test_adversarial_preserved(self):
        data, _ = self.rewrite('adversarial.svg')
        self.assertIn(b'<!-- id="paint" url(#paint) href="#paint" -->', data)
        root = ET.fromstring(data)
        self.assertEqual(root.find('{*}text').text, 'id="paint" url(#paint) href="#paint"')
        self.assertEqual(root.find('{*}rect').get('data-note'), 'url(#paint)')
        self.assertEqual(root.find('{*}rect').get('fill'), 'url(#relink-1)')

    def test_clean(self):
        _, report = self.rewrite('clean.svg')
        self.assertEqual(report, 'occurrence,before,after\n')

    def test_unknown_reference_not_captured(self):
        data, _ = self.rewrite('unknown.svg')
        root = ET.fromstring(data)
        self.assertEqual(root.find('{*}rect').get('id'), 'relink-2')
        self.assertEqual(root.find('{*}use').get('href'), '#relink-1')

    def test_output_and_input_unchanged(self):
        source = FIX / 'duplicate.svg'
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            output, mapping = Path(tmp) / 'result.svg', Path(tmp) / 'map.csv'
            cli.write_new(source, output, mapping)
            self.assertEqual(source.read_bytes(), before)
            self.assertIn('relink-1', output.read_text())
            self.assertIn('before,after', mapping.read_text())

    def test_same_path_rejected(self):
        source = FIX / 'clean.svg'
        with self.assertRaises(ValueError):
            cli.write_new(source, source, 'unused.csv')

    def test_existing_hardlink_rejected(self):
        source = FIX / 'clean.svg'
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'alias.svg'
            output.hardlink_to(source)
            with self.assertRaises(ValueError):
                cli.write_new(source, output, Path(tmp) / 'map.csv')

    def test_symlink_output_rejected(self):
        source = (FIX / 'clean.svg').resolve()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'alias.svg'
            output.symlink_to(source)
            with self.assertRaises(ValueError):
                cli.write_new(source, output, Path(tmp) / 'map.csv')

    def test_output_map_alias_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'output.svg'
            with self.assertRaises(ValueError):
                cli.write_new(FIX / 'clean.svg', output, output)
            self.assertFalse(output.exists())

    def test_invalid_cli_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, cli.__file__, str(FIX / 'missing.svg'), '--output', tmp + '/out.svg', '--map', tmp + '/map.csv'], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((Path(tmp) / 'out.svg').exists())

    def test_invalid_xml_rejected(self):
        with self.assertRaises(ET.ParseError):
            cli.rewrite(b'<svg>')

    def test_unsupported_stylesheet_rejected(self):
        with self.assertRaises(ValueError):
            cli.rewrite(b'<svg><style>#x { fill: blue; }</style></svg>')

    def test_deterministic(self):
        self.assertEqual(self.rewrite('duplicate.svg'), self.rewrite('duplicate.svg'))

    def test_help(self):
        result = subprocess.run([sys.executable, cli.__file__, '--help'], capture_output=True)
        self.assertEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
