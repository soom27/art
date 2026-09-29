"""표로 뽑는 같은 데이터.

그래프는 색으로 원인을 구분하는데, 라이트 모드의 aqua 는 배경 대비가 낮고
색각 이상이 있으면 색 구분 자체가 흔들린다. 그래서 같은 값을 언제나 표로도
꺼낼 수 있어야 한다 — 그림에서 못 읽은 값은 여기 다 있다.
"""

from __future__ import annotations

from typing import Sequence

from .data import CAUSE_LABELS_EN, CAUSE_LABELS_KO, CAUSES, CRIMEA_MORTALITY, MonthlyMortality

_HEADERS_KO = ("연·월", "병력", "질병", "전상", "기타", "합계")
_HEADERS_EN = ("Month", "Army", "Disease", "Wounds", "Other", "Total")
_MONTHS_EN = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _display_width(text: str) -> int:
    """한글·한자는 터미널에서 두 칸을 차지한다."""
    return sum(2 if ord(char) > 0x1100 and _is_wide(char) else 1 for char in text)


def _is_wide(char: str) -> bool:
    import unicodedata

    return unicodedata.east_asian_width(char) in ("W", "F")


def _pad(text: str, width: int, *, align: str = "right") -> str:
    padding = " " * max(width - _display_width(text), 0)
    return padding + text if align == "right" else text + padding


def format_table(
    records: Sequence[MonthlyMortality] = CRIMEA_MORTALITY,
    *,
    korean: bool = True,
    rates: bool = True,
) -> str:
    """월별 값을 정렬된 표 문자열로 만든다.

    Args:
        records: 출력할 관측값.
        korean: 머리글을 한글로 쓸지 여부.
        rates: ``True`` 면 연율 환산 사망률(그래프에 그려진 값), ``False`` 면
            원 사망자 수를 보여준다.
    """
    headers = _HEADERS_KO if korean else _HEADERS_EN
    labels = CAUSE_LABELS_KO if korean else CAUSE_LABELS_EN

    rows: list[tuple[str, ...]] = []
    for record in records:
        if korean:
            when = f"{record.year}-{record.month:02d}"
        else:
            when = f"{_MONTHS_EN[record.month - 1]} {record.year}"
        if rates:
            values = [f"{record.rate(cause):,.1f}" for cause in CAUSES]
            total = f"{record.total_rate:,.1f}"
        else:
            values = [f"{record.deaths(cause):,}" for cause in CAUSES]
            total = f"{record.total_deaths:,}"
        rows.append((when, f"{record.army:,}", *values, total))

    widths = [
        max(_display_width(header), *(_display_width(row[i]) for row in rows))
        if rows
        else _display_width(header)
        for i, header in enumerate(headers)
    ]

    lines = [
        "  ".join(
            _pad(header, width, align="left" if i == 0 else "right")
            for i, (header, width) in enumerate(zip(headers, widths))
        ),
        "  ".join("-" * width for width in widths),
    ]
    lines += [
        "  ".join(
            _pad(cell, width, align="left" if i == 0 else "right")
            for i, (cell, width) in enumerate(zip(row, widths))
        )
        for row in rows
    ]

    unit = (
        "병력 1,000명당 연율 환산 사망률" if korean else "deaths per 1,000 per year"
    ) if rates else ("사망자 수(명)" if korean else "deaths")
    legend = " · ".join(f"{headers[i + 2]}={labels[cause]}" for i, cause in enumerate(CAUSES))
    lines.append("")
    lines.append(f"{'단위' if korean else 'Unit'}: {unit}")
    lines.append(legend)
    return "\n".join(lines)
