"""나이팅게일 장미 그래프 — 데이터, 기하 계산, 렌더링.

빠르게 한 장 뽑아보려면::

    from nightingale import build_roses, save

    save(build_roses(), "rose.png", theme="light")

명령줄에서는::

    python -m nightingale --out out/rose.png --table
"""

from __future__ import annotations

from typing import Sequence

from .data import CAUSES, CRIMEA_MORTALITY, MonthlyMortality, periods
from .render import render, save
from .rose import Rose, Wedge, build_rose, radius_for, ring_values, shared_max_radius
from .table import format_table
from .theme import DARK, LIGHT, Theme, get_theme

__all__ = [
    "CAUSES",
    "CRIMEA_MORTALITY",
    "DARK",
    "LIGHT",
    "MonthlyMortality",
    "Rose",
    "Theme",
    "Wedge",
    "build_rose",
    "build_roses",
    "format_table",
    "get_theme",
    "periods",
    "radius_for",
    "render",
    "ring_values",
    "save",
    "shared_max_radius",
]


def build_roses(
    records: Sequence[MonthlyMortality] = CRIMEA_MORTALITY,
    *,
    months_per_period: int = 12,
    **kwargs,
) -> list[Rose]:
    """원본처럼 12개월씩 끊어 장미 그래프 여러 장을 만든다.

    `kwargs` 는 :func:`nightingale.rose.build_rose` 로 그대로 넘어간다.
    """
    return [
        build_rose(period, **kwargs)
        for period in periods(tuple(records), months_per_period=months_per_period)
    ]
