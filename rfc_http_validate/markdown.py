from os.path import basename
from typing import IO, Any

import commonmark
from commonmark.node import Node
from commonmark.render.renderer import Renderer

from rfc_http_validate.validate import RfcHttpValidator


def extract_md(fh: IO[str], validator: RfcHttpValidator) -> None:
    parser = commonmark.Parser()
    doc = parser.parse(fh.read())
    handler = MarkdownHttpExtractor(validator, fh.name)
    handler.render(doc)


class MarkdownHttpExtractor(Renderer):
    def __init__(self, validator: RfcHttpValidator, filename: str) -> None:
        self.validator = validator
        self.sourcepos: Any = None
        self.filename = filename

    def code_block(self, node: Node, entering: bool) -> None:
        info = node.info or ""
        self.sourcepos = node.sourcepos[0][0] if node.sourcepos else None
        if info in ["http-message"]:
            self.validator.validate(node.literal or "", self.location)
        else:
            self.validator.ui.skip(self.location(info), "section not a 'http-message'")

    def location(self, pinpoint: str = "") -> str:
        out = f"{basename(self.filename)}:{self.sourcepos}"
        if pinpoint:
            out += f" '{pinpoint}'"
        return out
