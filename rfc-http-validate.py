#!/usr/bin/env python3

import argparse
import json
import sys
from xml import sax

import http_sfv

REGISTERED_METHODS = [
    "ACL",
    "BASELINE-CONTROL",
    "BIND",
    "CHECKIN",
    "CHECKOUT",
    "CONNECT",
    "COPY",
    "DELETE",
    "GET",
    "HEAD",
    "LABEL",
    "LINK",
    "LOCK",
    "MERGE",
    "MKACTIVITY",
    "MKCALENDAR",
    "MKREDIRECTREF",
    "MKWORKSPACE",
    "MOVE",
    "OPTIONS",
    "ORDERPATCH",
    "PATCH",
    "POST",
    "PRI",
    "PROPFIND",
    "PUT",
    "QUERY",
    "REBIND",
    "REPORT",
    "SEARCH",
    "TRACE",
    "UNBIND",
    "UNCHECKOUT",
    "UNLINK",
    "UNLOCK",
    "UPDATE",
    "UPDATEREDIRECTREF",
    "VERSION-CONTROL",
]

verbose = True


def status(*args):
    global verbose
    if verbose:
        print(*args)


def validate(filehandles, typemap):
    errors = 0
    for fh in filehandles:
        handler = RfcHttpValidator(typemap)
        handler.filename = fh.name
        sax.parse(fh, handler)
        errors += handler.errors
    if errors > 0:
        sys.exit(1)


class RfcHttpValidator(sax.ContentHandler):
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
            self.listening = False
            if self.type in ["http-message"]:
                lines = self.content.strip("\n").split("\n")
                if len(lines) == 0:
                    self.validationError("Empty http-message")
                    return
                lines = self.combine_8792(lines)
                lines = self.check_start_line(lines)
                try:
                    headers = self.combine_headers(lines)
                except ValueError as why:
                    self.validationError(why)
                    return
                for hname, hvalue in headers.items():
                    header_type = self.typemap.get(hname)
                    if header_type:
                        try:
                            self.validationStatus(
                                f"validating field value {hname}: {hvalue}"
                            )
                            header_type().parse(hvalue.encode("ascii"))
                        except ValueError as why:
                            self.validationError(why)
                    else:
                        self.validationStatus(
                            f"skipping field value {hname} (no type information)"
                        )
            else:
                self.validationStatus(f"skipping section {self.type}")
        self.content = ""

    def characters(self, content):
        if self.listening:
            self.content += content

    def startDocument(self):
        status(f"* Validating {self.filename}")

    def endDocument(self):
        status(f"* {self.errors} errors.")
        status()

    def validationStatus(self, message):
        status(f"  {message}")

    def validationError(self, message):
        print(f"  ERROR at {self.location()}: {message}")
        self.errors += 1

    def location(self):
        return f"{self.filename}:{self._locator.getLineNumber()}"

    def check_start_line(self, lines):
        start_line = lines[0]
        if start_line[0] == " ":
            self.validationError(f"Start line starts with whitespace: '{start_line}'")
            return lines
        parts = start_line.split(" ")
        if parts[0][-1] == ":":
            return lines  # it must be a header line
        if "http" in parts[0].lower():
            self.validationStatus(
                f"{self.location()}: validating status line {start_line}"
            )
            if parts[0] != "HTTP/1.1":
                self.validationError(
                    f"Status line '{start_line}' doesn't start with 'HTTP/1.1'"
                )
            elif len(parts) < 3:
                self.validationError(
                    f"Status line '{start_line}' isn't 'HTTP/1.1 [status_code] [status_phrase]'"
                )
            else:
                if not parts[1].isdigit():
                    self.validationError(f"Status code {parts[1]} is non-numeric")
                elif not 99 < int(parts[1]) < 600:
                    self.validationError(f"Status code {parts[1]} is out of range")
        else:
            self.validationStatus(
                f"{self.location()}: validating request line {start_line}"
            )
            if len(parts) < 3:
                self.validationError("Request line isn't '[method] [url] HTTP/1.1'")
            else:
                if parts[0] not in REGISTERED_METHODS:
                    self.validationError(f"Method '{parts[0]}' not recognised")
                if parts[2] != "HTTP/1.1":
                    self.validationError(
                        f"Request line '{start_line}' doesn't end with 'HTTP/1.1'"
                    )
                if len(parts) > 3:
                    self.validationError(f"Request line '{start_line}' has extra text")
        lines.pop(0)
        return lines

    def combine_8792(self, lines):
        if not "NOTE: '\\' line wrapping per RFC 8792" in lines[0]:
            return lines
        else:
            lines = lines[2:]
        output = []
        continuation = False
        for line in lines:
            prev_continuation = continuation
            if line.endswith("\\"):
                continuation = True
                line = line[:-1]
            else:
                continuation = False
            if prev_continuation:
                output[-1] += line.lstrip()
            else:
                output.append(line)
        return output

    def combine_headers(self, lines):
        headers = {}
        prev_name = None
        in_body = False
        for line in lines:
            if len(line.strip()) == 0:
                if not headers:  # a blank line before seeing any headers
                    raise ValueError(f"Body without headers")
                in_body = True
                self.validationStatus(f"ignoring HTTP message body")
            if in_body:
                continue
            if line[0] == " ":
                if prev_name:
                    headers[prev_name] += f" {line.strip()}"
                    continue
                raise ValueError(
                    f"First header field line '{line}' starts with whitespace"
                )
            try:
                name, value = line.split(":", 1)
            except ValueError:
                raise ValueError(f"Non-field line '{line}' in content")
            if name != name.rstrip():
                self.validationError(
                    f"Whitespace between field name {name.strip()} and colon"
                )
            name = name.lower()
            value = value.strip()
            if name in headers:
                headers[name] += f", {value}"
            else:
                headers[name] = value
            prev_name = name
        return headers


def main():
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
        "-q", "--quiet", action="store_true", help="suppress status messages",
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
    if args.quiet:
        global verbose
        verbose = False

    validate(args.file, typemap)


if __name__ == "__main__":
    main()
