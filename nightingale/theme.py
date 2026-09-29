"""색과 글꼴 — 그래프의 "값이 아닌 부분".

색은 원인(identity)을 구분하는 용도이므로 순서가 고정된 범주형 팔레트를 쓴다.
라이트/다크는 같은 색을 밝기만 바꾼 것이 아니라 각 배경에서 따로 검증된 값이다
(색맹 시뮬레이션 분리도, 명도 대역, 배경 대비를 모두 통과한 조합).

라이트 모드의 aqua(#1baf7a)는 배경 대비가 3:1 아래라서 색만으로는 부족하다.
그래서 범례와 직접 라벨, 그리고 `--table` 로 뽑는 표를 항상 함께 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: 한글을 가진 글꼴 후보. 앞에 있는 것부터 찾는다.
KOREAN_FONT_CANDIDATES: tuple[str, ...] = (
    "Malgun Gothic",
    "AppleGothic",
    "Apple SD Gothic Neo",
    "NanumGothic",
    "NanumBarunGothic",
    "Noto Sans CJK KR",
    "Noto Sans KR",
    "Source Han Sans KR",
    "UnDotum",
    "WenQuanYi Zen Hei",
    "Unifont",
)


@dataclass(frozen=True)
class Theme:
    """한 모드(라이트/다크)의 색 묶음."""

    name: str
    surface: str
    page: str
    text_primary: str
    text_secondary: str
    text_muted: str
    gridline: str
    axis: str
    series: dict[str, str] = field(default_factory=dict)

    def color(self, cause: str) -> str:
        try:
            return self.series[cause]
        except KeyError:
            raise KeyError(f"팔레트에 없는 사망 원인: {cause!r}") from None


LIGHT = Theme(
    name="light",
    surface="#fcfcfb",
    page="#f9f9f7",
    text_primary="#0b0b0b",
    text_secondary="#52514e",
    text_muted="#898781",
    gridline="#e1e0d9",
    axis="#c3c2b7",
    series={"disease": "#2a78d6", "wounds": "#eb6834", "other": "#1baf7a"},
)

DARK = Theme(
    name="dark",
    surface="#1a1a19",
    page="#0d0d0d",
    text_primary="#ffffff",
    text_secondary="#c3c2b7",
    text_muted="#898781",
    gridline="#2c2c2a",
    axis="#383835",
    series={"disease": "#3987e5", "wounds": "#d95926", "other": "#199e70"},
)

THEMES: dict[str, Theme] = {LIGHT.name: LIGHT, DARK.name: DARK}


def get_theme(name: str) -> Theme:
    try:
        return THEMES[name]
    except KeyError:
        raise KeyError(f"알 수 없는 테마: {name!r} (가능한 값: {sorted(THEMES)})") from None


def find_korean_font() -> str | None:
    """설치된 글꼴 중 한글을 표시할 수 있는 첫 후보를 돌려준다.

    없으면 ``None``. 이때 렌더러는 라벨을 영문으로 바꿔 쓴다 — 네모(tofu)로
    깨진 한글을 내보내는 것보다 읽히는 영문이 낫다.
    """
    try:
        from matplotlib import font_manager
    except ImportError:  # pragma: no cover - matplotlib 없이도 import 되게
        return None

    installed = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in KOREAN_FONT_CANDIDATES:
        if candidate in installed:
            return candidate
    return None
