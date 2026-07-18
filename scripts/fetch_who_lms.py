"""Download official WHO LMS reference tables and convert to GrowthAI's format.

GrowthAI never bundles or invents reference constants. Run this script to fetch
the **official** WHO Child Growth Standards LMS tables and write them, in the
simple ``age_months,L,M,S`` CSV format the engine expects, into
``datasets/who/lms/``. Once present, :mod:`growthai.data.lms` activates
automatically and z-scores/percentiles use the exact LMS method.

Usage::

    python scripts/fetch_who_lms.py

The WHO publishes these tables (public domain, "expandable tables") at
https://www.who.int/tools/child-growth-standards/standards and
https://www.who.int/tools/growth-reference-data-for-5to19-years . The exact
download URLs change over time, so they are kept in ``SOURCES`` below - update
them if WHO reorganizes the site. Network access is required.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# gender, metric -> (url, column mapping). Fill/adjust URLs from the WHO pages above.
# Each source must resolve to a table with age (months) and L, M, S columns.
SOURCES: dict[tuple[str, str], str] = {
    # ("male", "bmi"): "https://cdn.who.int/media/docs/.../bmi-boys-z-...xlsx",
    # ("female", "bmi"): "https://cdn.who.int/media/docs/.../bmi-girls-z-...xlsx",
    # ("male", "height"): "...",
    # ("female", "height"): "...",
    # ("male", "weight"): "...",
    # ("female", "weight"): "...",
}

_METRIC_STEM = {"bmi": "bmi_for_age", "height": "height_for_age", "weight": "weight_for_age"}


def _out_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    d = root / "datasets" / "who" / "lms"
    d.mkdir(parents=True, exist_ok=True)
    return d


def main() -> int:
    if not SOURCES:
        print(
            "No SOURCES configured.\n"
            "Open scripts/fetch_who_lms.py and paste the official WHO LMS table URLs\n"
            "into the SOURCES dict (see datasets/who/lms/README.md for the format),\n"
            "then re-run. GrowthAI works without them via a documented approximation."
        )
        return 1

    try:
        import pandas as pd
        import requests
    except ImportError:
        print("This script needs 'requests' and 'pandas': pip install requests pandas")
        return 1

    out = _out_dir()
    for (gender, metric), url in SOURCES.items():
        print(f"Fetching {gender}/{metric} ...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        if url.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(resp.content))
        else:
            df = pd.read_csv(io.BytesIO(resp.content))

        # Normalize columns: WHO uses 'Month'/'Age' and 'L','M','S'.
        cols = {c.lower().strip(): c for c in df.columns}
        age_col = cols.get("month") or cols.get("age") or df.columns[0]
        norm = pd.DataFrame(
            {
                "age_months": pd.to_numeric(df[age_col], errors="coerce"),
                "L": pd.to_numeric(df[cols["l"]], errors="coerce"),
                "M": pd.to_numeric(df[cols["m"]], errors="coerce"),
                "S": pd.to_numeric(df[cols["s"]], errors="coerce"),
            }
        ).dropna()
        dest = out / f"{gender}_{_METRIC_STEM[metric]}.csv"
        norm.to_csv(dest, index=False)
        print(f"  wrote {dest} ({len(norm)} rows)")

    print("Done. Restart the app - LMS z-scores are now active.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
