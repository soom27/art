"""장미 그래프(polar area diagram)의 기하 계산.

이 그래프의 핵심 규칙은 **값을 반지름이 아니라 면적으로 표현한다**는 것이다.
중심각이 theta 인 부채꼴의 면적은 `theta / 2 * r**2` 이므로, 값을 반지름에
그대로 넣으면 면적이 값의 제곱으로 부풀어 눈이 과장된 값을 읽는다.
따라서 반지름은 값의 제곱근을 쓴다:

    r = sqrt(value)                       (단일 부채꼴)
    r_outer = sqrt(r_inner**2 + value)    (쌓아 올릴 때)

이 모듈은 그림을 그리지 않고 부채꼴의 좌표만 만든다. 반지름 단위는
"sqrt(연율 사망률)" 이며, 눈금 표시는 렌더러가 제곱근 축으로 처리한다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal, Sequence

from .data import CAUSES, MonthlyMortality

Layout = Literal["stacked", "superimposed"]


@dataclass(frozen=True)
class Wedge:
    """부채꼴 하나. 각도는 도(degree), 수학 관례(반시계 양수, 0도 = 3시 방향)."""

    record: MonthlyMortality
    cause: str
    value: float
    theta_start: float
    theta_end: float
    inner_radius: float
    outer_radius: float

    @property
    def theta_span(self) -> float:
        return self.theta_end - self.theta_start

    @property
    def theta_mid(self) -> float:
        return (self.theta_start + self.theta_end) / 2

    @property
    def area(self) -> float:
        """부채꼴의 실제 면적. 값에 정비례해야 한다."""
        span = math.radians(self.theta_span)
        return span / 2 * (self.outer_radius**2 - self.inner_radius**2)


@dataclass(frozen=True)
class Rose:
    """장미 그래프 한 장."""

    wedges: tuple[Wedge, ...]
    records: tuple[MonthlyMortality, ...]
    layout: Layout

    @property
    def max_radius(self) -> float:
        return max((w.outer_radius for w in self.wedges), default=0.0)

    def wedges_for(self, record: MonthlyMortality) -> tuple[Wedge, ...]:
        return tuple(w for w in self.wedges if w.record is record)


def radius_for(value: float) -> float:
    """면적 비례 반지름. 음수 값은 데이터 오류로 본다."""
    if value < 0:
        raise ValueError(f"사망률은 음수가 될 수 없다: {value}")
    return math.sqrt(value)


def build_rose(
    records: Sequence[MonthlyMortality],
    *,
    causes: Iterable[str] = CAUSES,
    layout: Layout = "stacked",
    start_angle: float = 90.0,
    clockwise: bool = True,
) -> Rose:
    """한 기간(보통 12개월)의 부채꼴을 만든다.

    Args:
        records: 시간순 관측값. 각 레코드가 동일한 중심각을 나눠 갖는다.
        causes: 그릴 사망 원인. 중심에서 바깥으로 쌓는 순서이기도 하다.
        layout: ``"stacked"`` 는 원인별로 쌓아 올려 전체 면적이 총 사망률과
            같아진다. ``"superimposed"`` 는 원본 도표처럼 세 원인을 각각
            중심에서부터 그려 겹친다 (아래 주의사항 참고).
        start_angle: 첫 달 부채꼴의 시작 경계 각도. 기본값 90도 = 12시 방향.
        clockwise: 달이 시계방향으로 진행하는지 여부.

    Returns:
        완성된 :class:`Rose`.

    Note:
        ``"superimposed"`` 는 원본의 작도법이지만, 세 원인의 면적이 서로
        겹쳐 있어 작은 원인의 "보이는 면적"이 그 값과 일치하지 않는다.
        원본 도표가 오래 비판받은 지점이므로 기본값은 ``"stacked"`` 다.
    """
    causes = tuple(causes)
    if not causes:
        raise ValueError("사망 원인이 최소 하나는 필요하다")
    unknown = set(causes) - set(CAUSES)
    if unknown:
        raise ValueError(f"알 수 없는 사망 원인: {sorted(unknown)}")
    if not records:
        return Rose(wedges=(), records=(), layout=layout)

    span = 360.0 / len(records)
    wedges: list[Wedge] = []

    for index, record in enumerate(records):
        if clockwise:
            theta_end = start_angle - index * span
            theta_start = theta_end - span
        else:
            theta_start = start_angle + index * span
            theta_end = theta_start + span

        if layout == "stacked":
            cumulative = 0.0
            for cause in causes:
                value = record.rate(cause)
                inner = radius_for(cumulative)
                cumulative += value
                wedges.append(
                    Wedge(
                        record=record,
                        cause=cause,
                        value=value,
                        theta_start=theta_start,
                        theta_end=theta_end,
                        inner_radius=inner,
                        outer_radius=radius_for(cumulative),
                    )
                )
        elif layout == "superimposed":
            # 큰 것부터 만들어 두면 렌더러가 그 순서대로 그려도
            # 작은 부채꼴이 큰 것에 덮이지 않는다.
            ordered = sorted(causes, key=record.rate, reverse=True)
            for cause in ordered:
                value = record.rate(cause)
                wedges.append(
                    Wedge(
                        record=record,
                        cause=cause,
                        value=value,
                        theta_start=theta_start,
                        theta_end=theta_end,
                        inner_radius=0.0,
                        outer_radius=radius_for(value),
                    )
                )
        else:
            raise ValueError(f"알 수 없는 layout: {layout!r}")

    return Rose(wedges=tuple(wedges), records=tuple(records), layout=layout)


def shared_max_radius(roses: Iterable[Rose], *, padding: float = 0.0) -> float:
    """여러 장을 같은 눈금으로 그리기 위한 공통 최대 반지름.

    두 장을 각자의 최대값에 맞춰 그리면 1855년의 급감이 사라진다. 그래서
    모든 장이 이 하나의 값을 쓴다. `padding` 은 부채꼴이 테두리에 닿지 않게
    하려고 반지름에 더하는 비율이며, 기준 원을 계산할 때는 0을 쓴다.
    """
    if padding < 0:
        raise ValueError("padding 은 음수가 될 수 없다")
    largest = max((rose.max_radius for rose in roses), default=0.0)
    return largest * (1.0 + padding)


def ring_values(max_radius: float, step: float = 250.0) -> list[float]:
    """제곱근 축에 표시할 기준 원의 값들 (사망률 단위)."""
    if step <= 0:
        raise ValueError("step 은 0보다 커야 한다")
    limit = max_radius**2
    values: list[float] = []
    value = step
    while value <= limit:
        values.append(value)
        value += step
    return values
