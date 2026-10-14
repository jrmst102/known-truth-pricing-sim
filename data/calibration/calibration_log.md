# Calibration Log

Exploratory cleaning rules; protocol review pending.

- SHA-256 data/wsna.zip: 9a1d3f078efa12625ef9b4b3c9d4482aa643634a7740d83d0a8f56222a1d5be6
- SHA-256 data/upcsna.csv: 5ce04b56bfd5c9c71d7e3e0f799acc4fcd7253326ae3c8443bd307e0b9518f12
- SHA-256 data/wtna.zip: c4dcd8e9c4928b822307e37e1b756fdacc7b2a0a026033e35c1ebc3d5b0d5885
- SHA-256 data/upctna.csv: 316d269f56d48880f1a430865b18d1225bb9ff2846c593b3e7e0428117f2cc07
- SHA-256 data/wtti.zip: 6dd3b03925a2ee3e3e1831da127a0240ee0e00ecb0f118e2578d2f629d2c0b95
- SHA-256 data/upctti.csv: 944a03a81ee106f89f11f272bf05e78393a1cc294ea28918db53c0f7f1d31e43
- SHA-256 data/raw/stores.csv: 07fbd8ff19673e83f81aea4e29cae7167be3b262a9f50ae3ac73def4833b89ce
- SHA-256 data/fixtures/week_decode.csv: d7def12e3b0e629ef177e82457eff64ef60fc15c8f253018ea4729756e17ee73

## sna
1 OK == 1: 5427491 -> 5326861
2 valid price/qty/move: 5326861 -> 3487565
3 known UPC and zoned store: 3487565 -> 3009832
4 store coverage: 3009832 -> 2783337
5 UPC coverage: 2783337 -> 541079
6 focal UPC selection and zero-share substitution: 541079 -> 25013
7 remove zero sales before log regression: 25013 -> 25013
Focal UPC: 4400000028; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.3413; expected [0.05, 0.4]; PASS
promo_depth: 0.1665; expected [0.05, 0.4]; PASS
resid_sd: 0.4651; expected [0.2, 1.0]; PASS
profit_mean: 24.2935; expected [10, 45]; PASS
beta_reference: -3.1596; expected [-2.59, -0.79]; FAIL - author review required; no silent fallback

## Calibration invocation

- SHA-256 data/wsna.zip: 9a1d3f078efa12625ef9b4b3c9d4482aa643634a7740d83d0a8f56222a1d5be6
- SHA-256 data/upcsna.csv: 5ce04b56bfd5c9c71d7e3e0f799acc4fcd7253326ae3c8443bd307e0b9518f12
- SHA-256 data/wtna.zip: c4dcd8e9c4928b822307e37e1b756fdacc7b2a0a026033e35c1ebc3d5b0d5885
- SHA-256 data/upctna.csv: 316d269f56d48880f1a430865b18d1225bb9ff2846c593b3e7e0428117f2cc07
- SHA-256 data/wtti.zip: 6dd3b03925a2ee3e3e1831da127a0240ee0e00ecb0f118e2578d2f629d2c0b95
- SHA-256 data/upctti.csv: 944a03a81ee106f89f11f272bf05e78393a1cc294ea28918db53c0f7f1d31e43
- SHA-256 data/raw/stores.csv: 07fbd8ff19673e83f81aea4e29cae7167be3b262a9f50ae3ac73def4833b89ce
- SHA-256 data/fixtures/week_decode.csv: d7def12e3b0e629ef177e82457eff64ef60fc15c8f253018ea4729756e17ee73

## sna
1 OK == 1: 5427491 -> 5326861
2 valid price/qty/move: 5326861 -> 3487565
3 known UPC and zoned store: 3487565 -> 3009832
4 store coverage: 3009832 -> 2783337
5 UPC coverage: 2783337 -> 541079
6 focal UPC selection and zero-share substitution: 541079 -> 25013
7 remove zero sales before log regression: 25013 -> 25013
Focal UPC: 4400000028; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.3413; expected [0.05, 0.4]; PASS
promo_depth: 0.1665; expected [0.05, 0.4]; PASS
resid_sd: 0.4651; expected [0.2, 1.0]; PASS
profit_mean: 24.2935; expected [10, 45]; PASS
beta_reference: -3.1596; expected [-2.59, -0.79]; FAIL - author review required; no silent fallback

## tna
BLOCKED: No UPC satisfies coverage threshold 90%; best UPC coverage 83.6%, 75 stores, 399 weeks. No automatic threshold change.

## tti
1 OK == 1: 1627284 -> 1600398
2 valid price/qty/move: 1600398 -> 1149973
3 known UPC and zoned store: 1149973 -> 993280
4 store coverage: 993280 -> 917126
5 UPC coverage: 917126 -> 199277
6 focal UPC selection and zero-share substitution: 199277 -> 24918
7 remove zero sales before log regression: 24918 -> 24918
Focal UPC: 5400041500; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.2389; expected [0.05, 0.4]; PASS
promo_depth: 0.1101; expected [0.05, 0.4]; PASS
resid_sd: 0.5044; expected [0.2, 1.0]; PASS
profit_mean: 10.2483; expected [10, 45]; PASS
beta_reference: -3.8482; expected [-2.59, -0.79]; FAIL - author review required; no silent fallback

## Calibration invocation

- SHA-256 data/wsna.zip: 9a1d3f078efa12625ef9b4b3c9d4482aa643634a7740d83d0a8f56222a1d5be6
- SHA-256 data/upcsna.csv: 5ce04b56bfd5c9c71d7e3e0f799acc4fcd7253326ae3c8443bd307e0b9518f12
- SHA-256 data/wtna.zip: c4dcd8e9c4928b822307e37e1b756fdacc7b2a0a026033e35c1ebc3d5b0d5885
- SHA-256 data/upctna.csv: 316d269f56d48880f1a430865b18d1225bb9ff2846c593b3e7e0428117f2cc07
- SHA-256 data/wtti.zip: 6dd3b03925a2ee3e3e1831da127a0240ee0e00ecb0f118e2578d2f629d2c0b95
- SHA-256 data/upctti.csv: 944a03a81ee106f89f11f272bf05e78393a1cc294ea28918db53c0f7f1d31e43
- SHA-256 data/raw/stores.csv: 07fbd8ff19673e83f81aea4e29cae7167be3b262a9f50ae3ac73def4833b89ce
- SHA-256 data/fixtures/week_decode.csv: d7def12e3b0e629ef177e82457eff64ef60fc15c8f253018ea4729756e17ee73

## sna
1 OK == 1: 5427491 -> 5326861
2 valid price/qty/move: 5326861 -> 3487565
3 known UPC and zoned store: 3487565 -> 3009832
4 store coverage: 3009832 -> 2783337
5 UPC coverage: 2783337 -> 541079
6 focal UPC selection and zero-share substitution: 541079 -> 25013
Coverage denominator: weeks 1–399; span 399; retained stores 67; focal rows 25013
7 remove zero sales before log regression: 25013 -> 25013
Focal UPC: 4400000028; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.3413; expected [0.05, 0.4]; PASS
promo_depth: 0.1301; expected [0.05, 0.4]; PASS
resid_sd: 0.4651; expected [0.2, 1.0]; PASS
profit_mean: 24.2935; expected [10, 45]; PASS
beta_reference: -2.9456; expected [-2.59, -0.79]; FLAG

## tna
BLOCKED: No UPC satisfies coverage threshold 90%; best UPC coverage 83.6%, 75 stores, 399 weeks. No automatic threshold change.

## tti
1 OK == 1: 1627284 -> 1600398
2 valid price/qty/move: 1600398 -> 1149973
3 known UPC and zoned store: 1149973 -> 993280
4 store coverage: 993280 -> 917126
5 UPC coverage: 917126 -> 199277
6 focal UPC selection and zero-share substitution: 199277 -> 24918
Coverage denominator: weeks 1–399; span 399; retained stores 67; focal rows 24918
7 remove zero sales before log regression: 24918 -> 24918
Focal UPC: 5400041500; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.2389; expected [0.05, 0.4]; PASS
promo_depth: 0.1103; expected [0.05, 0.4]; PASS
resid_sd: 0.5044; expected [0.2, 1.0]; PASS
profit_mean: 10.2483; expected [10, 45]; PASS
beta_reference: -3.8578; expected [-2.59, -0.79]; FLAG

## Calibration invocation

- SHA-256 data/wtna.zip: c4dcd8e9c4928b822307e37e1b756fdacc7b2a0a026033e35c1ebc3d5b0d5885
- SHA-256 data/upctna.csv: 316d269f56d48880f1a430865b18d1225bb9ff2846c593b3e7e0428117f2cc07
- SHA-256 data/raw/stores.csv: 07fbd8ff19673e83f81aea4e29cae7167be3b262a9f50ae3ac73def4833b89ce
- SHA-256 data/fixtures/week_decode.csv: d7def12e3b0e629ef177e82457eff64ef60fc15c8f253018ea4729756e17ee73
tna: documented calibration window 1–341

## tna
1 OK == 1: 3354113 -> 3276148
2 valid price/qty/move: 3276148 -> 2157434
3 known UPC and zoned store: 2157434 -> 1881535
4 store coverage: 1881535 -> 1728596
5 UPC coverage: 1728596 -> 61944
6 focal UPC selection and zero-share substitution: 61944 -> 20765
Coverage denominator: weeks 1–341; span 341; retained stores 67; focal rows 20765
7 remove zero sales before log regression: 20765 -> 20765
Focal UPC: 8660000033; substituted: True
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.2381; expected [0.05, 0.4]; PASS
promo_depth: 0.1767; expected [0.05, 0.4]; PASS
resid_sd: 0.7537; expected [0.2, 1.0]; PASS
profit_mean: 28.7746; expected [10, 45]; PASS
beta_reference: -4.4345; expected [-2.59, -0.79]; FLAG

## Calibration invocation

- SHA-256 data/wsna.zip: 9a1d3f078efa12625ef9b4b3c9d4482aa643634a7740d83d0a8f56222a1d5be6
- SHA-256 data/upcsna.csv: 5ce04b56bfd5c9c71d7e3e0f799acc4fcd7253326ae3c8443bd307e0b9518f12
- SHA-256 data/wtna.zip: c4dcd8e9c4928b822307e37e1b756fdacc7b2a0a026033e35c1ebc3d5b0d5885
- SHA-256 data/upctna.csv: 316d269f56d48880f1a430865b18d1225bb9ff2846c593b3e7e0428117f2cc07
- SHA-256 data/wtti.zip: 6dd3b03925a2ee3e3e1831da127a0240ee0e00ecb0f118e2578d2f629d2c0b95
- SHA-256 data/upctti.csv: 944a03a81ee106f89f11f272bf05e78393a1cc294ea28918db53c0f7f1d31e43
- SHA-256 data/raw/stores.csv: 07fbd8ff19673e83f81aea4e29cae7167be3b262a9f50ae3ac73def4833b89ce
- SHA-256 data/fixtures/week_decode.csv: d7def12e3b0e629ef177e82457eff64ef60fc15c8f253018ea4729756e17ee73

## sna
1 OK == 1: 5427491 -> 5326861
2 valid price/qty/move: 5326861 -> 3487565
3 known UPC and zoned store: 3487565 -> 3009832
4 store coverage: 3009832 -> 2783337
5 UPC coverage: 2783337 -> 541079
6 focal UPC selection and zero-share substitution: 541079 -> 25013
Coverage denominator: weeks 1–399; span 399; retained stores 67; focal rows 25013
7 remove zero sales before log regression: 25013 -> 25013
Focal UPC: 4400000028; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.3413; expected [0.05, 0.4]; PASS
promo_depth: 0.1301; expected [0.05, 0.4]; PASS
resid_sd: 0.4651; expected [0.2, 1.0]; PASS
profit_mean: 24.2935; expected [10, 45]; PASS
beta_reference: -2.9456; expected [-2.59, -0.79]; FLAG
tna: documented calibration window 1–341

## tna
1 OK == 1: 3354113 -> 3276148
2 valid price/qty/move: 3276148 -> 2157434
3 known UPC and zoned store: 2157434 -> 1881535
4 store coverage: 1881535 -> 1728596
5 UPC coverage: 1728596 -> 61944
6 focal UPC selection and zero-share substitution: 61944 -> 20765
Coverage denominator: weeks 1–341; span 341; retained stores 67; focal rows 20765
7 remove zero sales before log regression: 20765 -> 20765
Focal UPC: 8660000033; substituted: True
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.2381; expected [0.05, 0.4]; PASS
promo_depth: 0.1767; expected [0.05, 0.4]; PASS
resid_sd: 0.7537; expected [0.2, 1.0]; PASS
profit_mean: 28.7746; expected [10, 45]; PASS
beta_reference: -4.4345; expected [-2.59, -0.79]; FLAG

## tti
1 OK == 1: 1627284 -> 1600398
2 valid price/qty/move: 1600398 -> 1149973
3 known UPC and zoned store: 1149973 -> 993280
4 store coverage: 993280 -> 917126
5 UPC coverage: 917126 -> 199277
6 focal UPC selection and zero-share substitution: 199277 -> 24918
Coverage denominator: weeks 1–399; span 399; retained stores 67; focal rows 24918
7 remove zero sales before log regression: 24918 -> 24918
Focal UPC: 5400041500; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.2389; expected [0.05, 0.4]; PASS
promo_depth: 0.1103; expected [0.05, 0.4]; PASS
resid_sd: 0.5044; expected [0.2, 1.0]; PASS
profit_mean: 10.2483; expected [10, 45]; PASS
beta_reference: -3.8578; expected [-2.59, -0.79]; FLAG

## Calibration invocation

- SHA-256 data/wsna.zip: 9a1d3f078efa12625ef9b4b3c9d4482aa643634a7740d83d0a8f56222a1d5be6
- SHA-256 data/upcsna.csv: 5ce04b56bfd5c9c71d7e3e0f799acc4fcd7253326ae3c8443bd307e0b9518f12
- SHA-256 data/wtna.zip: c4dcd8e9c4928b822307e37e1b756fdacc7b2a0a026033e35c1ebc3d5b0d5885
- SHA-256 data/upctna.csv: 316d269f56d48880f1a430865b18d1225bb9ff2846c593b3e7e0428117f2cc07
- SHA-256 data/wtti.zip: 6dd3b03925a2ee3e3e1831da127a0240ee0e00ecb0f118e2578d2f629d2c0b95
- SHA-256 data/upctti.csv: 944a03a81ee106f89f11f272bf05e78393a1cc294ea28918db53c0f7f1d31e43
- SHA-256 data/raw/stores.csv: 07fbd8ff19673e83f81aea4e29cae7167be3b262a9f50ae3ac73def4833b89ce
- SHA-256 data/fixtures/week_decode.csv: d7def12e3b0e629ef177e82457eff64ef60fc15c8f253018ea4729756e17ee73

## sna
1 OK == 1: 5427491 -> 5326861
2 valid price/qty/move: 5326861 -> 3487565
3 known UPC and zoned store: 3487565 -> 3009832
4 store coverage: 3009832 -> 2783337
5 UPC coverage: 2783337 -> 541079
6 focal UPC selection and zero-share substitution: 541079 -> 25013
Coverage denominator: weeks 1–399; span 399; retained stores 67; focal rows 25013
7 remove zero sales before log regression: 25013 -> 25013
Focal UPC: 4400000028; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.3413; expected [0.05, 0.4]; PASS
promo_depth: 0.1301; expected [0.05, 0.4]; PASS
resid_sd: 0.4651; expected [0.2, 1.0]; PASS
profit_mean: 24.2935; expected [10, 45]; PASS
beta_reference: -2.9456; expected [-2.59, -0.79]; FLAG
tna: documented calibration window 1–341

## tna
1 OK == 1: 3354113 -> 3276148
2 valid price/qty/move: 3276148 -> 2157434
3 known UPC and zoned store: 2157434 -> 1881535
4 store coverage: 1881535 -> 1728596
5 UPC coverage: 1728596 -> 61944
6 focal UPC selection and zero-share substitution: 61944 -> 20765
Coverage denominator: weeks 1–341; span 341; retained stores 67; focal rows 20765
7 remove zero sales before log regression: 20765 -> 20765
Focal UPC: 8660000033; substituted: True
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.2381; expected [0.05, 0.4]; PASS
promo_depth: 0.1767; expected [0.05, 0.4]; PASS
resid_sd: 0.7537; expected [0.2, 1.0]; PASS
profit_mean: 28.7746; expected [10, 45]; PASS
beta_reference: -4.4345; expected [-2.59, -0.79]; FLAG

## tti
1 OK == 1: 1627284 -> 1600398
2 valid price/qty/move: 1600398 -> 1149973
3 known UPC and zoned store: 1149973 -> 993280
4 store coverage: 993280 -> 917126
5 UPC coverage: 917126 -> 199277
6 focal UPC selection and zero-share substitution: 199277 -> 24918
Coverage denominator: weeks 1–399; span 399; retained stores 67; focal rows 24918
7 remove zero sales before log regression: 24918 -> 24918
Focal UPC: 5400041500; substituted: False
retained_stores_min: 67.0000; expected 40; PASS
promo_freq: 0.2389; expected [0.05, 0.4]; PASS
promo_depth: 0.1103; expected [0.05, 0.4]; PASS
resid_sd: 0.5044; expected [0.2, 1.0]; PASS
profit_mean: 10.2483; expected [10, 45]; PASS
beta_reference: -3.8578; expected [-2.59, -0.79]; FLAG
