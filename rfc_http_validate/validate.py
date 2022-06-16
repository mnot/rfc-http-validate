from typing import Callable, Dict, List

from .methods import REGISTERED_METHODS


class ValidatorUi:
    def status(self, message: str) -> None:
        pass

    def skip(self, subject: str, message: str) -> None:
        pass

    def success(self, subject: str, message: str) -> None:
        pass

    def error(self, subject: str, message: str) -> None:
        pass

    def fatal_error(self, message: str) -> None:
        pass


class RfcHttpValidator:
    def __init__(self, typemap: Dict[str, Callable], ui: ValidatorUi):
        self.typemap = typemap
        self.ui = ui
        self.location: Callable[..., str] = None

    def validate(self, http_message: str, location: Callable[..., str]) -> None:
        self.location = location
        lines = http_message.strip("\n").split("\n")
        if len(lines) == 0:
            self.ui.error(self.location(), "Empty http-message")
            return
        lines = self.combine_8792(lines)
        skip_lines = self.check_start_line(lines[0])
        try:
            headers = self.combine_headers(lines[skip_lines:])
        except ValueError as why:
            self.ui.error(self.location(), str(why))
            return
        for hname, hvalue in headers.items():
            header_type = self.typemap.get(hname)
            if header_type:
                subject = f"{hname}: {hvalue}"
                try:
                    header_type().parse(hvalue.encode("ascii"))
                    self.ui.success(self.location(subject), "valid")
                except ValueError as why:
                    self.ui.error(self.location(subject), str(why))
            else:
                self.ui.skip(self.location(hname), "no type information")

    def check_start_line(self, start_line: str) -> int:
        if start_line[0].isspace():
            self.ui.error(
                self.location(start_line), "Start line starts with whitespace"
            )
            return 0
        parts = start_line.split(" ")
        if parts[0][-1] == ":":
            return 0  # it must be a header line
        if "http" in parts[0].lower():
            if parts[0] != "HTTP/1.1":
                self.ui.error(
                    self.location(start_line),
                    "Status line doesn't start with 'HTTP/1.1'",
                )
            elif len(parts) < 3:
                self.ui.error(
                    self.location(),
                    f"Status line '{start_line}' isn't 'HTTP/1.1 [status_code] [status_phrase]'",
                )
            else:
                if not parts[1].isdigit():
                    self.ui.error(self.location(parts[1]), "Non-numeric status code")
                elif not 99 < int(parts[1]) < 600:
                    self.ui.error(self.location(parts[1]), "Status code out of range")
        else:
            if len(parts) < 3:
                self.ui.error(
                    self.location(), "Request line isn't '[method] [url] HTTP/1.1'"
                )
            else:
                if parts[0] not in REGISTERED_METHODS:
                    self.ui.error(self.location(parts[0]), "Method not recognised")
                if parts[2] != "HTTP/1.1":
                    self.ui.error(
                        self.location(),
                        f"Request line '{start_line}' doesn't end with 'HTTP/1.1'",
                    )
                if len(parts) > 3:
                    self.ui.error(
                        self.location(start_line), "Request line has extra text"
                    )
        return 1

    def combine_8792(self, lines: List[str]) -> List[str]:
        if not "NOTE: '\\' line wrapping per RFC 8792" in lines[0]:
            return lines
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
                    raise ValueError("Body without headers")
                in_body = True
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
            except ValueError as why:
                raise ValueError(f"Non-field line '{line}' in content") from why
            if " " in name:
                self.ui.error(self.location(name), "Whitespace in field name")
            name = name.lower()
            value = value.strip()
            if name in headers:
                headers[name] += f", {value}"
            else:
                headers[name] = value
            prev_name = name
        return headers
