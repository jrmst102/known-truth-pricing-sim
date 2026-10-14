# Coverage audit: tna

Metadata scope: retained-store table; source: data/calibration/stores_sna.csv.

Calendar span: 399; week range: [1, 399]; retained stores: 66; duplicate rows: 0.

Best coverage: 83.576365%; threshold: 90%.

## Store retention

| rule | stores_before | stores_after | rows_after |
| --- | --- | --- | --- |
| OK == 1 | 93 | 93 | 3685264 |
| valid price/qty/move | 93 | 93 | 2382983 |
| known UPC and zoned store | 93 | 67 | 1904986 |
| store coverage | 67 | 66 | 1877529 |

## Top ten UPCs and missing-record causes

| upc | volume | rows_present | expected_rows | coverage | missing_store_absent | missing_upc_absent | dropped_ok | dropped_price_qty_move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8000000245 | 4256504.0 | 21600 | 26334 | 0.8202323991797676 | 1584 | 2332 | 509 | 309 |
| 8660000033 | 2926066.0 | 21853 | 26334 | 0.8298397508923825 | 1584 | 2332 | 510 | 55 |
| 4800000024 | 2733247.0 | 17549 | 26334 | 0.6664008506113769 | 1584 | 6292 | 184 | 725 |
| 8000000280 | 1311557.0 | 21439 | 26334 | 0.8141186299081036 | 1584 | 2332 | 509 | 470 |
| 3828105003 | 1005125.0 | 11590 | 26334 | 0.4401154401154401 | 1584 | 7980 | 185 | 4995 |
| 8660000037 | 888676.0 | 21473 | 26334 | 0.815409736462368 | 1584 | 2332 | 510 | 435 |
| 3828105005 | 810281.0 | 10379 | 26334 | 0.39412926255031516 | 1584 | 7319 | 438 | 6614 |
| 7114010110 | 749779.0 | 21678 | 26334 | 0.823194349510139 | 1584 | 2332 | 510 | 230 |
| 1780000024 | 671308.0 | 4638 | 26334 | 0.17612212349054454 | 1584 | 13829 | 431 | 5852 |
| 7303010314 | 662784.0 | 21278 | 26334 | 0.8080048606364396 | 1584 | 2332 | 510 | 630 |

## Date alignment

```json
{
  "week_min": 1,
  "week_max": 399,
  "all_weeks_in_calendar": true,
  "start_date": "1989-09-14 00:00:00",
  "end_date": "1997-05-01 00:00:00",
  "date_basis": "week joined to authoritative codebook calendar; movement supplies week IDs, not independent dates"
}
```

## Window proposal

```json
{
  "week_range": [
    1,
    341
  ],
  "weeks": 341,
  "n_stores": 66,
  "upc": 8660000033,
  "coverage": 0.9104683195592287,
  "status": "candidate; author sample review pending",
  "competing_index_validated": true,
  "clean_validation": {
    "focal_upc": 8660000033,
    "n_stores": 66,
    "n_rows": 20491
  }
}
```

A proposal does not change the sample or authorize a scientific run.
