#!/usr/bin/env python3

import sys
from xml import sax

import http_sfv

__version__ = "0.0.1"

typeMap = {
    "http-sf-item": http_sfv.Item,
    "http-sf-list": http_sfv.List,
    "http-sf-dict": http_sfv.Dictionary,
    "http-sf-invalid": None,
}

class SfValidator(sax.ContentHandler):
    def __init__(self, *args, **kw):
        sax.ContentHandler.__init__(self, *args, **kw)
        self.listening = False
        self.content = ""
        self.type = None
        self.errors = 0

    def startElement(self, name, attrs):
        if name == "sourcecode" and "type" in attrs.keys():
            self.listening = True
            self.type = attrs["type"]

    def endElement(self, name):
        if self.listening:
            header_type = typeMap.get(self.type)
            if header_type:
                for line in self.content.split("\n"):
                    line = line.strip().encode("ascii")
                    if b":" in line:
                        name, value = line.split(b":", 1)
                        try:
                            print(f"Validating {line.decode('ascii')}")
                            header_type().parse(value)
                        except ValueError as why:
                            print(f"* ERROR - {why}")
                            self.errors += 1
            else:
                print(f"Skipping {self.type}")
            self.listening = False
            self.content = ""

    def characters(self, content):
        if self.listening:
            self.content += content

    def endDocument(self):
        print(f"* {self.errors} errors.")
        if self.errors:
            sys.exit(1)


if __name__ == "__main__":
    handler = SfValidator()
    sax.parse(sys.argv[1], handler)
