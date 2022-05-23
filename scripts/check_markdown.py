#!/usr/bin/env python3

from pathlib import Path

from dnd_md import DNDMarkdown, Logger

if __name__ == "__main__":
    for path in Path(".").iterdir():
        if path.is_file() and path.suffix == ".md":
            DNDMarkdown(path, Logger(path)).check_integrity()
