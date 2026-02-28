from __future__ import annotations

import shutil
from pathlib import Path

import importlib.resources as pkg_resources


class ScaffoldError(RuntimeError):
    pass


def _template_root() -> Path:
    ref = pkg_resources.files("personaops_kit").joinpath("templates", "personaops-starter")
    with pkg_resources.as_file(ref) as p:
        return p


def install_starter(target_dir: str | Path, *, force: bool = False) -> Path:
    target = Path(target_dir).expanduser().resolve()
    if target.exists() and any(target.iterdir()) and not force:
        raise ScaffoldError(f"Target directory is not empty: {target}")

    if target.exists() and force:
        shutil.rmtree(target)

    template = _template_root()
    shutil.copytree(template, target)
    return target
