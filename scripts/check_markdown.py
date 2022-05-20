#!/usr/bin/env python3

from pathlib import Path

from dnd_md import DNDMarkDown, Logger

if __name__ == "__main__":
    for path in Path(".").iterdir():
        if path.is_file() and path.suffix == ".md":
            DNDMarkDown(path, Logger(path)).check_integrity()
