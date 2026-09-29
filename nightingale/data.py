"""나이팅게일의 크림 전쟁 사망률 데이터.

Florence Nightingale, *Notes on Matters Affecting the Health, Efficiency and
Hospital Administration of the British Army* (1858) 에 실린
"Diagram of the Causes of Mortality in the Army in the East" 의 원자료다.

원본 도표는 1854년 4월 ~ 1856년 3월, 24개월을 두 장의 장미 그래프로 나눠
그렸다. 각 달의 값은 **연율 환산 사망률**(annual rate of mortality per 1,000)
이며, 원 자료인 월별 사망자 수와 평균 병력 규모에서 계산된다:

    rate = deaths * 12 * 1000 / army

이 모듈은 파생값(사망률)이 아니라 원자료(사망자 수, 병력)를 저장하고
사망률은 계산해서 쓴다. 두 벌을 따로 적어두면 서로 어긋날 수 있기 때문이다.
"""

from __future__ import annotations

from dataclasses import dataclass

#: 사망 원인 3종. 원본 도표의 범례 순서와 같다.
CAUSES: tuple[str, str, str] = ("disease", "wounds", "other")

CAUSE_LABELS_KO: dict[str, str] = {
    "disease": "전염병 등 예방 가능한 질병",
    "wounds": "전상(戰傷)",
    "other": "기타 원인",
}

CAUSE_LABELS_EN: dict[str, str] = {
    "disease": "Preventable or mitigable zymotic diseases",
    "wounds": "Wounds and injuries",
    "other": "All other causes",
}

_MONTH_NAMES_KO = (
    "1월", "2월", "3월", "4월", "5월", "6월",
    "7월", "8월", "9월", "10월", "11월", "12월",
)


@dataclass(frozen=True)
class MonthlyMortality:
    """한 달치 관측값.

    Attributes:
        year: 연도.
        month: 월 (1-12).
        army: 해당 월의 평균 병력 규모.
        disease: 예방 가능한 질병으로 인한 사망자 수.
        wounds: 전상으로 인한 사망자 수.
        other: 그 밖의 원인으로 인한 사망자 수.
    """

    year: int
    month: int
    army: int
    disease: int
    wounds: int
    other: int

    def deaths(self, cause: str) -> int:
        """`cause` 원인의 사망자 수."""
        if cause not in CAUSES:
            raise KeyError(f"알 수 없는 사망 원인: {cause!r} (가능한 값: {CAUSES})")
        return int(getattr(self, cause))

    def rate(self, cause: str) -> float:
        """`cause` 원인의 연율 환산 사망률 (1,000명당)."""
        return self.deaths(cause) * 12_000 / self.army

    @property
    def total_deaths(self) -> int:
        return self.disease + self.wounds + self.other

    @property
    def total_rate(self) -> float:
        """세 원인을 합친 연율 환산 사망률."""
        return self.total_deaths * 12_000 / self.army

    @property
    def label_ko(self) -> str:
        return f"{self.year}년 {_MONTH_NAMES_KO[self.month - 1]}"

    @property
    def short_label_ko(self) -> str:
        return _MONTH_NAMES_KO[self.month - 1]


#: 1854-04 ~ 1856-03, 24개월. (year, month, army, disease, wounds, other)
CRIMEA_MORTALITY: tuple[MonthlyMortality, ...] = tuple(
    MonthlyMortality(*row)
    for row in (
        (1854, 4, 8_571, 1, 0, 5),
        (1854, 5, 23_333, 12, 0, 9),
        (1854, 6, 28_333, 11, 0, 6),
        (1854, 7, 28_722, 359, 0, 23),
        (1854, 8, 30_246, 828, 1, 30),
        (1854, 9, 30_290, 788, 81, 70),
        (1854, 10, 30_643, 503, 132, 128),
        (1854, 11, 29_736, 844, 287, 106),
        (1854, 12, 32_779, 1_725, 114, 131),
        (1855, 1, 32_393, 2_761, 83, 324),
        (1855, 2, 30_919, 2_120, 42, 361),
        (1855, 3, 30_107, 1_205, 32, 172),
        (1855, 4, 32_252, 477, 48, 57),
        (1855, 5, 35_473, 508, 49, 37),
        (1855, 6, 38_863, 802, 209, 31),
        (1855, 7, 42_647, 382, 134, 33),
        (1855, 8, 44_614, 483, 164, 25),
        (1855, 9, 47_751, 189, 276, 20),
        (1855, 10, 46_852, 128, 53, 18),
        (1855, 11, 37_853, 178, 33, 32),
        (1855, 12, 43_217, 91, 18, 28),
        (1856, 1, 44_212, 42, 2, 48),
        (1856, 2, 43_485, 24, 0, 19),
        (1856, 3, 46_140, 15, 0, 35),
    )
)


def periods(
    records: tuple[MonthlyMortality, ...] = CRIMEA_MORTALITY,
    months_per_period: int = 12,
) -> list[tuple[MonthlyMortality, ...]]:
    """원본처럼 12개월씩 끊어 나눈다.

    Raises:
        ValueError: `records` 길이가 `months_per_period` 의 배수가 아닐 때.
    """
    if months_per_period <= 0:
        raise ValueError("months_per_period 는 1 이상이어야 한다")
    if len(records) % months_per_period:
        raise ValueError(
            f"{len(records)}개월을 {months_per_period}개월 단위로 나눌 수 없다"
        )
    return [
        records[i : i + months_per_period]
        for i in range(0, len(records), months_per_period)
    ]
