#!/usr/bin/env python3
"""Check that Renovate can match all dependencies in library descriptors.

Errors in this check mean regex matchers in renovate.json should be
adjusted to match the missing libraries.
"""

import argparse
import json
from pathlib import Path
import re
import sys


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('log',
                    type=Path,
                    help='Path of Renovate debug log that should be checked')
parser.add_argument('--descriptors-dir',
                    type=Path,
                    default=Path('.'),
                    help='Directory containing kernel library descriptors. \
                          Defaults to current dir.')


def main(argv=None):
    args = parser.parse_args(argv)
    print("Parsing dependencies of library descriptors...", file=sys.stderr)
    packages = parse_descriptor_dependencies(args.descriptors_dir)
    print(f"Checking packages matched by Renovate in '{args.log}'...", file=sys.stderr)
    unmatched = get_packages_not_in_log(packages, args.log)
    if unmatched:
        print("Unmatched packages:", file=sys.stderr)
        print('\n'.join(unmatched))
        exit(1)
    else:
        print("All packages were matched")


def parse_descriptor_dependencies(descriptors_dir: Path):
    packages = set()
    for path, descriptor in get_library_descriptors(descriptors_dir):
        for dependency in extract_dependencies(descriptor):
            package = dependency_to_package_name(dependency)
            packages.add(package)
            print(f"[{path}] {package}", file=sys.stderr)
    return packages


def get_library_descriptors(dir: Path):
    """Get library descriptors in JSON format"""
    for path in dir.glob('*.json'):
        yield path, json.loads(path.read_text())


def extract_dependencies(descriptor: dict):
    """Parse dependencies required by a library descriptor"""
    if 'dependencies' not in descriptor:
        return
    for dep in descriptor['dependencies']:
        if 'properties' in descriptor:
            yield interpolate(dep, descriptor['properties'])
        else:
            yield dep


def interpolate(dep: str, properties: dict):
    """
    Interpolate a string if it contains variables from the properties object,
    e.g. 'my:lib:$myLibVersion'
    """
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


def dependency_to_package_name(dep: str) -> str:
    """group:artifact:version -> group:artifact"""
    parts = dep.split(':')
    return ':'.join(parts[0:2])


def get_packages_not_in_log(packages: list[str], log: Path):
    """Get a list of dependencies that don't appear in the Renovate debug log"""
    missing = packages
    for line in log.read_text().splitlines():
        line_matches = set(p for p in missing if p in line)
        for package in line_matches:
            missing.remove(package)
    return missing


if __name__ == '__main__':
    main()
