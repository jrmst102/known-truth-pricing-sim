# Coverage audit: tti

Calendar range: [1, 399]; span 399 weeks; equals 399: True.
Retained stores: 67. Duplicates: 0.

| UPC | Rows present | Expected | Coverage | Missing by cause |
| --- | --- | --- | --- | --- |
| 5400041500 | 24918 | 26733 | 0.932106 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 307} |
| 3700060511 | 24999 | 26733 | 0.935136 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 226} |
| 5400046550 | 22096 | 26733 | 0.826544 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 3129} |
| 5400046510 | 22375 | 26733 | 0.836981 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 2850} |
| 5400046520 | 22465 | 26733 | 0.840347 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 2760} |
| 4200013100 | 24972 | 26733 | 0.934126 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 253} |
| 3700060571 | 22759 | 26733 | 0.851345 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 2466} |
| 5400046530 | 22556 | 26733 | 0.843751 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 2669} |
| 3828111217 | 24827 | 26733 | 0.928702 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 398} |
| 4200013700 | 24891 | 26733 | 0.931096 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 334} |

Best coverage across every UPC: {'upc': 3700060511, 'volume': 4538834.0, 'rows_present': 24999, 'expected_rows': 26733, 'coverage': 0.9351363483335203, 'missing_by_cause': {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 226}}

Store rules: [{'rule': 'raw', 'stores': 93, 'rows': 1627284}, {'rule': 'OK == 1', 'stores': 93, 'rows': 1600398}, {'rule': 'valid price/qty/move', 'stores': 93, 'rows': 1149973}, {'rule': 'known UPC and zoned store', 'stores': 75, 'rows': 993280}, {'rule': 'store coverage', 'stores': 67, 'rows': 917126}]

Date alignment: {'missing_weeks': [], 'first': [{'week': '1', 'date': '1989-09-14', 'end': '1989-09-20', 'special_event': 'nan', 'lent': 'False', 'holiday_easter': '0', 'holiday_lent': '0', 'holiday_halloween': '0', 'holiday_thanksgiving': '0', 'holiday_christmas': '0', 'holiday_new_year': '0', 'holiday_presidents_day': '0', 'holiday_memorial_day': '0', 'holiday_4th_of_july': '0', 'holiday_labor_day': '0'}], 'last': [{'week': '399', 'date': '1997-05-01', 'end': '1997-05-07', 'special_event': 'nan', 'lent': 'False', 'holiday_easter': '0', 'holiday_lent': '0', 'holiday_halloween': '0', 'holiday_thanksgiving': '0', 'holiday_christmas': '0', 'holiday_new_year': '0', 'holiday_presidents_day': '0', 'holiday_memorial_day': '0', 'holiday_4th_of_july': '0', 'holiday_labor_day': '0'}]}
