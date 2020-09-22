#!/usr/bin/env python

"""Auto import script from a user directory
"""


import sys
import argparse

from importer_job import auto_import


parser = argparse.ArgumentParser()
parser.add_argument("path", help="path to the directory you want to import into omero")
parser.add_argument(
    "-d",
    "--dry_run",
    help="do not perform the import, just output the preparation files",
    action="store_true",
)

parser.add_argument(
    "-c",
    "--use-cache",
    help="Do not parse the directory again, perform import "
    "from previously generated files",
    action="store_true",
)

args = parser.parse_args()
reset = not parser.use_cache
auto_import(parser.path, parser.dry_run, reset)
