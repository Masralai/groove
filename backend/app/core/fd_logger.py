import os
import traceback
from datetime import datetime

LOG_FORMAT = "[{asctime}] {level:5s}  {name:<35s} {message}"
LEVEL_INFO = "INFO"
LEVEL_WARNING = "WARNING"
LEVEL_ERROR = "ERROR"


class FdLogger:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def info(self, message: str) -> None:
        self._log(LEVEL_INFO, message)

    def warning(self, message: str) -> None:
        self._log(LEVEL_WARNING, message)

    def error(self, message: str) -> None:
        self._log(LEVEL_ERROR, message)

    def exception(self, message: str) -> None:
        tb = traceback.format_exc()
        self._log(LEVEL_ERROR, f"{message}\n{tb}")

    def _log(self, level: str, message: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = LOG_FORMAT.format(asctime=now, level=level, name=self.name, message=message) + "\n"
        os.write(1, line.encode("utf-8", errors="replace"))
