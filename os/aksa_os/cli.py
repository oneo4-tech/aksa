"""The AKSA OS command line entry point."""

import argparse
from collections.abc import Callable, Sequence

import uvicorn

from aksa_os.app import create_app
from aksa_os.settings import Settings

Run = Callable[..., None]


def build_parser(settings: Settings) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aksa-os", description="AKSA OS, the read-only cockpit for aksa.")
    parser.add_argument("--port", type=int, default=settings.port, help=f"port to serve on (default {settings.port})")
    parser.add_argument("--check", action="store_true", help="print the settings and exit")
    return parser


def main(argv: Sequence[str] | None = None, run: Run = uvicorn.run) -> int:
    """Serve the app on localhost, or report settings with --check."""
    settings = Settings()
    args = build_parser(settings).parse_args(argv)
    if args.check:
        print(f"AKSA OS serves on http://{settings.host}:{args.port}")
        print(f"repository: {settings.repo_root}")
        print(f"knowledge base: {settings.kb}")
        print(f"projects: {settings.projects}")
        return 0
    run(create_app(), host=settings.host, port=args.port)
    return 0
