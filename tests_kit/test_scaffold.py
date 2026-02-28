from pathlib import Path

import pytest

from personaops_kit.scaffold import ScaffoldError, install_starter


def test_install_starter_creates_expected_files(tmp_path: Path):
    dst = tmp_path / "personaops"
    install_starter(dst)

    assert (dst / "PRD.md").exists()
    assert (dst / "SDD.md").exists()
    assert (dst / "implementation" / "control_plane.py").exists()
    assert (dst / "schemas" / "event.schema.json").exists()


def test_install_starter_rejects_non_empty_target_without_force(tmp_path: Path):
    dst = tmp_path / "personaops"
    dst.mkdir()
    (dst / "dummy.txt").write_text("x")

    with pytest.raises(ScaffoldError):
        install_starter(dst, force=False)


def test_install_starter_overwrites_when_force(tmp_path: Path):
    dst = tmp_path / "personaops"
    dst.mkdir()
    (dst / "dummy.txt").write_text("x")

    install_starter(dst, force=True)
    assert not (dst / "dummy.txt").exists()
    assert (dst / "README.md").exists()
