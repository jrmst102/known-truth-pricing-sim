# Coverage audit: sna

Metadata scope: retained-store table; source: data/calibration/stores_sna.csv.

Calendar span: 399; week range: [1, 399]; retained stores: 67; duplicate rows: 0.

Best coverage: 93.566005%; threshold: 90%.

## Store retention

| rule | stores_before | stores_after | rows_after |
| --- | --- | --- | --- |
| OK == 1 | 93 | 93 | 5326861 |
| valid price/qty/move | 93 | 93 | 3487565 |
| known UPC and zoned store | 93 | 67 | 2783337 |
| store coverage | 67 | 67 | 2783337 |

## Top ten UPCs and missing-record causes

| upc | volume | rows_present | expected_rows | coverage | missing_store_absent | missing_upc_absent | dropped_ok | dropped_price_qty_move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4400000028 | 1148296.0 | 25013 | 26733 | 0.9356600456364793 | 938 | 0 | 570 | 212 |
| 4400000119 | 763520.0 | 24820 | 26733 | 0.9284405042456888 | 938 | 0 | 570 | 405 |
| 4400004754 | 715191.0 | 14133 | 26733 | 0.5286724273369993 | 938 | 10143 | 74 | 1445 |
| 3010067264 | 699798.0 | 24958 | 26733 | 0.9336026633748551 | 938 | 0 | 570 | 267 |
| 4400000104 | 690623.0 | 24941 | 26733 | 0.9329667452212621 | 938 | 0 | 570 | 284 |
| 1470001283 | 681005.0 | 24923 | 26733 | 0.9322934201174579 | 938 | 0 | 571 | 301 |
| 4400000105 | 596376.0 | 24667 | 26733 | 0.9227172408633524 | 938 | 0 | 570 | 558 |
| 1410007450 | 514861.0 | 24913 | 26733 | 0.9319193506153444 | 938 | 0 | 571 | 311 |
| 4400000071 | 472792.0 | 24784 | 26733 | 0.9270938540380803 | 938 | 0 | 570 | 441 |
| 4400000120 | 471958.0 | 24548 | 26733 | 0.9182658137882018 | 938 | 0 | 570 | 677 |

## Date alignment

```json
{
  "week_min": 1,
  "week_max": 399,
  "all_weeks_in_calendar": false,
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
