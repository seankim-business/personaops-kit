from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .scaffold import ScaffoldError, install_starter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="personaops-kit",
        description="Package and inject PersonaOps starter into OpenClaw/NanoBot workspaces.",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")

    sub = parser.add_subparsers(dest="command")

    init_cmd = sub.add_parser("init", help="Install PersonaOps starter into target directory")
    init_cmd.add_argument("target", help="Target directory to install starter into")
    init_cmd.add_argument("--force", action="store_true", help="Overwrite target if exists")

    inject_cmd = sub.add_parser("inject", help="Inject starter into an existing workspace")
    inject_cmd.add_argument("workspace", help="Workspace root path")
    inject_cmd.add_argument(
        "--profile",
        choices=["openclaw", "nanobot"],
        default="openclaw",
        help="Layout profile for target workspace",
    )
    inject_cmd.add_argument("--name", default="personaops", help="Folder name under workspace")
    inject_cmd.add_argument("--force", action="store_true", help="Overwrite destination if exists")

    return parser


def _resolve_inject_destination(workspace: Path, profile: str, name: str) -> Path:
    # Both profiles currently default to workspace/<name>.
    # Keep profile field for future layout differences.
    if profile in {"openclaw", "nanobot"}:
        return workspace / name
    raise ValueError(f"unsupported profile: {profile}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "init":
        try:
            dst = install_starter(args.target, force=args.force)
            print(f"Installed PersonaOps starter at: {dst}")
            return 0
        except ScaffoldError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    if args.command == "inject":
        workspace = Path(args.workspace).expanduser().resolve()
        dst = _resolve_inject_destination(workspace, args.profile, args.name)
        try:
            installed = install_starter(dst, force=args.force)
            print(f"Injected PersonaOps starter ({args.profile}) at: {installed}")
            return 0
        except ScaffoldError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
