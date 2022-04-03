#!/usr/bin/env python3

import argparse
import json
import sys
from xml import sax

import http_sfv

from .validate import RfcHttpValidator

__version__ = "0.2.0"


class ValidatorCLI:
    def __init__(self):
        self.args = self.parse_args()
        self.typemap = self.load_typemap()
        self.run()

    def run(self):
        errors = 0
        for fh in self.args.file:
            handler = RfcHttpValidator(self.typemap, self.status)
            handler.filename = fh.name
            sax.parse(fh, handler)
            errors += handler.errors
        if errors > 0:
            sys.exit(1)

    def status(self, *args):
        if not self.args.quiet:
            print(*args)

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="Validate HTTP messages in XML2RFC documents"
        )
        parser.add_argument(
            "-m",
            "--map",
            dest="map",
            type=argparse.FileType("r"),
            help="JSON file that maps field names to structured types",
        )
        parser.add_argument(
            "-i",
            "--item",
            dest="item",
            action="append",
            default=[],
            help="field name to consider as a Structured Item",
        )
        parser.add_argument(
            "-l",
            "--list",
            dest="list",
            action="append",
            default=[],
            help="field name to consider as a Structured List",
        )
        parser.add_argument(
            "-d",
            "--dict",
            dest="dict",
            action="append",
            default=[],
            help="field name to consider as a Structured Dictionary",
        )
        parser.add_argument(
            "-q",
            "--quiet",
            dest="quiet",
            action="store_true",
            help="suppress status messages",
        )
        parser.add_argument(
            "file",
            type=argparse.FileType("r"),
            nargs="+",
            help="an XML file to validate",
        )
        return parser.parse_args()

    def load_typemap(self):
        typemap = {}
        if self.args.map:
            try:
                rawmap = json.load(self.args.map)
            except (IOError, ValueError) as why:
                sys.stderr.write(f"ERROR loading JSON: {why}\n")
                sys.exit(1)
            try:
                typemap.update(
                    {
                        k.lower(): {
                            "item": http_sfv.Item,
                            "list": http_sfv.List,
                            "dict": http_sfv.Dictionary,
                        }[v]
                        for (k, v) in rawmap.items()
                    }
                )
            except KeyError as why:
                sys.stderr.write(f"ERROR loading JSON value: {why}\n")
                sys.exit(1)
        for item in self.args.item:
            typemap[item.lower()] = http_sfv.Item
        for _list in self.args.list:
            typemap[_list.lower()] = http_sfv.List
        for _dict in self.args.dict:
            typemap[_dict.lower()] = http_sfv.Dictionary
        return typemap


def main():
    ValidatorCLI()

if __name__ == "__main__":
    main()
