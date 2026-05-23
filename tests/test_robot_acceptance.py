from __future__ import annotations

from pathlib import Path

from robot import run as robot_run


def test_robot_suite_passes(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    suite = project_root / "tests" / "robot"
    output_dir = tmp_path / "robot-output"

    rc = robot_run(
        str(suite),
        outputdir=str(output_dir),
        pythonpath=[str(project_root / "src")],
        console="dotted",
    )

    assert rc == 0
