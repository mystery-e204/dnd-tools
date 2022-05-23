from collections import OrderedDict
import sys
from pathlib import Path

from sty import fg, rs, Style

class Logger:
    ERROR = ("error", fg.li_red)
    WARNING = ("warning", fg.li_yellow)

    def __init__(self, title: str):
        self._use_color = sys.stdout.isatty()
        self._fresh = True
        self._title = self._stylize(f"* {title}", fg.li_cyan)

    def _stylize(self, text: str, style: Style) -> str:
        return f"{style}{text}{rs.all}" if self._use_color else text

    def log(self, kind: tuple[str, Style], message: str):
        if self._fresh:
            self._fresh = False
            print(self._title)

        front = self._stylize(f"{kind[0]}:", kind[1])
        print(f"   {front} {message}")

class DNDMarkdown:
    """Representation of a DnD Markdown document."""

    _charac_keys = ["Race", "Gender", "Birthday", "Age"]

    def __init__(self, file_path: Path, logger: Logger = None):
        self._path = file_path
        self._logger = logger

        with open(file_path, "r", encoding="utf-8") as file:
            self._lines = [line.rstrip("\n") for line in file.readlines()]

        self._tags = self._get_tags()
        self._characs, self._characs_start_line = self._get_characteristics()

    @property
    def characteristics(self) -> dict[str, str]:
        return dict(self._characs)

    @characteristics.setter
    def characteristics(self, characs: dict[str, str]):
        if not self._characs:
            raise Exception(f"File {self._path} does not have characteristics")

        for _ in range(len(self._characs)):
            self._lines.pop(self._characs_start_line)

        self._characs = OrderedDict()
        for key in DNDMarkdown._charac_keys:
            if key in characs:
                self._characs[key] = characs[key]

        for key, val in characs.items():
            if not key in self._characs:
                self._characs[key] = val

        for key, val in reversed(self._characs.items()):
            self._lines.insert(self._characs_start_line, f"* {key}: {val}")

    def update_file(self):
        """Update markdown file on disk."""
        with open(self._path, "w", encoding="utf-8") as file:
            file.write("\n".join(self._lines))

    def _log_error(self, msg: str):
        if self._logger:
            self._logger.log(self._logger.ERROR, msg)

    def _log_warning(self, msg: str):
        if self._logger:
            self._logger.log(self._logger.WARNING, msg)

    def _get_tags(self) -> list[str]:
        """Return all hashtags found in document.

        Only the last non-empty line is considered for finding hashtags.
        The hash symbol is stripped from each tag.
        """
        for line in reversed(self._lines):
            tags = line.split()
            if tags:
                if all(t.startswith("#") for t in tags) and not any(t.startswith("##") or len(t) == 1 for t in tags):
                    return [t[1:] for t in tags]
                else:
                    self._log_warning("No tags found")
                    return []

    def _get_characteristics(self) -> tuple[OrderedDict[str, str], int]:
        """Return characteristics.

        Characteristics are returned as an ordered dict.
        In addition, the index of the first line of the characteristics block is returned.
        """
        # Find the characteristics heading
        for line_idx, line in enumerate(self._lines):
            if line.startswith("#"):
                heading = line[line.find(" ") + 1 :]
                if heading.lower() == "characteristics":
                    if heading != "Characteristics":
                        self._log_error("Characteristics heading has wrong case")
                    if not line.startswith("## "):
                        self._log_error("Characteristics heading has wrong level")
                    break
        else:
            return {}, None

        if self._lines[line_idx + 1].strip():
            self._log_error("Missing line break after characteristics heading")

        # Skip empty lines
        for line_idx, line in enumerate(self._lines[line_idx + 1 :], line_idx + 1):
            if line.strip():
                break

        # Parse characteristics line by line
        characs = OrderedDict()
        for line in self._lines[line_idx :]:
            key, ok, val = line.partition(":")
            if not ok:
                break
            if key.startswith("* "):
                key = key[2:].strip()
                val = val.strip()
                if key:
                    if key in characs:
                        self._log_error(f"{key} appears twice in characteristics block")
                    characs[key] = val

        return characs, line_idx

    def _check_trailing_whitespaces(self):
        """Checks if there are any trailing whitespace characters."""
        past_tag_line = False
        for rev_idx, line in enumerate(reversed(self._lines)):
            if not past_tag_line and self._tags and line:
                past_tag_line = True
                continue
            if line and line[-1] == " ":
                self._log_warning(f"Trailing whitespace found on line {len(self._lines) - rev_idx}")

    def _check_title_line(self):
        """Check integrity of the title line."""
        line = self._lines[0]

        if not line.startswith("#"):
            self._log_error("Title missing on first line")
        elif line.startswith("##"):
            self._log_error("Title heading has wrong level")
        elif not line.startswith("# "):
            self._log_error("Title is malformed")
        elif line != f"# {self._path.stem}":
            self._log_error("Title does not match file name")

    def _check_characteristics(self):
        """Check presence and integrity of characteristics block."""
        person_tag_found = "person" in self._tags
        if self._characs and not person_tag_found:
            self._log_warning("Characteristics block found but tag 'person' missing")
        if person_tag_found and not self._characs:
            self._log_warning("Tag 'person' found but characteristics block missing")

        if not self._characs:
            return

        found_error = False
        for ref_key in DNDMarkdown._charac_keys:
            if not ref_key in self._characs:
                self._log_error(f"{ref_key} missing from characteristics")
                found_error = True

        if not found_error:
            if any(key != ref_key for key, ref_key in zip(self._characs, DNDMarkdown._charac_keys)):
                self._log_error("Characteristics block is shuffled")
            for key, val in self._characs.items():
                if not val:
                    self._log_warning(f"{key} has no value")

    def check_integrity(self) -> bool:
        """Check integrity of the DnD markdown file."""
        if not self._lines:
            self._log_error("File is empty")
            return

        self._check_trailing_whitespaces()
        self._check_title_line()
        self._check_characteristics()
