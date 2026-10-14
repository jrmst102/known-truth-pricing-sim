# Coverage audit: tti

Metadata scope: retained-store table; source: data/calibration/stores_sna.csv.

Calendar span: 399; week range: [1, 399]; retained stores: 67; duplicate rows: 0.

Best coverage: 93.513635%; threshold: 90%.

## Store retention

| rule | stores_before | stores_after | rows_after |
| --- | --- | --- | --- |
| OK == 1 | 93 | 93 | 1600398 |
| valid price/qty/move | 93 | 93 | 1149973 |
| known UPC and zoned store | 93 | 67 | 917126 |
| store coverage | 67 | 67 | 917126 |

## Top ten UPCs and missing-record causes

| upc | volume | rows_present | expected_rows | coverage | missing_store_absent | missing_upc_absent | dropped_ok | dropped_price_qty_move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5400041500 | 11405017.0 | 24918 | 26733 | 0.9321063853664011 | 938 | 0 | 570 | 307 |
| 3700060511 | 4538834.0 | 24999 | 26733 | 0.9351363483335203 | 938 | 0 | 570 | 226 |
| 5400046550 | 3662681.0 | 22096 | 26733 | 0.8265439718699734 | 938 | 0 | 570 | 3129 |
| 5400046510 | 3466978.0 | 22375 | 26733 | 0.8369805109789399 | 938 | 0 | 570 | 2850 |
| 5400046520 | 3281450.0 | 22465 | 26733 | 0.8403471364979613 | 938 | 0 | 570 | 2760 |
| 4200013100 | 3029693.0 | 24972 | 26733 | 0.934126360677814 | 938 | 0 | 570 | 253 |
| 3700060571 | 2804832.0 | 22759 | 26733 | 0.851344779860098 | 938 | 0 | 570 | 2466 |
| 5400046530 | 2762924.0 | 22556 | 26733 | 0.8437511689671942 | 938 | 0 | 570 | 2669 |
| 3828111217 | 2683457.0 | 24827 | 26733 | 0.9287023528971683 | 938 | 0 | 570 | 398 |
| 4200013700 | 2678337.0 | 24891 | 26733 | 0.9310963977106946 | 938 | 0 | 570 | 334 |

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
null
```

A proposal does not change the sample or authorize a scientific run.
