"""명령줄 동작."""

from __future__ import annotations

import pytest

from nightingale.cli import main


def test_table_only_prints_and_skips_the_chart(capsys, tmp_path):
    out = tmp_path / "never.png"
    assert main(["--table", "--no-chart", "--out", str(out)]) == 0
    assert "1,022.8" in capsys.readouterr().out
    assert not out.exists()


def test_renders_to_the_requested_path(capsys, tmp_path):
    pytest.importorskip("matplotlib")
    out = tmp_path / "rose.png"
    assert main(["--out", str(out), "--lang", "en", "--dpi", "72"]) == 0
    assert out.exists()
    assert str(out) in capsys.readouterr().out


def test_uneven_period_is_an_error(capsys, tmp_path):
    assert main(["--months", "5", "--out", str(tmp_path / "x.png")]) == 2
    assert "오류" in capsys.readouterr().out


def test_deaths_switches_the_table_units(capsys):
    assert main(["--table", "--no-chart", "--deaths"]) == 0
    assert "단위: 사망자 수(명)" in capsys.readouterr().out
