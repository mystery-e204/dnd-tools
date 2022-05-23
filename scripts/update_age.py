#!/usr/bin/env python3

from pathlib import Path
import sys

from dnd_md import DNDMarkdown

if __name__ == "__main__":
    for path in map(Path, sys.argv[1:]):
        if not path.is_file():
            sys.stderr.write(f"Error: '{path}' is not a file")
        dnd_markdown = DNDMarkdown(path)
        characs = dnd_markdown.characteristics
        characs["Age"] = "1337"
        dnd_markdown.characteristics = characs
        dnd_markdown.update_file()
