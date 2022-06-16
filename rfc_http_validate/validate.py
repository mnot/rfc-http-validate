from typing import Callable, Dict, List
from xml.sax.handler import ContentHandler

from .methods import REGISTERED_METHODS


class ValidatorUi:
    def status(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass


class RfcHttpValidator(ContentHandler):
    def __init__(self, typemap: Dict[str, Callable], ui: ValidatorUi):
        ContentHandler.__init__(self)
        self.typemap = typemap
        self.ui = ui
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
                lines = self.content.strip("\n").split("\n")
                if len(lines) == 0:
                    self.ui.error("Empty http-message")
                    return
                lines = self.combine_8792(lines)
                skip_lines = self.check_start_line(lines[0])
                try:
                    headers = self.combine_headers(lines[skip_lines:])
                except ValueError as why:
                    self.ui.error(str(why))
                    return
                for hname, hvalue in headers.items():
                    header_type = self.typemap.get(hname)
                    if header_type:
                        try:
                            self.ui.status(f"validating field value {hname}: {hvalue}")
                            header_type().parse(hvalue.encode("ascii"))
                        except ValueError as why:
                            self.ui.error(str(why))
                    else:
                        self.ui.status(
                            f"skipping field value {hname} (no type information)"
                        )
            else:
                self.ui.status(f"skipping section {self.type}")
        self.content = ""

    def characters(self, content: str) -> None:
        if self.listening:
            self.content += content

    def location(self) -> str:
        return f"{self.filename}:{self._locator.getLineNumber()}"  # type: ignore

    def check_start_line(self, start_line: str) -> int:
        if start_line[0].isspace():
            self.ui.error(f"Start line starts with whitespace: '{start_line}'")
            return 0
        parts = start_line.split(" ")
        if parts[0][-1] == ":":
            return 0  # it must be a header line
        if "http" in parts[0].lower():
            self.ui.status(f"{self.location()}: validating status line {start_line}")
            if parts[0] != "HTTP/1.1":
                self.ui.error(
                    f"Status line '{start_line}' doesn't start with 'HTTP/1.1'"
                )
            elif len(parts) < 3:
                self.ui.error(
                    f"Status line '{start_line}' isn't 'HTTP/1.1 [status_code] [status_phrase]'"
                )
            else:
                if not parts[1].isdigit():
                    self.ui.error(f"Status code {parts[1]} is non-numeric")
                elif not 99 < int(parts[1]) < 600:
                    self.ui.error(f"Status code {parts[1]} is out of range")
        else:
            self.ui.status(f"{self.location()}: validating request line {start_line}")
            if len(parts) < 3:
                self.ui.error("Request line isn't '[method] [url] HTTP/1.1'")
            else:
                if parts[0] not in REGISTERED_METHODS:
                    self.ui.error(f"Method '{parts[0]}' not recognised")
                if parts[2] != "HTTP/1.1":
                    self.ui.error(
                        f"Request line '{start_line}' doesn't end with 'HTTP/1.1'"
                    )
                if len(parts) > 3:
                    self.ui.error(f"Request line '{start_line}' has extra text")
        return 1

    def combine_8792(self, lines: List[str]) -> List[str]:
        if not "NOTE: '\\' line wrapping per RFC 8792" in lines[0]:
            return lines
        else:
            lines = lines[2:]
        output = []  # type: List[str]
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

    def combine_headers(self, lines: List[str]) -> Dict[str, str]:
        headers = {}  # type: Dict[str, str]
        prev_name: str = None
        in_body = False
        for line in lines:
            if len(line.strip()) == 0:
                if not headers:  # a blank line before seeing any headers
                    raise ValueError(f"Body without headers")
                in_body = True
                self.ui.status(f"ignoring HTTP message body")
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
            if " " in name:
                self.ui.error(f"Whitespace in field name '{name}'")
            name = name.lower()
            value = value.strip()
            if name in headers:
                headers[name] += f", {value}"
            else:
                headers[name] = value
            prev_name = name
        return headers
