"""Einstiegspunkt für ``python -m bundesanzeiger``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
