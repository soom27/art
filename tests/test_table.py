"""표 출력 — 그림에서 못 읽은 값을 여기서 읽을 수 있어야 한다."""

from __future__ import annotations

from nightingale.data import CRIMEA_MORTALITY
from nightingale.table import _display_width, format_table


def test_one_row_per_month_plus_header():
    lines = format_table().splitlines()
    header, separator, *rest = lines
    assert "연·월" in header
    assert set(separator) <= {"-", " "}
    rows = [line for line in rest if line.startswith(("1854-", "1855-", "1856-"))]
    assert len(rows) == len(CRIMEA_MORTALITY)


def test_columns_line_up():
    lines = [line for line in format_table().splitlines() if line.strip()]
    widths = {_display_width(line) for line in lines[: len(CRIMEA_MORTALITY) + 2]}
    assert len(widths) == 1, "머리글과 본문의 폭이 다르다"


def test_rates_and_counts_are_both_available():
    rates = format_table()
    counts = format_table(rates=False)
    assert "1,022.8" in rates  # 1855년 1월 질병 사망률
    assert "2,761" in counts   # 같은 달 질병 사망자 수
    assert "단위: 병력 1,000명당 연율 환산 사망률" in rates
    assert "단위: 사망자 수(명)" in counts


def test_english_table():
    text = format_table(korean=False)
    assert text.splitlines()[0].split() == ["Month", "Army", "Disease", "Wounds", "Other", "Total"]
    assert "Jan 1855" in text


def test_empty_input_still_renders_a_header():
    lines = format_table([]).splitlines()
    assert "연·월" in lines[0]
