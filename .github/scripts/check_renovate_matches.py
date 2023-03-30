#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path
import re
import sys


def get_library_descriptors(dir):
    for p in os.listdir(dir):
        if p.endswith('.json'):
            yield json.loads(Path(dir/p).read_text())


def extract_dependencies(descriptor):
    if 'dependencies' not in descriptor:
        return
    for dep in descriptor['dependencies']:
        if 'properties' in descriptor:
            yield interpolate(dep, descriptor['properties'])
        else:
            yield dep


def interpolate(dep, properties):
    for var in re.findall(r'\$[a-zA-Z0-9]+', dep):
        key = var[1:]
        if isinstance(properties, list):
            for prop_obj in properties:
                if prop_obj['name'] == key:
                    value = prop_obj['value']
                    break
        elif key in properties:
            value = properties[key]
        if not value:
            raise RuntimeError(
                f"Error interpolating {var} in {dep} with props {properties}")
        dep = dep.replace(var, value)
    return dep


def get_packages_not_in_log(dependencies, log):
    missing_deps = dependencies
    for line in log.readlines():
        line_matches = set(dep for dep in missing_deps if dep in line)
        for dep in line_matches:
            missing_deps.remove(dep)
    return missing_deps


def main(descriptors_dir, renovate_debug_log):
    packages = set()
    for descriptor in get_library_descriptors(descriptors_dir):
        for dependency in extract_dependencies(descriptor):
            parts = dependency.split(':')
            package = ':'.join(parts[0:2])
            packages.add(package)
    unmatched = get_packages_not_in_log(packages, renovate_debug_log)
    if unmatched:
        print(*unmatched, sep='\n', file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log',
                        type=argparse.FileType('r'),
                        help='Path of Renovate debug log that should be checked')
    args = parser.parse_args()
    main(descriptors_dir=Path('.'), renovate_debug_log=args.log)
