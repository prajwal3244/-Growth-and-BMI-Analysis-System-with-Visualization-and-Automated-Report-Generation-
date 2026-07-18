# WHO LMS reference tables

Drop official **WHO LMS** tables here to unlock exact z-scores/percentiles.

## Why

GrowthAI's default engine derives percentiles from median reference curves using
a documented log-normal approximation. The clinically exact method uses WHO's
**L, M, S** parameters (Box-Cox skewness, median, coefficient of variation) at
each age. When the files below are present, `growthai.data.lms` activates
automatically and every z-score/percentile uses the LMS method - no code change.

## Expected files

One CSV per gender + metric, named exactly:

```
male_bmi_for_age.csv      female_bmi_for_age.csv
male_height_for_age.csv   female_height_for_age.csv
male_weight_for_age.csv   female_weight_for_age.csv
```

## Expected format

```csv
age_months,L,M,S
60,-0.7,15.28,0.0812
61,-0.71,15.27,0.0815
...
```

`age_months` is age in months; `L`, `M`, `S` are the WHO parameters for that age.

## How to get them

Run `python scripts/fetch_who_lms.py` after pasting the official WHO download
URLs into that script's `SOURCES` dict. Sources (public domain):

- 0-5 years: <https://www.who.int/tools/child-growth-standards/standards>
- 5-19 years: <https://www.who.int/tools/growth-reference-data-for-5to19-years>

> GrowthAI intentionally ships **no** bundled reference constants - only the
> engine and loader. This keeps the medical data authoritative and traceable to WHO.
