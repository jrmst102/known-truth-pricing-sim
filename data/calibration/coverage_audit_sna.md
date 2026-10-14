# Coverage audit: sna

Calendar range: [1, 399]; span 399 weeks; equals 399: True.
Retained stores: 67. Duplicates: 0.

| UPC | Rows present | Expected | Coverage | Missing by cause |
| --- | --- | --- | --- | --- |
| 4400000028 | 25013 | 26733 | 0.935660 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 212} |
| 4400000119 | 24820 | 26733 | 0.928441 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 405} |
| 4400004754 | 14133 | 26733 | 0.528672 | {'store_absent': 938, 'upc_absent': 10143, 'ok_zero': 74, 'price_qty_rule': 1445} |
| 3010067264 | 24958 | 26733 | 0.933603 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 267} |
| 4400000104 | 24941 | 26733 | 0.932967 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 284} |
| 1470001283 | 24923 | 26733 | 0.932293 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 571, 'price_qty_rule': 301} |
| 4400000105 | 24667 | 26733 | 0.922717 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 558} |
| 1410007450 | 24913 | 26733 | 0.931919 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 571, 'price_qty_rule': 311} |
| 4400000071 | 24784 | 26733 | 0.927094 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 441} |
| 4400000120 | 24548 | 26733 | 0.918266 | {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 677} |

Best coverage across every UPC: {'upc': 4400000028, 'volume': 1148296.0, 'rows_present': 25013, 'expected_rows': 26733, 'coverage': 0.9356600456364793, 'missing_by_cause': {'store_absent': 938, 'upc_absent': 0, 'ok_zero': 570, 'price_qty_rule': 212}}

Store rules: [{'rule': 'raw', 'stores': 93, 'rows': 5427491}, {'rule': 'OK == 1', 'stores': 93, 'rows': 5326861}, {'rule': 'valid price/qty/move', 'stores': 93, 'rows': 3487565}, {'rule': 'known UPC and zoned store', 'stores': 75, 'rows': 3009832}, {'rule': 'store coverage', 'stores': 67, 'rows': 2783337}]

Date alignment: {'missing_weeks': [], 'first': [{'week': '1', 'date': '1989-09-14', 'end': '1989-09-20', 'special_event': 'nan', 'lent': 'False', 'holiday_easter': '0', 'holiday_lent': '0', 'holiday_halloween': '0', 'holiday_thanksgiving': '0', 'holiday_christmas': '0', 'holiday_new_year': '0', 'holiday_presidents_day': '0', 'holiday_memorial_day': '0', 'holiday_4th_of_july': '0', 'holiday_labor_day': '0'}], 'last': [{'week': '399', 'date': '1997-05-01', 'end': '1997-05-07', 'special_event': 'nan', 'lent': 'False', 'holiday_easter': '0', 'holiday_lent': '0', 'holiday_halloween': '0', 'holiday_thanksgiving': '0', 'holiday_christmas': '0', 'holiday_new_year': '0', 'holiday_presidents_day': '0', 'holiday_memorial_day': '0', 'holiday_4th_of_july': '0', 'holiday_labor_day': '0'}]}
