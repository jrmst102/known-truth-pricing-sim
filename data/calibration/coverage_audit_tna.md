# Coverage audit: tna

Calendar range: [1, 399]; span 399 weeks; equals 399: True.
Retained stores: 66. Duplicates: 0.

| UPC | Rows present | Expected | Coverage | Missing by cause |
| --- | --- | --- | --- | --- |
| 8000000245 | 21600 | 26334 | 0.820232 | {'store_absent': 1584, 'upc_absent': 2332, 'ok_zero': 509, 'price_qty_rule': 309} |
| 8660000033 | 21853 | 26334 | 0.829840 | {'store_absent': 1584, 'upc_absent': 2332, 'ok_zero': 510, 'price_qty_rule': 55} |
| 4800000024 | 17549 | 26334 | 0.666401 | {'store_absent': 1584, 'upc_absent': 6292, 'ok_zero': 184, 'price_qty_rule': 725} |
| 8000000280 | 21439 | 26334 | 0.814119 | {'store_absent': 1584, 'upc_absent': 2332, 'ok_zero': 509, 'price_qty_rule': 470} |
| 3828105003 | 11590 | 26334 | 0.440115 | {'store_absent': 1584, 'upc_absent': 7980, 'ok_zero': 185, 'price_qty_rule': 4995} |
| 8660000037 | 21473 | 26334 | 0.815410 | {'store_absent': 1584, 'upc_absent': 2332, 'ok_zero': 510, 'price_qty_rule': 435} |
| 3828105005 | 10379 | 26334 | 0.394129 | {'store_absent': 1584, 'upc_absent': 7319, 'ok_zero': 438, 'price_qty_rule': 6614} |
| 7114010110 | 21678 | 26334 | 0.823194 | {'store_absent': 1584, 'upc_absent': 2332, 'ok_zero': 510, 'price_qty_rule': 230} |
| 1780000024 | 4638 | 26334 | 0.176122 | {'store_absent': 1584, 'upc_absent': 13829, 'ok_zero': 431, 'price_qty_rule': 5852} |
| 7303010314 | 21278 | 26334 | 0.808005 | {'store_absent': 1584, 'upc_absent': 2332, 'ok_zero': 510, 'price_qty_rule': 630} |

Best coverage across every UPC: {'upc': 7242100111, 'volume': 146993.0, 'rows_present': 22009, 'expected_rows': 26334, 'coverage': 0.8357636515531253, 'missing_by_cause': {'store_absent': 1584, 'upc_absent': 0, 'ok_zero': 510, 'price_qty_rule': 2231}}

Store rules: [{'rule': 'raw', 'stores': 93, 'rows': 3763229}, {'rule': 'OK == 1', 'stores': 93, 'rows': 3685264}, {'rule': 'valid price/qty/move', 'stores': 93, 'rows': 2382983}, {'rule': 'known UPC and zoned store', 'stores': 75, 'rows': 2063181}, {'rule': 'store coverage', 'stores': 66, 'rows': 1877529}]

Date alignment: {'missing_weeks': [], 'first': [{'week': '1', 'date': '1989-09-14', 'end': '1989-09-20', 'special_event': 'nan', 'lent': 'False', 'holiday_easter': '0', 'holiday_lent': '0', 'holiday_halloween': '0', 'holiday_thanksgiving': '0', 'holiday_christmas': '0', 'holiday_new_year': '0', 'holiday_presidents_day': '0', 'holiday_memorial_day': '0', 'holiday_4th_of_july': '0', 'holiday_labor_day': '0'}], 'last': [{'week': '399', 'date': '1997-05-01', 'end': '1997-05-07', 'special_event': 'nan', 'lent': 'False', 'holiday_easter': '0', 'holiday_lent': '0', 'holiday_halloween': '0', 'holiday_thanksgiving': '0', 'holiday_christmas': '0', 'holiday_new_year': '0', 'holiday_presidents_day': '0', 'holiday_memorial_day': '0', 'holiday_4th_of_july': '0', 'holiday_labor_day': '0'}]}
