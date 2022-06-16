import argparse
import json
import sys
from typing import Callable, Dict

from blessings import Terminal  # type: ignore[import]
import http_sfv

from .retrofit import typemap as base_typemap
from .validate import RfcHttpValidator, ValidatorUi
from .markdown import extract_md
from .xml import extract_xml

term = Terminal()


class ValidatorCLI(ValidatorUi):
    def __init__(self) -> None:
        self.args = self.parse_args()
        self.typemap = self.load_typemap()
        self.errors = 0
        self.run()

    def run(self) -> None:
        validator = RfcHttpValidator(self.typemap, self)
        for fh in self.args.file:
            if fh.name.endswith(".xml"):
                extract_xml(fh, validator)
            elif fh.name.endswith(".md"):
                extract_md(fh, validator)
            else:
                self.fatal_error(f"Can't determine format of {fh.name}")
        if self.errors > 0:
            sys.exit(1)

    def status(self, message: str) -> None:
        if not self.args.quiet:
            print(message)

    def success(self, subject: str, message: str) -> None:
        if not self.args.quiet:
            print(f"{subject} -- {term.green}{message}{term.normal}")

    def error(self, subject: str, message: str) -> None:
        self.errors += 1
        print(f"{subject}: {term.red}{message}{term.normal}")

    def skip(self, subject: str, message: str) -> None:
        if not self.args.quiet:
            print(f"{subject}: {term.yellow}{message}{term.normal}")

    def parse_args(self) -> argparse.Namespace:
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
            help="only output errors",
        )
        parser.add_argument(
            "file",
            type=argparse.FileType("r"),
            nargs="+",
            help="an XML file to validate",
        )
        return parser.parse_args()

    def load_typemap(self) -> Dict[str, Callable]:
        typemap = self.process_typemap(base_typemap)
        if self.args.map:
            try:
                jsonmap = json.load(self.args.map)
            except (IOError, ValueError) as why:
                self.fatal_error(f"Cannot load JSON: {why}")
            typemap.update(self.process_typemap(jsonmap))

        for item in self.args.item:
            typemap[item.lower()] = http_sfv.Item
        for _list in self.args.list:
            typemap[_list.lower()] = http_sfv.List
        for _dict in self.args.dict:
            typemap[_dict.lower()] = http_sfv.Dictionary
        return typemap

    def process_typemap(self, typemap: Dict[str, str]) -> Dict[str, Callable]:
        try:
            return {
                k.lower(): {
                    "item": http_sfv.Item,
                    "list": http_sfv.List,
                    "dict": http_sfv.Dictionary,
                }[v]
                for (k, v) in typemap.items()
            }
        except KeyError as why:
            self.fatal_error(f"Cannot load field type mapping: {why}")
            raise

    def fatal_error(self, message: str) -> None:
        sys.stderr.write(f"{term.red}FATAL ERROR:{term.normal} {message}\n")
        sys.exit(1)
