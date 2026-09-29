"""원자료가 스스로 어긋나지 않는지 확인한다."""

from __future__ import annotations

import pytest

from nightingale.data import CAUSES, CRIMEA_MORTALITY, MonthlyMortality, periods


def test_covers_24_contiguous_months():
    assert len(CRIMEA_MORTALITY) == 24
    first, last = CRIMEA_MORTALITY[0], CRIMEA_MORTALITY[-1]
    assert (first.year, first.month) == (1854, 4)
    assert (last.year, last.month) == (1856, 3)

    for previous, current in zip(CRIMEA_MORTALITY, CRIMEA_MORTALITY[1:]):
        months = (current.year - previous.year) * 12 + (current.month - previous.month)
        assert months == 1, f"{previous.label_ko} 다음이 {current.label_ko}"


def test_every_record_is_plausible():
    for record in CRIMEA_MORTALITY:
        assert record.army > 0
        assert 1 <= record.month <= 12
        for cause in CAUSES:
            assert record.deaths(cause) >= 0


def test_rate_is_deaths_annualised_per_thousand():
    record = MonthlyMortality(1855, 1, army=12_000, disease=12, wounds=0, other=0)
    # 한 달에 12명이 죽었으니 1년이면 144명, 병력 12,000명 기준 1,000명당 12명.
    assert record.rate("disease") == pytest.approx(12.0)


def test_published_rates_match():
    """출판된 도표의 숫자와 맞는지 — 1855년 1월이 최악의 달이다."""
    january = next(r for r in CRIMEA_MORTALITY if (r.year, r.month) == (1855, 1))
    assert january.rate("disease") == pytest.approx(1022.8, abs=0.05)
    assert january.rate("wounds") == pytest.approx(30.7, abs=0.05)
    assert january.rate("other") == pytest.approx(120.0, abs=0.05)
    assert january.total_rate == max(r.total_rate for r in CRIMEA_MORTALITY)


def test_total_is_the_sum_of_its_parts():
    for record in CRIMEA_MORTALITY:
        assert record.total_deaths == sum(record.deaths(c) for c in CAUSES)
        assert record.total_rate == pytest.approx(sum(record.rate(c) for c in CAUSES))


def test_unknown_cause_is_rejected():
    with pytest.raises(KeyError):
        CRIMEA_MORTALITY[0].rate("cholera")


def test_periods_split_into_two_years():
    first, second = periods()
    assert len(first) == len(second) == 12
    assert (first[0].year, first[0].month) == (1854, 4)
    assert (second[0].year, second[0].month) == (1855, 4)


def test_periods_rejects_uneven_split():
    with pytest.raises(ValueError):
        periods(CRIMEA_MORTALITY, months_per_period=5)
    with pytest.raises(ValueError):
        periods(CRIMEA_MORTALITY, months_per_period=0)
