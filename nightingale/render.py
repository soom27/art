"""matplotlib 으로 장미 그래프를 그린다.

기하 계산은 :mod:`nightingale.rose` 가 끝낸 상태로 넘어온다. 이 모듈이 하는
일은 부채꼴을 실제 좌표에 얹고, 눈금·범례·라벨을 붙이는 것뿐이다.

레이아웃 규칙 몇 가지:

* 두 장은 **같은 반지름 눈금**을 쓴다. 각자의 최대값에 맞추면 1855년의
  급감이라는 이 데이터의 핵심이 그림에서 사라진다.
* 반지름은 제곱근 축이므로 기준 원의 간격이 밖으로 갈수록 좁아진다.
  값을 오해하지 않도록 기준 원마다 숫자를 적고 캡션에 축을 명시한다.
* 직접 라벨은 최악의 달 하나에만 붙인다. 24개 값을 다 적으면 아무도 안 읽는다.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from .data import (
    CAUSE_LABELS_EN,
    CAUSE_LABELS_KO,
    CAUSES,
    MonthlyMortality,
)
from .rose import Rose, Wedge, ring_values, shared_max_radius
from .theme import Theme, find_korean_font, get_theme

_MONTHS_EN = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

_TEXT_KO = {
    "title": "동방(東方) 파견 영국군 사망 원인",
    "subtitle": "월별 연율 환산 사망률(병력 1,000명당) · 부채꼴의 면적이 사망률에 비례한다",
    "peak_stacked": "{month}\n합계 {value:,.0f}",
    "peak_superimposed": "{month}\n최대 {value:,.0f}",
    "caption": (
        "반지름은 사망률의 제곱근(면적 비례). 두 장은 같은 눈금을 쓴다.\n"
        "자료: F. Nightingale, 「Notes on Matters Affecting the Health, Efficiency and "
        "Hospital Administration of the British Army」(1858)"
    ),
    "panel": "{start}~{end}",
    "superimposed_note": "겹쳐 그린 작도(원본 방식) — 원인별 면적이 서로 포개져 있다",
}

_TEXT_EN = {
    "title": "Causes of mortality in the British army in the East",
    "subtitle": "Monthly deaths at an annual rate per 1,000 · wedge area is proportional to the rate",
    "peak_stacked": "{month}\ntotal {value:,.0f}",
    "peak_superimposed": "{month}\nlargest cause {value:,.0f}",
    "caption": (
        "Radius is the square root of the rate, so area encodes the value. Both panels share one scale.\n"
        "Source: F. Nightingale, Notes on Matters Affecting the Health, Efficiency and "
        "Hospital Administration of the British Army (1858)"
    ),
    "panel": "{start}–{end}",
    "superimposed_note": "Superimposed construction (as in the original) — the causes overlap",
}

#: 달 사이, 그리고 원인 사이를 벌리는 각도. 배경색이 경계를 만든다.
_THETA_GAP_DEG = 0.25

#: 반지름 눈금 숫자를 놓을 방향. 두 장 모두 이 언저리가 비어 있다.
_RLABEL_ANGLE_DEG = 60.0

#: 직접 라벨을 놓을 반지름 (최대 반지름 대비). 달 이름 고리 바깥이다.
_CALLOUT_RADIUS_FACTOR = 1.32


def _theta_rad(degrees: float) -> float:
    """각도를 [0, 360) 으로 접어 라디안으로. matplotlib 의 극좌표축은 음수 각도를
    넣으면 theta 범위 자체를 늘려버려서, 쓰지도 않은 경계선이 생기고 눈금
    위치가 틀어진다."""
    return math.radians(degrees % 360.0)


def _panel_title(rose: Rose, korean: bool) -> str:
    first, last = rose.records[0], rose.records[-1]
    if korean:
        return _TEXT_KO["panel"].format(start=first.label_ko, end=last.label_ko)
    return _TEXT_EN["panel"].format(
        start=f"{_MONTHS_EN[first.month - 1]} {first.year}",
        end=f"{_MONTHS_EN[last.month - 1]} {last.year}",
    )


def _month_label(record: MonthlyMortality, korean: bool) -> str:
    return record.short_label_ko if korean else _MONTHS_EN[record.month - 1]


def _peak_wedge(roses: Sequence[Rose]) -> tuple[int, Wedge]:
    """가장 멀리 뻗은 부채꼴과 그것이 속한 장의 번호.

    반지름으로 고르는 이유는 그 값이 작도 방식과 무관하게 "그림에서 가장 큰
    것"이기 때문이다. 쌓아 그리면 그 달의 합계, 겹쳐 그리면 그 달의 최대
    원인이 되고, 어느 쪽이든 라벨이 가리키는 부채꼴과 숫자가 일치한다.
    """
    best_index, best = 0, roses[0].wedges[0]
    for index, rose in enumerate(roses):
        for wedge in rose.wedges:
            if wedge.outer_radius > best.outer_radius:
                best_index, best = index, wedge
    return best_index, best


def _draw_rose(
    ax,
    rose: Rose,
    theme: Theme,
    axis_radius: float,
    ring_radius: float,
    korean: bool,
) -> None:
    gap = math.radians(_THETA_GAP_DEG)

    for wedge in rose.wedges:
        if wedge.outer_radius <= wedge.inner_radius:
            continue  # 사망자 0명인 달 — 그릴 면적이 없다
        ax.bar(
            x=_theta_rad(wedge.theta_mid),
            height=wedge.outer_radius - wedge.inner_radius,
            width=max(math.radians(wedge.theta_span) - gap, 1e-6),
            bottom=wedge.inner_radius,
            color=theme.color(wedge.cause),
            edgecolor=theme.surface,
            linewidth=0.9,
            zorder=2,
        )

    ax.set_facecolor(theme.surface)
    # 온전한 원임을 못박아 둔다. 이게 없으면 matplotlib 이 눈금 각도에서 theta
    # 범위를 넘겨짚고, 쓰지도 않은 시작/끝 경계선을 그린다.
    ax.set_thetalim(0, 2 * math.pi)
    ax.set_ylim(0, axis_radius)
    ax.set_axisbelow(True)

    rings = ring_values(ring_radius)
    ax.set_yticks([math.sqrt(value) for value in rings])
    ax.set_yticklabels(
        [f"{value:,.0f}" for value in rings],
        color=theme.text_muted,
        fontsize=7,
    )
    ax.set_rlabel_position(_RLABEL_ANGLE_DEG)
    for label in ax.get_yticklabels():
        label.set_bbox(
            dict(facecolor=theme.surface, edgecolor="none", pad=1.2, alpha=0.85)
        )

    ax.set_xticks(
        [_theta_rad(rose.wedges_for(record)[0].theta_mid) for record in rose.records]
    )
    ax.set_xticklabels(
        [_month_label(record, korean) for record in rose.records],
        color=theme.text_secondary,
        fontsize=8,
    )
    ax.tick_params(axis="x", pad=2)

    ax.grid(color=theme.gridline, linewidth=0.8, linestyle="-")
    ax.spines["polar"].set_color(theme.axis)
    ax.spines["polar"].set_linewidth(0.8)
    ax.set_title(
        _panel_title(rose, korean),
        color=theme.text_primary,
        fontsize=10,
        pad=14,
    )


def render(
    roses: Sequence[Rose],
    *,
    theme: Theme | str = "light",
    korean: bool | None = None,
):
    """장미 그래프 한 장 이상을 하나의 Figure 에 그린다.

    Args:
        roses: :func:`nightingale.rose.build_rose` 로 만든 장들. 보통 2장.
        theme: :class:`~nightingale.theme.Theme` 또는 ``"light"`` / ``"dark"``.
        korean: 라벨을 한글로 쓸지 여부. ``None`` 이면 한글 글꼴이 설치된
            경우에만 한글을 쓴다.

    Returns:
        ``matplotlib.figure.Figure``.
    """
    import matplotlib

    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    if not roses:
        raise ValueError("그릴 장미 그래프가 없다")
    if any(not rose.wedges for rose in roses):
        raise ValueError("부채꼴이 하나도 없는 장이 섞여 있다")
    if isinstance(theme, str):
        theme = get_theme(theme)

    korean_font = find_korean_font()
    if korean is None:
        korean = korean_font is not None
    if korean and korean_font is None:
        raise RuntimeError(
            "한글 글꼴을 찾지 못했다. 글꼴을 설치하거나 korean=False 로 영문 라벨을 쓴다."
        )

    text = _TEXT_KO if korean else _TEXT_EN
    font_family = [korean_font] if korean else ["DejaVu Sans"]

    with plt.rc_context({"font.family": font_family, "axes.unicode_minus": False}):
        fig, axes = plt.subplots(
            1,
            len(roses),
            figsize=(5.5 * len(roses), 6.0),
            subplot_kw={"projection": "polar"},
        )
        axes = [axes] if len(roses) == 1 else list(axes)
        fig.patch.set_facecolor(theme.page)

        # 기준 원은 실제 데이터 최대값까지만, 축은 부채꼴이 테두리에 닿지 않게 조금 더.
        ring_radius = shared_max_radius(roses)
        axis_radius = shared_max_radius(roses, padding=0.05)
        for ax, rose in zip(axes, roses):
            _draw_rose(ax, rose, theme, axis_radius, ring_radius, korean)

        # 직접 라벨은 최악의 달 하나에만. 24개 값을 다 적으면 아무도 안 읽는다.
        peak_index, peak_wedge = _peak_wedge(roses)
        peak = peak_wedge.record
        peak_angle = _theta_rad(peak_wedge.theta_mid)
        peak_radius = peak_wedge.outer_radius
        peak_key = f"peak_{roses[peak_index].layout}"
        axes[peak_index].annotate(
            text[peak_key].format(
                month=peak.label_ko if korean else f"{_MONTHS_EN[peak.month - 1]} {peak.year}",
                value=peak_radius**2,
            ),
            xy=(peak_angle, peak_radius),
            xytext=(peak_angle, axis_radius * _CALLOUT_RADIUS_FACTOR),
            textcoords="data",
            color=theme.text_primary,
            fontsize=8,
            ha="center",
            va="center",
            linespacing=1.3,
            arrowprops=dict(arrowstyle="-", color=theme.axis, linewidth=0.8),
            annotation_clip=False,
        )

        labels = CAUSE_LABELS_KO if korean else CAUSE_LABELS_EN
        handles = [
            Patch(facecolor=theme.color(cause), edgecolor="none", label=labels[cause])
            for cause in CAUSES
        ]
        fig.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.905),
            ncol=len(handles),
            frameon=False,
            fontsize=8.5,
            labelcolor=theme.text_primary,
            handlelength=1.1,
            handleheight=1.1,
            columnspacing=1.6,
        )

        fig.suptitle(text["title"], color=theme.text_primary, fontsize=15, y=0.985)
        subtitle = text["subtitle"]
        if any(rose.layout == "superimposed" for rose in roses):
            subtitle = f"{subtitle}\n{text['superimposed_note']}"
        fig.text(
            0.5,
            0.945,
            subtitle,
            color=theme.text_secondary,
            fontsize=9,
            ha="center",
            va="top",
        )
        fig.text(
            0.5,
            0.035,
            text["caption"],
            color=theme.text_muted,
            fontsize=7.5,
            ha="center",
            va="center",
            linespacing=1.5,
        )
        fig.subplots_adjust(left=0.11, right=0.97, top=0.78, bottom=0.13, wspace=0.26)

    return fig


def save(
    roses: Sequence[Rose],
    path: str | Path,
    *,
    theme: Theme | str = "light",
    korean: bool | None = None,
    dpi: int = 200,
) -> Path:
    """그래프를 그려 파일로 저장한다."""
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = render(roses, theme=theme, korean=korean)
    try:
        figure.savefig(path, dpi=dpi, facecolor=figure.get_facecolor())
    finally:
        plt.close(figure)
    return path
