from os.path import basename
from typing import Dict, IO

import commonmark  # type: ignore[import]
from commonmark.node import Node  # type: ignore[import]

from .validate import RfcHttpValidator


def extract_md(fh: IO, validator: RfcHttpValidator) -> None:
    parser = commonmark.Parser()
    doc = parser.parse(fh.read())
    handler = MarkdownHttpExtractor(validator, fh.name)
    handler.render(doc)


class MarkdownHttpExtractor(commonmark.render.renderer.Renderer):
    def __init__(self, validator: RfcHttpValidator, filename: str) -> None:
        self.validator = validator
        self.sourcepos = None
        self.filename = filename

    def code_block(self, node: Node, entering: bool) -> None:
        info = node.info or ""
        self.sourcepos = node.sourcepos[0][0]
        if info in ["http-message"]:
            self.validator.validate(node.literal, self.location)
        else:
            self.validator.ui.skip(self.location(info), "section not a 'http-message'")

    def location(self, pinpoint: str = "") -> str:
        out = f"{basename(self.filename)}:{self.sourcepos}"
        if pinpoint:
            out += f" '{pinpoint}'"
        return out
