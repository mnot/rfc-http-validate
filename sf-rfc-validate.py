#!/usr/bin/env python3

import sys
from xml import sax

import http_sfv

__version__ = "0.0.5"

typeMap = {
    "http-sf-item": http_sfv.Item,
    "http-sf-list": http_sfv.List,
    "http-sf-dict": http_sfv.Dictionary,
    "http-sf-invalid": None,
}


def validate(filenames):
    errors = 0
    for filename in filenames:
        print(f"* Validating {filename}")
        handler = SfValidator()
        sax.parse(filename, handler)
        errors += handler.errors
        print()
    if errors > 0:
        sys.exit(1)


class SfValidator(sax.ContentHandler):
    def __init__(self, *args, **kw):
        sax.ContentHandler.__init__(self, *args, **kw)
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
            header_type = typeMap.get(self.type)
            if header_type:
                headers = combine_headers(self.content)
                for hname, hvalue in headers.items():
                    try:
                        print(f"  checking {hname}: {hvalue}")
                        header_type().parse(hvalue.encode("ascii"))
                    except ValueError as why:
                        print(f"* ERROR - {why}")
                        self.errors += 1
            else:
                print(f"  skipping {self.type}")
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
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            name, value = line.split(":", 1)
            name = name.lower()
            if name in headers:
                headers[name] += f", {value}"
            else:
                headers[name] = value
            prev_name = name
        elif prev_name:
            headers[prev_name] += f", {line}"
    return headers


if __name__ == "__main__":
    validate(sys.argv[1:])
