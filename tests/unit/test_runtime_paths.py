from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from nornikel_kg.services import runtime


def test_project_root_prefers_environment_variable(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))

    assert runtime.project_root() == tmp_path.resolve()
