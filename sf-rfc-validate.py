#!/usr/bin/env python3

import argparse
import json
import sys
from xml import sax

import http_sfv


def validate(filehandles, typemap):
    errors = 0
    for fh in filehandles:
        print(f"* Validating {fh.name}")
        handler = SfValidator(typemap)
        sax.parse(fh, handler)
        errors += handler.errors
        print()
    if errors > 0:
        sys.exit(1)


class SfValidator(sax.ContentHandler):
    def __init__(self, typemap):
        sax.ContentHandler.__init__(self)
        self.typemap = typemap
        self.listening = False
        self.content = ""
        self.type = None
        self.errors = 0

    def startElement(self, name, attrs):
        if name in ["sourcecode", "artwork"] and "type" in attrs.keys():
            self.listening = True
            self.type = attrs["type"]

    def endElement(self, name):
        if self.listening:
            if self.type in ["http-structured-fields"]:
                try:
                    headers = combine_headers(self.content)
                except ValueError as why:
                    print(f"  ERROR - {why}")
                    self.errors += 1
                    return
                for hname, hvalue in headers.items():
                    header_type = self.typemap.get(hname)
                    if header_type:
                        try:
                            print(f"  validating {hname}: {hvalue}")
                            header_type().parse(hvalue.encode("ascii"))
                        except ValueError as why:
                            print(f"  ERROR - {why}")
                            self.errors += 1
                    else:
                        print(f"  skipping {hname} field (no type information)")
            else:
                print(f"  skipping {self.type} section")
            self.listening = False
            self.content = ""

    def characters(self, content):
        if self.listening:
            self.content += content

    def endDocument(self):
        print(f"* {self.errors} errors.")


def combine_headers(content):
    headers = {}
    prev_name = None
    for line in content.split("\n"):
        if not line:
            continue
        if line[0] == " ":
            if prev_name:
                headers[prev_name] += f" {line.strip()}"
                continue
            raise ValueError("First line starts with whitespace")
        try:
            name, value = line.split(":", 1)
        except ValueError:
            raise ValueError("Non-field line in content")
        name = name.strip().lower()
        value = value.strip()
        if name in headers:
            headers[name] += f", {value}"
        else:
            headers[name] = value
        prev_name = name
    return headers


def main():
    parser = argparse.ArgumentParser(
        description="Validate HTTP Structured Fields in XML2RFC documents"
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
        "file", type=argparse.FileType("r"), nargs="+", help="an XML file to validate"
    )

    args = parser.parse_args()
    typemap = {}
    if args.map:
        try:
            rawmap = json.load(args.map)
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
    for item in args.item:
        typemap[item.lower()] = http_sfv.Item
    for _list in args.list:
        typemap[_list.lower()] = http_sfv.List
    for _dict in args.dict:
        typemap[_dict.lower()] = http_sfv.Dictionary

    validate(args.file, typemap)


if __name__ == "__main__":
    main()
