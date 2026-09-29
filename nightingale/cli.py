"""명령줄 진입점.

    python -m nightingale --out out/rose.png --theme dark --table
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from . import build_roses
from .data import CRIMEA_MORTALITY
from .table import format_table

_DEFAULT_OUT = Path("out/nightingale-rose.png")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m nightingale",
        description="나이팅게일 장미 그래프(polar area diagram)를 그린다.",
    )
    parser.add_argument(
        "-o", "--out", type=Path, default=_DEFAULT_OUT, help=f"저장 경로 (기본: {_DEFAULT_OUT})"
    )
    parser.add_argument(
        "--theme", choices=("light", "dark"), default="light", help="배경 테마 (기본: light)"
    )
    parser.add_argument(
        "--layout",
        choices=("stacked", "superimposed"),
        default="stacked",
        help="원인을 쌓아 그릴지(stacked), 원본처럼 겹쳐 그릴지(superimposed)",
    )
    parser.add_argument(
        "--lang",
        choices=("auto", "ko", "en"),
        default="auto",
        help="라벨 언어. auto 는 한글 글꼴이 있으면 한글 (기본: auto)",
    )
    parser.add_argument("--dpi", type=int, default=200, help="저장 해상도 (기본: 200)")
    parser.add_argument(
        "--months", type=int, default=12, help="한 장에 담을 개월 수 (기본: 12)"
    )
    parser.add_argument("--table", action="store_true", help="같은 값을 표로도 출력한다")
    parser.add_argument(
        "--deaths",
        action="store_true",
        help="--table 에서 사망률 대신 사망자 수를 보여준다",
    )
    parser.add_argument("--no-chart", action="store_true", help="그림은 그리지 않는다")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    korean = {"auto": None, "ko": True, "en": False}[args.lang]

    if args.table:
        print(format_table(CRIMEA_MORTALITY, korean=korean is not False, rates=not args.deaths))
        if not args.no_chart:
            print()

    if args.no_chart:
        return 0

    try:
        roses = build_roses(months_per_period=args.months, layout=args.layout)
    except ValueError as error:
        print(f"오류: {error}")
        return 2

    try:
        from .render import save
    except ImportError:  # pragma: no cover
        print("오류: matplotlib 가 필요하다 — pip install -r requirements.txt")
        return 1

    try:
        path = save(roses, args.out, theme=args.theme, korean=korean, dpi=args.dpi)
    except RuntimeError as error:
        print(f"오류: {error}")
        return 1

    print(f"저장: {path}")
    return 0
