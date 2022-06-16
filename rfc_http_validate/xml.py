from os.path import basename
from typing import Dict, IO
from xml import sax
from xml.sax.handler import ContentHandler

from .validate import RfcHttpValidator


def extract_xml(fh: IO, validator: RfcHttpValidator) -> None:
    handler = XmlHttpExtractor(validator, fh.name)
    try:
        sax.parse(fh, handler)
    except sax.SAXParseException as why:
        validator.ui.fatal_error(str(why))


class XmlHttpExtractor(ContentHandler):
    def __init__(self, validator: RfcHttpValidator, filename: str) -> None:
        ContentHandler.__init__(self)
        self.validator = validator
        self.filename = filename
        self.listening = False
        self.content = ""
        self.type: str = None

    def startElement(self, name: str, attrs: Dict[str, str]) -> None:
        if name in ["sourcecode", "artwork"] and "type" in attrs.keys():
            self.listening = True
            self.type = attrs["type"]

    def endElement(self, name: str) -> None:
        if self.listening:
            self.listening = False
            if self.type in ["http-message"]:
                self.validator.validate(self.content, self.location)
            else:
                self.validator.ui.skip(
                    self.location(self.type), "section not a 'http-message'"
                )
        self.content = ""

    def characters(self, content: str) -> None:
        if self.listening:
            self.content += content

    def location(self, pinpoint: str = "") -> str:
        out = f"{basename(self.filename)}:{self._locator.getLineNumber()}"  # type: ignore
        if pinpoint:
            out += f" '{pinpoint}'"
        return out
