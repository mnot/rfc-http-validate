from typing import Dict, List, Optional, Tuple

from rfc_http_validate.validate import RfcHttpValidator, ValidatorUi


class RecordingUi(ValidatorUi):
    """A ValidatorUi that records every call so tests can assert on outcomes."""

    def __init__(self) -> None:
        self.events: List[Tuple[str, str, str]] = []

    def status(self, message: str) -> None:
        self.events.append(("status", "", message))

    def skip(self, subject: str, message: str) -> None:
        self.events.append(("skip", subject, message))

    def success(self, subject: str, message: str) -> None:
        self.events.append(("success", subject, message))

    def error(self, subject: str, message: str) -> None:
        self.events.append(("error", subject, message))

    def fatal_error(self, message: str) -> None:
        self.events.append(("fatal", "", message))

    # -- helpers -------------------------------------------------------

    def kinds(self) -> List[str]:
        return [kind for kind, _, _ in self.events]

    def messages(self, kind: str) -> List[str]:
        return [msg for k, _, msg in self.events if k == kind]


def run(message: str, field_types: Optional[Dict[str, str]] = None) -> RecordingUi:
    """Validate a raw http-message and return the recording UI."""
    ui = RecordingUi()
    validator = RfcHttpValidator(field_types or {}, ui)
    validator.validate(message, lambda pinpoint="": pinpoint or "loc")
    return ui
