#!/usr/bin/env python3
"""Relink static SVG IDs into new explicit output files, never in place."""
import argparse
import csv
import io
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

REFERENCE_ATTRIBUTES = {'fill', 'stroke', 'filter', 'clip-path', 'mask', 'marker', 'marker-start', 'marker-mid', 'marker-end', 'cursor', 'style'}
URL_REF = re.compile(r'''url\(\s*(["']?)#([^\s)'"()]+)\1\s*\)''')
ID_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_.:-]*\Z')


def local(tag):
    return tag.rsplit('}', 1)[-1] if isinstance(tag, str) else ''


def rewrite(data):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper() or b'\x00' in data:
        raise ValueError('DTD, entities and non-UTF-8 XML are outside pinned scope')
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))
    root = ET.fromstring(data, parser=parser)
    if local(root.tag) != 'svg':
        raise ValueError('root element must be svg')
    first = {}
    mapping = []
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        if local(node.tag) in {'style', 'script', 'animate', 'animateMotion', 'animateTransform', 'set'}:
            raise ValueError('stylesheets, scripting and animation are outside pinned scope')
        old = node.get('id')
        if old is not None:
            if not ID_RE.fullmatch(old):
                raise ValueError('ID is outside the pinned ASCII identifier subset')
            new = 'relink-' + str(len(mapping) + 1)
            first.setdefault(old, new)
            mapping.append((len(mapping) + 1, old, new))
            node.set('id', new)
    # Unknown targets must stay unknown: reserve their spellings when allocating IDs.
    references = set()
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        for attr, value in node.attrib.items():
            name = local(attr)
            if name == 'href' and value.startswith('#'):
                references.add(value[1:])
            elif name in REFERENCE_ATTRIBUTES:
                references.update(match.group(2) for match in URL_REF.finditer(value))
            elif name in {'aria-labelledby', 'aria-describedby'}:
                references.update(value.split())
    unknown = references - first.keys()
    if unknown:
        first = {}
        replacement = []
        number = 1
        for ordinal, old, _ in mapping:
            while 'relink-' + str(number) in unknown:
                number += 1
            new = 'relink-' + str(number)
            number += 1
            first.setdefault(old, new)
            replacement.append((ordinal, old, new))
        mapping = replacement
        for node, row in zip((e for e in root.iter() if isinstance(e.tag, str) and e.get('id') is not None), mapping):
            node.set('id', row[2])
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        for attr, value in list(node.attrib.items()):
            name = local(attr)
            if name == 'href' and value.startswith('#'):
                node.set(attr, '#' + first.get(value[1:], value[1:]))
            elif name in REFERENCE_ATTRIBUTES:
                node.set(attr, URL_REF.sub(lambda m: 'url(' + m.group(1) + '#' + first.get(m.group(2), m.group(2)) + m.group(1) + ')', value))
            elif name in {'aria-labelledby', 'aria-describedby'}:
                node.set(attr, ' '.join(first.get(token, token) for token in value.split()))
    output = ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'
    report = io.StringIO(newline='')
    writer = csv.writer(report, lineterminator='\n')
    writer.writerow(('occurrence', 'before', 'after'))
    writer.writerows(mapping)
    return output, report.getvalue()


def write_new(source, output, map_path):
    paths = [Path(source), Path(output), Path(map_path)]
    if len({p.resolve() for p in paths}) != 3:
        raise ValueError('input and both output paths must be distinct')
    for p in paths[1:]:
        if p.exists() or p.is_symlink():
            raise ValueError('output already exists; choose a new path')
    svg, report = rewrite(paths[0].read_bytes())
    created = []
    try:
        for p, data in ((paths[1], svg), (paths[2], report.encode('utf-8'))):
            with p.open('xb') as stream:
                created.append(p)
                stream.write(data)
    except OSError:
        for p in created:
            p.unlink()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('svg', help='local static SVG input')
    parser.add_argument('--output', required=True, help='new rewritten SVG path')
    parser.add_argument('--map', required=True, dest='map_path', help='new CSV map path')
    args = parser.parse_args(argv)
    try:
        write_new(args.svg, args.output, args.map_path)
    except (OSError, ValueError, ET.ParseError) as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
