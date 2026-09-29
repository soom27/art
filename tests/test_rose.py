"""장미 그래프의 기하 — 값이 면적으로 옮겨지는지."""

from __future__ import annotations

import math

import pytest

from nightingale.data import CAUSES, CRIMEA_MORTALITY, periods
from nightingale.rose import (
    build_rose,
    radius_for,
    ring_values,
    shared_max_radius,
)

FIRST_YEAR, SECOND_YEAR = periods()


def test_radius_is_the_square_root_of_the_value():
    assert radius_for(0) == 0
    assert radius_for(100) == pytest.approx(10)
    # 값이 4배면 반지름은 2배 — 면적이 4배가 되도록.
    assert radius_for(400) == pytest.approx(2 * radius_for(100))


def test_negative_value_is_rejected():
    with pytest.raises(ValueError):
        radius_for(-1)


def test_area_is_proportional_to_value():
    """이 그래프의 존재 이유. 부채꼴 면적 / 값 이 모든 조각에서 같아야 한다."""
    rose = build_rose(FIRST_YEAR)
    ratios = [wedge.area / wedge.value for wedge in rose.wedges if wedge.value > 0]
    assert ratios, "0이 아닌 값이 하나도 없다"
    for ratio in ratios:
        assert ratio == pytest.approx(ratios[0])


def test_radius_would_exaggerate_if_used_directly():
    """반지름에 값을 그대로 넣으면 면적이 값의 제곱으로 부푼다 — 그걸 피했는지."""
    rose = build_rose(FIRST_YEAR)
    small, large = sorted(
        (w for w in rose.wedges if w.cause == "disease" and w.value > 0),
        key=lambda w: w.value,
    )[:: max(1, len(FIRST_YEAR) - 1)][:2]
    value_ratio = large.value / small.value
    assert large.area / small.area == pytest.approx(value_ratio)
    assert large.outer_radius / small.outer_radius == pytest.approx(math.sqrt(value_ratio))


def test_months_tile_the_full_circle():
    rose = build_rose(FIRST_YEAR)
    spans = {record: None for record in rose.records}
    for record in rose.records:
        wedges = rose.wedges_for(record)
        assert len({(w.theta_start, w.theta_end) for w in wedges}) == 1
        spans[record] = (wedges[0].theta_start, wedges[0].theta_end)

    widths = [end - start for start, end in spans.values()]
    assert sum(widths) == pytest.approx(360.0)
    assert all(width == pytest.approx(30.0) for width in widths)

    ordered = sorted(spans.values())
    for (_, end), (next_start, _) in zip(ordered, ordered[1:]):
        assert end == pytest.approx(next_start), "달 사이에 틈이나 겹침이 있다"


def test_months_run_clockwise_from_the_top_by_default():
    rose = build_rose(FIRST_YEAR)
    april, may = rose.records[0], rose.records[1]
    assert rose.wedges_for(april)[0].theta_end == pytest.approx(90.0)
    # 시계방향이므로 다음 달의 각도가 더 작다.
    assert rose.wedges_for(may)[0].theta_mid < rose.wedges_for(april)[0].theta_mid


def test_counterclockwise_is_available():
    rose = build_rose(FIRST_YEAR, clockwise=False, start_angle=0.0)
    april, may = rose.records[0], rose.records[1]
    assert rose.wedges_for(april)[0].theta_start == pytest.approx(0.0)
    assert rose.wedges_for(may)[0].theta_mid > rose.wedges_for(april)[0].theta_mid


def test_stacked_segments_touch_and_end_at_the_total():
    rose = build_rose(FIRST_YEAR, layout="stacked")
    for record in rose.records:
        wedges = rose.wedges_for(record)
        assert [w.cause for w in wedges] == list(CAUSES)
        assert wedges[0].inner_radius == 0.0
        for inner, outer in zip(wedges, wedges[1:]):
            assert inner.outer_radius == pytest.approx(outer.inner_radius)
        assert wedges[-1].outer_radius == pytest.approx(radius_for(record.total_rate))


def test_superimposed_draws_every_cause_from_the_centre():
    rose = build_rose(FIRST_YEAR, layout="superimposed")
    for record in rose.records:
        wedges = rose.wedges_for(record)
        assert all(w.inner_radius == 0.0 for w in wedges)
        for wedge in wedges:
            assert wedge.outer_radius == pytest.approx(radius_for(record.rate(wedge.cause)))
        # 큰 것부터 나와야 나중에 그린 작은 부채꼴이 보인다.
        radii = [w.outer_radius for w in wedges]
        assert radii == sorted(radii, reverse=True)


def test_unknown_layout_and_cause_are_rejected():
    with pytest.raises(ValueError):
        build_rose(FIRST_YEAR, layout="spiral")
    with pytest.raises(ValueError):
        build_rose(FIRST_YEAR, causes=("cholera",))
    with pytest.raises(ValueError):
        build_rose(FIRST_YEAR, causes=())


def test_empty_period_makes_an_empty_rose():
    rose = build_rose([])
    assert rose.wedges == ()
    assert rose.max_radius == 0.0


def test_both_panels_can_share_one_scale():
    roses = [build_rose(period) for period in periods()]
    shared = shared_max_radius(roses)
    assert shared == pytest.approx(max(rose.max_radius for rose in roses))
    # 1855년의 급감이 보이려면 두 번째 장이 첫 장보다 확실히 작아야 한다.
    # 반지름은 제곱근이므로 비교는 값(사망률)으로 한다.
    peaks = [max(r.total_rate for r in rose.records) for rose in roses]
    assert peaks[1] < peaks[0] / 3
    assert shared_max_radius(roses, padding=0.05) == pytest.approx(shared * 1.05)
    with pytest.raises(ValueError):
        shared_max_radius(roses, padding=-0.1)


def test_rings_stay_inside_the_data():
    roses = [build_rose(period) for period in periods()]
    shared = shared_max_radius(roses)
    rings = ring_values(shared)
    assert rings == [250.0, 500.0, 750.0, 1000.0]
    assert max(rings) <= max(r.total_rate for r in CRIMEA_MORTALITY)
    with pytest.raises(ValueError):
        ring_values(shared, step=0)


def test_zero_value_produces_a_zero_area_wedge():
    """전상 사망자가 없던 달도 부채꼴 자체는 만들어지되 면적이 0이다."""
    rose = build_rose(FIRST_YEAR)
    april = rose.records[0]
    wounds = next(w for w in rose.wedges_for(april) if w.cause == "wounds")
    assert wounds.value == 0
    assert wounds.inner_radius == pytest.approx(wounds.outer_radius)
    assert wounds.area == pytest.approx(0.0)
