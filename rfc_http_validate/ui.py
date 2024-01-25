import argparse
import json
import sys
from typing import Dict

from blessings import Terminal  # type: ignore

from rfc_http_validate.validate import RfcHttpValidator, ValidatorUi
from rfc_http_validate.markdown import extract_md
from rfc_http_validate.xml import extract_xml

term = Terminal()


class ValidatorCLI(ValidatorUi):
    def __init__(self) -> None:
        self.args = self.parse_args()
        self.field_types = self.load_field_types()
        self.errors = 0
        self.run()

    def run(self) -> None:
        validator = RfcHttpValidator(self.field_types, self)
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

    def load_field_types(self) -> Dict[str, str]:
        field_types = {}
        if self.args.map:
            try:
                jsonmap = json.load(self.args.map)
            except (IOError, ValueError) as why:
                self.fatal_error(f"Cannot load JSON: {why}")
            field_types.update(jsonmap)

        for item in self.args.item:
            field_types[item.lower()] = "item"
        for _list in self.args.list:
            field_types[_list.lower()] = "list"
        for _dict in self.args.dict:
            field_types[_dict.lower()] = "dictionary"
        return field_types

    def fatal_error(self, message: str) -> None:
        sys.stderr.write(f"{term.red}FATAL ERROR:{term.normal} {message}\n")
        sys.exit(1)
