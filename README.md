# Irish residential property prices: SQL, Python and Power BI

An end-to-end analytics project on the Property Price Register (PPR), the official record of every residential property sale in Ireland since 2010. The pipeline cleans the raw register in Python, loads it into a SQL star schema, reconciles and validates the load, answers market questions in SQL, and feeds a Power BI dashboard.

![Median price, new vs second-hand](figures/median_new_vs_secondhand.png)

## Questions answered

1. How have median prices moved nationally since 2010, and how big is the premium for new homes once VAT is included?
2. Which counties are most and least expensive, and where did prices rise or fall fastest in the latest full year?
3. How has transaction volume evolved month by month?
4. How are sales spread across price bands in each province?

## Pipeline

```
PPR-ALL.csv ──► clean.py ──► sales_clean.csv ──► load_and_analyse.py ──► SQLite star schema
  (raw)         cleaning log                      reconciliation          ├─ data-quality checks (SQL)
                                                  load                    ├─ analyses (SQL)  ──► outputs/*.csv, figures/
                                                                          └─ Power BI exports ──► dashboard
```

| Step | File | What it does |
| --- | --- | --- |
| Clean | `src/clean.py` | Decodes the non-UTF-8 file, standardises headers, parses dates and prices (euro signs, commas), translates Irish-language descriptions, adds 13.5% VAT to VAT-exclusive new homes, flags non-market sales and implausible prices, drops street addresses for privacy, and logs every rule with its row count |
| Model | `sql/schema.sql` | Star schema: `fact_sale`, `dim_county` (with province), `dim_date`, and the analysis view `v_market_sales` |
| Validate | `src/load_and_analyse.py`, `sql/checks/` | Reconciles row counts and price totals between the clean file and the database, then runs referential-integrity and business-rule checks |
| Analyse | `sql/analysis/` | Five SQL analyses (below) |
| Report | `powerbi/DASHBOARD_SPEC.md` | Data model, DAX measures and page layout for the Power BI dashboard, including a data-quality page |

## SQL techniques

| Query | Techniques |
| --- | --- |
| `01_county_year_median.sql` | Median without a MEDIAN function: `ROW_NUMBER()` and `COUNT()` window functions, picking the middle row(s) |
| `02_county_yoy_change.sql` | CTEs, `LAG()` over a named `WINDOW`, `RANK()` per year |
| `03_new_vs_secondhand.sql` | Conditional aggregation (pivot with `CASE`), premium calculation |
| `04_monthly_volume_rolling.sql` | Rolling 3- and 12-month averages with `ROWS BETWEEN` frames |
| `05_price_bands_by_province.sql` | `CASE` banding, share of total with `SUM() OVER (PARTITION BY ...)` |
| `checks/data_quality_checks.sql` | Orphan-key checks with `LEFT JOIN ... IS NULL`, business-rule tests, duplicate detection |

## Data quality approach

Rows that cannot be parsed and exact duplicates are removed. Non-market sales and prices outside EUR 10,000 to 5,000,000 (typically bulk or portfolio sales) are **flagged, not deleted**, so the raw-to-database reconciliation stays exact and the analysis filter is explicit. Every rule and its row count is written to `outputs/data_quality_report.csv`, and the pipeline stops if reconciliation or any hard check fails.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Real data.** Download the full register (all years, CSV) from [propertypriceregister.ie](https://www.propertypriceregister.ie), unzip it, and save it as `data/raw/PPR-ALL.csv`. Then:

```bash
python run_pipeline.py
```

**Quick test without the download.** A synthetic sample in the same format (invented values, same data-quality problems) is generated and processed:

```bash
python run_pipeline.py --sample
```

Outputs: `data/ppr.db` (SQLite), `outputs/*.csv`, `outputs/powerbi/*.csv`, `figures/*.png`.

## Key findings

<!-- Fill in after running on the real register: 3 or 4 bullets with numbers,
     e.g. national median in 2025, change since 2013, new-home premium,
     fastest-rising county. Replace the figures in figures/ with the real-data versions. -->

![County year-on-year change](figures/county_yoy_latest.png)

![Monthly volume](figures/monthly_volume.png)

## Limitations

- The register records price and county but not floor area, bedrooms or condition, so medians mix very different properties. Changes in the mix of what sells can move a median without any change in like-for-like prices; the CSO Residential Property Price Index adjusts for this.
- Non-market sales are flagged by the register itself, and the price thresholds are a judgement call; both are documented and easy to change in `src/clean.py`.
- New homes are compared VAT-inclusive at 13.5% throughout.

## Tools

Python (pandas, NumPy, Matplotlib), SQL (SQLite 3.25+ for window functions; the queries port to MySQL 8 with minor changes), Power BI (DAX).

## Data source

Property Services Regulatory Authority, Residential Property Price Register. Street addresses are removed during cleaning and are not stored in the database or outputs.
