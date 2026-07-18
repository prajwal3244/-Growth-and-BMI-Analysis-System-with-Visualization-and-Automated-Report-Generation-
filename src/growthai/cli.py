"""Command-line interface.

Preserves the spirit of the original interactive script (``python
GrowthInsight.py``) but powered by the new engine. Supports a guided prompt flow
and a one-shot report mode. Registered as the ``growthai`` console script.
"""

from __future__ import annotations

import argparse
import json

from growthai import __version__
from growthai.core.domain import Gender, Measurement, Standard
from growthai.logging_conf import configure_logging
from growthai.services.growth_service import GrowthService
from growthai.services.report_service import ReportService


def _analyze(args: argparse.Namespace) -> None:
    m = Measurement(
        age_months=args.age_months,
        height_cm=args.height,
        weight_kg=args.weight,
        gender=Gender.parse(args.gender),
    )
    analysis = GrowthService(Standard(args.standard)).analyze(m)
    print(json.dumps(analysis.as_dict(), indent=2))


def _report(args: argparse.Namespace) -> None:
    m = Measurement(
        age_months=args.age_months,
        height_cm=args.height,
        weight_kg=args.weight,
        gender=Gender.parse(args.gender),
    )
    result = ReportService(Standard(args.standard)).generate(args.name, m)
    print(f"Report {result.report_id}")
    print(f"  HTML: {result.html_path}")
    print(f"  PDF : {result.pdf_path if result.pdf_generated else '(unavailable - install WeasyPrint/GTK)'}")


def _interactive(_: argparse.Namespace) -> None:
    """The classic guided flow, modernized."""
    print("GrowthAI - interactive analysis\n")
    gender = input("Gender M(male)/F(female): ")
    unit = input("Age unit (m=months / y=years) [y]: ") or "y"
    age = float(input("Age: "))
    age_months = age if unit.lower().startswith("m") else age * 12
    name = input("Name: ")
    weight = float(input("Weight (kg): "))
    height = float(input("Height (cm): "))
    m = Measurement(age_months=age_months, height_cm=height, weight_kg=weight, gender=Gender.parse(gender))
    analysis = GrowthService().analyze(m)
    a = analysis.assessment
    print(f"\n{name}: BMI {a.bmi} -> {a.category.value} (p{a.percentile:.0f}, z={a.z_score:+.2f})")
    for f in analysis.forecasts:
        print(f"  {f.horizon_label}: {f.height_cm:.0f} cm, {f.weight_kg:.0f} kg, BMI {f.bmi:.1f} ({f.confidence:.0f}%)")
    print(f"\n{analysis.explanation.summary}")


def main() -> None:
    configure_logging("WARNING")
    parser = argparse.ArgumentParser(prog="growthai", description="GrowthAI health-intelligence CLI")
    parser.add_argument("--version", action="version", version=f"GrowthAI {__version__}")
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--age-months", type=float, required=True)
    common.add_argument("--height", type=float, required=True, help="height in cm")
    common.add_argument("--weight", type=float, required=True, help="weight in kg")
    common.add_argument("--gender", required=True, choices=["M", "F", "male", "female"])
    common.add_argument("--standard", default="WHO", choices=[s.value for s in Standard])

    p_an = sub.add_parser("analyze", parents=[common], help="Print a JSON analysis")
    p_an.set_defaults(func=_analyze)

    p_rp = sub.add_parser("report", parents=[common], help="Generate an HTML/PDF report")
    p_rp.add_argument("--name", default="Anonymous")
    p_rp.set_defaults(func=_report)

    p_it = sub.add_parser("interactive", help="Classic guided prompts")
    p_it.set_defaults(func=_interactive)

    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
