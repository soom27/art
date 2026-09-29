"""렌더링 — 파일이 실제로 나오는지, 눈금이 공유되는지."""

from __future__ import annotations

import pytest

matplotlib = pytest.importorskip("matplotlib", reason="그림 테스트에는 matplotlib 가 필요하다")
matplotlib.use("Agg")

from nightingale import build_roses  # noqa: E402
from nightingale.render import _peak_wedge, render, save  # noqa: E402
from nightingale.theme import find_korean_font  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.fixture
def roses():
    return build_roses()


def test_one_axes_per_period(roses):
    import matplotlib.pyplot as plt

    figure = render(roses, theme="light", korean=False)
    try:
        assert len(figure.axes) == len(roses)
    finally:
        plt.close(figure)


def test_panels_share_one_radial_scale(roses):
    import matplotlib.pyplot as plt

    figure = render(roses, theme="light", korean=False)
    try:
        limits = {axes.get_ylim() for axes in figure.axes}
        assert len(limits) == 1, "장마다 눈금이 다르면 급감이 사라진다"
    finally:
        plt.close(figure)


def test_callout_points_at_the_largest_wedge(roses):
    index, wedge = _peak_wedge(roses)
    assert index == 0
    assert (wedge.record.year, wedge.record.month) == (1855, 1)
    # 쌓아 그린 그림에서 가장 바깥은 그 달의 합계다.
    assert wedge.outer_radius**2 == pytest.approx(wedge.record.total_rate)


def test_callout_follows_the_layout():
    superimposed = build_roses(layout="superimposed")
    _, wedge = _peak_wedge(superimposed)
    # 겹쳐 그리면 가장 바깥은 합계가 아니라 그 달 최대 원인이다.
    assert wedge.cause == "disease"
    assert wedge.outer_radius**2 == pytest.approx(wedge.record.rate("disease"))


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_save_writes_a_png(tmp_path, roses, theme):
    path = save(roses, tmp_path / f"rose_{theme}.png", theme=theme, korean=False, dpi=72)
    assert path.exists()
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert path.stat().st_size > 10_000


def test_save_creates_missing_directories(tmp_path, roses):
    path = save(roses, tmp_path / "deep" / "er" / "rose.png", korean=False, dpi=72)
    assert path.exists()


def test_korean_labels_need_a_korean_font(roses):
    import matplotlib.pyplot as plt

    if find_korean_font() is None:
        with pytest.raises(RuntimeError):
            render(roses, korean=True)
    else:
        figure = render(roses, korean=True)
        plt.close(figure)


def test_empty_input_is_rejected():
    with pytest.raises(ValueError):
        render([])
